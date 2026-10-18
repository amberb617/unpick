"""The one shape every result takes, whether it came from a built-in check, a scanner, a judge or rehearse.

A finding is a question for a person, not a verdict. Each one carries enough context to answer it:
the matched line with three lines either side, why the rule fires, and when it is a false positive.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field

SEVERITIES = ("info", "low", "medium", "high")
CONTEXT_LINES = 3


def line_hash(text: str) -> str:
    """Content hash of a matched line. Decisions key on this, so editing the line makes it fire again."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


@dataclass
class Finding:
    rule_id: str
    source: str  # builtin | backend:<name> | judge:<model> | rehearse
    severity: str
    path: str
    line: int  # 1-based; 0 when the finding is about the whole file
    message: str
    why: str
    false_positive: str
    matched: str = ""
    context: list[dict] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    original_rule_id: str | None = None  # the backend's own id, kept verbatim
    original_message: str | None = None
    agreed_by: list[str] = field(default_factory=list)
    decision: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"bad severity {self.severity!r}")

    @property
    def line_hash(self) -> str:
        return line_hash(self.matched)

    @property
    def id(self) -> str:
        key = f"{self.source}|{self.rule_id}|{self.path}|{self.line}|{self.line_hash}"
        return hashlib.sha256(key.encode()).hexdigest()[:10]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["id"] = self.id
        d["line_hash"] = self.line_hash
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Finding:
        keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in d.items() if k in keys})


def with_context(lines: list[str], line: int) -> tuple[str, list[dict]]:
    """Return the matched line and up to CONTEXT_LINES of context on each side (1-based `line`)."""
    if not 1 <= line <= len(lines):
        return "", []
    lo, hi = max(1, line - CONTEXT_LINES), min(len(lines), line + CONTEXT_LINES)
    ctx = [{"line": n, "text": lines[n - 1]} for n in range(lo, hi + 1)]
    return lines[line - 1], ctx
