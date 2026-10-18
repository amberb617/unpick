"""Remember what a person decided about a finding: accept, reject or ask-author.

Accepted findings are suppressed by rule id plus the content hash of the matched line, so if the line
changes the finding fires again. Project decisions live in ./.runthrough/decisions.json, user-wide
ones in ~/.runthrough/decisions.json.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

CHOICES = ("accept", "reject", "ask-author")


def project_file(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / ".runthrough" / "decisions.json"


def user_file() -> Path:
    return Path.home() / ".runthrough" / "decisions.json"


def load(paths: list[Path]) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for p in paths:
        if p.is_file():
            for d in json.loads(p.read_text(encoding="utf-8")).get("decisions", []):
                out[(d["rule_id"], d["line_hash"])] = d
    return out


def record(path: Path, finding: dict, choice: str, note: str = "") -> dict:
    if choice not in CHOICES:
        raise ValueError(f"decision must be one of {CHOICES}")
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"version": 1, "decisions": []}
    entry = {
        "rule_id": finding["rule_id"], "line_hash": finding["line_hash"], "decision": choice,
        "note": note, "path": finding["path"], "line": finding["line"], "source": finding["source"],
        "matched": finding["matched"][:200], "decided_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    data["decisions"] = [d for d in data["decisions"]
                         if (d["rule_id"], d["line_hash"]) != (entry["rule_id"], entry["line_hash"])] + [entry]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return entry


def apply(findings, decided: dict[tuple[str, str], dict]):
    """Attach decisions. Returns (open findings, accepted findings)."""
    open_, accepted = [], []
    for f in findings:
        d = decided.get((f.rule_id, f.line_hash))
        if d:
            f.decision = d["decision"]
        (accepted if f.decision == "accept" else open_).append(f)
    return open_, accepted
