"""One engine for the CLI and the UI: walk a target, run the built-in checks, the chosen scanners and the
chosen judge, apply decisions, and compute consensus.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from unpick import __version__, consensus, decisions
from unpick.checks import Doc, run_checks
from unpick.finding import Finding

SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__", ".unpick",
             ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", ".tox"}
TEXT_EXT = {".md", ".mdc", ".markdown", ".txt", ".json", ".jsonc", ".toml", ".yaml", ".yml", ".sh", ".bash",
            ".zsh", ".ps1", ".psm1", ".bat", ".cmd", ".py", ".js", ".mjs", ".cjs", ".ts", ".rb", ".swift", ".yar"}
TEXT_NAMES = {".cursorrules", ".clinerules", ".windsurfrules", "dockerfile", "makefile"}
MAX_BYTES = 2_000_000
IGNORE_FILE = ".unpickignore"


def _ignored(root: Path) -> list[str]:
    p = root / IGNORE_FILE
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        pat = line.split("#", 1)[0].strip()  # trailing comments say why a path is skipped
        if pat:
            out.append(pat)
    return out


def walk(target: Path) -> tuple[Path, list[Path]]:
    """Return (root, files). A file target is its own root's only file."""
    target = target.resolve()
    if target.is_file():
        return target.parent, [target]
    patterns = _ignored(target)
    files = []
    for p in sorted(target.rglob("*")):
        rel = p.relative_to(target).as_posix()
        if any(part in SKIP_DIRS for part in p.relative_to(target).parts[:-1]) or not p.is_file():
            continue
        if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.rstrip("/") + "/*") for pat in patterns):
            continue
        if p.name == "decisions.json" or p.name.endswith(".decisions.json"):
            continue  # unpick's own state, not a component
        if p.suffix.lower() not in TEXT_EXT and p.name.lower() not in TEXT_NAMES:
            continue
        if p.stat().st_size > MAX_BYTES:
            continue
        with p.open("rb") as fh:
            if b"\x00" in fh.read(8192):
                continue
        files.append(p)
    return target, files


@dataclass
class ScanResult:
    target: str
    started_at: str
    sources: list[str]
    files: list[str]
    findings: list[Finding] = field(default_factory=list)
    accepted: list[Finding] = field(default_factory=list)
    runs: list[dict] = field(default_factory=list)  # one entry per backend / judge: version, network, status
    errors: list[str] = field(default_factory=list)
    unavailable: list[str] = field(default_factory=list)

    @property
    def network_calls(self) -> list[dict]:
        return [r for r in self.runs if r.get("network")]

    def to_dict(self) -> dict:
        everything = self.findings + self.accepted
        return {
            "tool": "unpick", "version": __version__, "target": self.target, "started_at": self.started_at,
            "sources": self.sources, "files": self.files, "runs": self.runs, "errors": self.errors,
            "unavailable": self.unavailable,
            "summary": {
                "open": len(self.findings), "accepted": len(self.accepted),
                "by_source": consensus.totals(everything, self.sources),
                "agreement": consensus.matrix(everything, self.sources),
                "network_calls": self.network_calls,
            },
            "findings": [f.to_dict() for f in self.findings],
            "accepted": [f.to_dict() for f in self.accepted],
        }

    @property
    def exit_code(self) -> int:
        if not self.files:
            return 2  # nothing was read, so "no findings" would be absence posing as health
        if self.unavailable:
            return 3
        if self.errors and not self.findings:
            return 2
        return 1 if self.findings else 0


def scan(target: Path, backends: list[str] | None = None, judge: str | None = None, boxed: bool = False,
         online: bool = False, decision_files: list[Path] | None = None, only_rules: set[str] | None = None,
         consent=None) -> ScanResult:
    from unpick import backends as be
    from unpick import judges as ju

    root, files = walk(target)
    res = ScanResult(target=str(target), started_at=datetime.now(UTC).isoformat(timespec="seconds"),
                     sources=["builtin"], files=[])
    if not files:
        res.errors.append(f"no readable text files under {target}; nothing was scanned")
    docs = []
    for p in files:
        doc = Doc.load(p, root if target.is_dir() else p.parent)
        docs.append(doc)
        res.files.append(doc.rel)
        res.findings.extend(run_checks(doc, only_rules))

    for name in backends or []:
        out = be.run(name, target, boxed=boxed, online=online)
        res.runs.append(out.meta)
        if out.unavailable:
            res.unavailable.append(f"backend:{name}")
            continue
        if out.meta.get("status") == "ran":  # a scanner that did not apply is not a witness
            res.sources.append(f"backend:{name}")
        res.findings.extend(out.findings)
        res.errors.extend(out.errors)

    if judge:
        out = ju.run(judge, docs, consent=consent)
        res.runs.append(out.meta)
        if out.unavailable:
            res.unavailable.append(f"judge:{judge}")
        else:
            res.sources.append(out.meta["source"])
            res.findings.extend(out.findings)
            res.errors.extend(out.errors)

    for f in res.findings:  # backends report absolute or target-relative paths; give every finding the same shape
        f.path = _relpath(f.path, target)
    _fill_context(res.findings, docs)
    consensus.annotate(res.findings, res.sources)
    files_ = decision_files if decision_files is not None else [decisions.project_file(), decisions.user_file()]
    res.findings, res.accepted = decisions.apply(res.findings, decisions.load(files_))
    order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    res.findings.sort(key=lambda f: (f.path, f.line, order[f.severity], f.rule_id))
    return res


def _relpath(path: str, target: Path) -> str:
    p = Path(path)
    base = target.resolve() if target.is_dir() else target.resolve().parent
    if p.is_absolute():
        try:
            return p.resolve().relative_to(base).as_posix()
        except ValueError:
            return p.as_posix()
    return p.as_posix()


def _fill_context(findings, docs) -> None:
    from unpick.finding import with_context

    by_rel = {d.rel: d for d in docs}
    for f in findings:
        if not f.context and f.path in by_rel and f.line:
            f.matched, f.context = with_context(by_rel[f.path].lines, f.line)


def save_last(res: ScanResult, root: Path | None = None) -> Path:
    p = (root or Path.cwd()) / ".unpick" / "last-scan.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(res.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return p
