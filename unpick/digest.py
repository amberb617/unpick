"""One scan, folded into something a person can read in a minute: a header, a TL;DR, collapsed groups,
coverage and next steps. No terminal code here, so the CLI, the home screen and the web UI can share it.

Design reviewed with Codex and Grok over two rounds (DECISIONS.md, "Scan output"). Every sentence is built
from the scan's own records; nothing here says safe, benign or harmless. Severity and exit codes are untouched.
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from unpick.explain import UNKNOWN_EXPLANATION, get_explanation

ORDER = ("high", "medium", "low", "info")
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".bash", ".zsh", ".ps1", ".rb", ".go",
            ".rs", ".java", ".kt", ".swift", ".c", ".h", ".cpp", ".php", ".lua", ".pl"}
DOC_EXT = {".md", ".mdc", ".markdown", ".txt", ".rst", ".yaml", ".yml", ".json", ".jsonc", ".toml", ".ini",
           ".cfg", ".conf", ".xml", ".html", ".htm"}
PLACES = ("code", "docs/config", "other")
MAX_FILES = 4  # file lines shown per group before "and N more"


def place(path: str) -> str:
    """File type, not trust: a Markdown skill can instruct execution as surely as a script."""
    ext = os.path.splitext(path)[1].lower()
    if ext in CODE_EXT:
        return "code"
    if ext in DOC_EXT or os.path.basename(path).lower() in ("dockerfile", "makefile"):
        return "docs/config"
    return "other"


def severity_mix(findings: list[dict]) -> str:
    c = Counter(f["severity"] for f in findings)
    return ", ".join(f"{c[s]} {s}" for s in ORDER if c[s])


def _explanation(rule_id: str):
    try:
        return get_explanation(rule_id)
    except KeyError:
        return UNKNOWN_EXPLANATION


@dataclass
class Group:
    rule_id: str
    place: str
    findings: list[dict]
    title: str = ""
    what_it_means: str = ""
    what_to_do: str = ""
    hint: str = ""
    files: dict[str, list[int]] = field(default_factory=dict)

    @property
    def worst(self) -> str:
        return min((f["severity"] for f in self.findings), key=ORDER.index)

    @property
    def mix(self) -> str:
        return severity_mix(self.findings)

    @property
    def example(self) -> dict:
        """The most serious finding, then the first in path order: one line a reader can judge the group by."""
        return min(self.findings, key=lambda f: (ORDER.index(f["severity"]), _describes(f, self.place),
                                                  len(os.path.basename(f["path"])), f["path"], f.get("line") or 0))


COMMENT = re.compile(r"^\s*(#|//|/\*|\*|<!--|--|\"\"\"|\'\'\')")


def _is_comment(line: str) -> bool:
    """A comment describes; prefer an example line that does something (a line that opens a key file over the
    comment above it that says so)."""
    return bool(COMMENT.match(line))


def _describes(f: dict, where: str) -> bool:
    """In code, a comment or a line of prose describes; a line with a call or an assignment acts."""
    line = f.get("matched") or ""
    return _is_comment(line) or (where == "code" and not re.search(r"[(=\[]", line))


def _hint(g: Group) -> str:
    """Location hints: a fact about where every finding in the group sits. Never a verdict."""
    names = {os.path.basename(f["path"]).lower() for f in g.findings}
    reasons = [(f.get("extra") or {}).get("reasons") or [] for f in g.findings]  # the detector's own record
    if g.rule_id == "RT-RENDER-DIVERGE" and all(n.startswith("readme") for n in names) and \
            all(r == ["inside a collapsed <details> block"] for r in reasons):
        return "All are inside <details> blocks of the project's README files. Still open."
    return ""


def groups(findings: list[dict]) -> list[Group]:
    """One group per rule and file type; most serious first, then code before docs, then size."""
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for f in findings:
        by_key[(f["rule_id"], place(f["path"]))].append(f)
    out = []
    for (rule_id, where), items in by_key.items():
        e = _explanation(rule_id)
        g = Group(rule_id, where, sorted(items, key=lambda f: (f["path"], f.get("line") or 0)),
                  e.title, e.what_it_means, e.what_to_do)
        for f in g.findings:
            g.files.setdefault(f["path"], []).append(f.get("line") or 0)
        g.hint = _hint(g)
        out.append(g)
    return sorted(out, key=lambda g: (ORDER.index(g.worst), PLACES.index(g.place), -len(g.findings), g.rule_id))


def headline(d: dict) -> str:
    """What to do, in one line: render.scan_verdict, the one place that decides when a scan may not look clean."""
    from unpick.render import scan_verdict

    return scan_verdict(d)


def coverage(d: dict) -> dict:
    runs = d.get("runs", [])
    others = [r["source"] for r in runs if r.get("source") and r.get("status") not in ("unavailable", "skipped")]
    network = [f"{r['source']}: {r.get('network_detail')}" for r in d.get("summary", {}).get("network_calls", [])]
    reasons: dict[str, list[str]] = defaultdict(list)
    for s in d.get("skipped", []):
        reasons[s["reason"]].append(s["path"])
    return {"files_read": len(d.get("files", [])), "not_read": sum(len(v) for v in reasons.values()),
            "not_read_by_reason": dict(sorted(reasons.items(), key=lambda kv: -len(kv[1]))),
            "sources": ["built-in"] + others, "network": network, "errors": d.get("errors", []),
            "unavailable": d.get("unavailable", [])}


def tldr(gs: list[Group], limit: int = 5) -> list[str]:
    lines = []
    for g in gs[:limit]:
        n = len(g.files)
        lines.append(f"{g.mix}: {g.title.rstrip('.')} ({g.rule_id}), {n} {g.place} file{'s' * (n != 1)}.")
    if len(gs) > limit:
        rest = sum(len(g.findings) for g in gs[limit:])
        lines.append(f"{len(gs) - limit} more group{'s' * (len(gs) - limit != 1)}, {rest} findings.")
    return lines


def build(d: dict) -> dict:
    gs = groups(d.get("findings", []))
    return {"headline": headline(d), "counts": severity_mix(d.get("findings", [])) or "none",
            "open": len(d.get("findings", [])), "accepted": len(d.get("accepted", [])),
            "groups": gs, "tldr": tldr(gs), "coverage": coverage(d)}
