"""Built-in checks: one file per attack, no backend, no network.

Each check module defines:
    RULE_ID, TITLE, WHY, FALSE_POSITIVE  -- the two explanation sentences travel with every finding
    SEVERITY                             -- default severity
    applies(doc) -> bool                 -- optional; default is every text file
    run(doc) -> iterable of Hit
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path

from unpick.finding import Finding, with_context

RULES_FILE_NAMES = {
    ".cursorrules", ".clinerules", ".windsurfrules", "agents.md", "claude.md", "gemini.md",
    "copilot-instructions.md",
}


@dataclass
class Doc:
    path: Path
    rel: str
    raw: bytes
    text: str
    lines: list[str]

    @property
    def name(self) -> str:
        return self.path.name.lower()

    @property
    def is_markdown(self) -> bool:
        return self.name.endswith((".md", ".mdc", ".markdown", ".mdx", ".md.tmpl", ".md.j2", ".md.jinja", ".md.hbs")) or self.is_rules

    @property
    def is_rules(self) -> bool:
        return (
            self.name in RULES_FILE_NAMES
            or self.name.endswith((".mdc", ".instructions.md", ".prompt.md"))
            or "/.cursor/rules/" in self.path.as_posix()
            or "/.windsurf/rules/" in self.path.as_posix()
        )

    @property
    def is_json(self) -> bool:
        return self.name.endswith((".json", ".jsonc"))

    @classmethod
    def load(cls, path: Path, root: Path) -> Doc:
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.as_posix()
        return cls(path, rel or path.name, raw, text, text.splitlines())


@dataclass
class Hit:
    line: int
    message: str
    severity: str | None = None
    extra: dict = field(default_factory=dict)


def all_checks():
    mods = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if info.name.startswith("_"):
            continue  # helpers, not checks
        mods.append(importlib.import_module(f"{__name__}.{info.name}"))
    return mods


def run_checks(doc: Doc, only: set[str] | None = None) -> list[Finding]:
    out = []
    for mod in all_checks():
        if only and mod.RULE_ID not in only:
            continue
        applies = getattr(mod, "applies", None)
        if applies and not applies(doc):
            continue
        for hit in mod.run(doc):
            matched, ctx = with_context(doc.lines, hit.line)
            out.append(Finding(
                rule_id=mod.RULE_ID, source="builtin", severity=hit.severity or mod.SEVERITY,
                path=doc.rel, line=hit.line, message=hit.message, why=mod.WHY,
                false_positive=mod.FALSE_POSITIVE, matched=matched, context=ctx, extra=hit.extra,
            ))
    return out
