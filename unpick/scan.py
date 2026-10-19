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
TEXT_NAMES = {".cursorrules", ".clinerules", ".windsurfrules", ".gitattributes", ".gitmodules", ".npmrc", ".pypirc",
              "pip.conf", "pip.ini", "dockerfile", "makefile"}
MAX_BYTES = 2_000_000
IGNORE_FILE = ".unpickignore"
GIT_FILES = (".git/config", ".git/commondir")  # read even though .git/ is otherwise skipped (git_autorun check)
OPAQUE = {".mcpb", ".dxt", ".wasm", ".pyc", ".pyo", ".so", ".dylib", ".dll", ".node", ".exe", ".jar", ".zip",
          ".tgz", ".gz", ".whl", ".vsix", ".bin"}
UNREAD_RULE = "RT-UNREAD"
UNREAD_WHY = "This file is in a format unpick cannot read, so a clean result says nothing about it; bundles, WebAssembly and compiled code can carry anything."
UNREAD_FP = "Images, fonts and lock files are routinely skipped; it matters when the file is something the component runs or installs."


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


def _skip_reason(p: Path) -> str | None:
    if p.name == "decisions.json" or p.name.endswith(".decisions.json"):
        return "state"  # unpick's own state, not a component
    if p.suffix.lower() not in TEXT_EXT and p.name.lower() not in TEXT_NAMES:
        return "not a text format"
    if p.stat().st_size > MAX_BYTES:
        return f"larger than {MAX_BYTES // 1_000_000} MB"
    with p.open("rb") as fh:
        if b"\x00" in fh.read(8192):
            return "binary"
    return None


def walk(target: Path) -> tuple[Path, list[Path], list[tuple[str, str]]]:
    """Return (root, files to read, skipped (relative path, reason)). A file target is its own only file."""
    target = target.resolve()
    if target.is_file():
        reason = _skip_reason(target)
        return target.parent, ([] if reason and reason != "state" else [target]), ([(target.name, reason)] if reason else [])
    patterns = _ignored(target)
    files, skipped = [], []
    for p in sorted(target.rglob("*")):
        parts = p.relative_to(target).parts
        rel = p.relative_to(target).as_posix()
        if rel in GIT_FILES and p.is_file():
            files.append(p)
            continue
        if any(part in SKIP_DIRS for part in parts[:-1]) or not p.is_file() or p.is_symlink():
            continue
        if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.rstrip("/") + "/*") for pat in patterns):
            continue
        reason = _skip_reason(p)
        if reason == "state":
            continue
        if reason:
            skipped.append((rel, reason))
        else:
            files.append(p)
    return target, files, skipped


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
    skipped: list[dict] = field(default_factory=list)

    @property
    def network_calls(self) -> list[dict]:
        return [r for r in self.runs if r.get("network")]

    def to_dict(self) -> dict:
        everything = self.findings + self.accepted
        return {
            "tool": "unpick", "version": __version__, "target": self.target, "started_at": self.started_at,
            "sources": self.sources, "files": self.files, "runs": self.runs, "errors": self.errors,
            "unavailable": self.unavailable, "skipped": self.skipped,
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
        if not self.files and not self.findings:
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

    root, files, skipped = walk(target)
    res = ScanResult(target=str(target), started_at=datetime.now(UTC).isoformat(timespec="seconds"),
                     sources=["builtin"], files=[])
    res.skipped = [{"path": rel, "reason": why} for rel, why in skipped]
    for rel, why in skipped:
        if Path(rel).suffix.lower() in OPAQUE or why == "binary" or why.startswith("larger"):
            res.findings.append(Finding(
                rule_id=UNREAD_RULE, source="builtin", severity="medium", path=rel, line=0,
                message=f"not read ({why}); review it another way or remove it", why=UNREAD_WHY, false_positive=UNREAD_FP))
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
