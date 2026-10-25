"""`unpick lock` and `unpick verify`: step 5 of the triage, pin it and re-check it.

Approval is a moment; exposure is continuous. postmark-mcp was clean for fifteen versions before one
added a BCC line (https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html), and the
skills.sh campaign uploaded clean skills and swapped them later (Zenity Labs, 2026-07). `lock` records
every inventoried component with per-file SHA-256 and, for git checkouts, the commit. `verify` compares
the machine with that record, shows a unified diff for every changed text file, re-scans only what
changed, and flags MCP and hook entries whose command, arguments, environment or URL changed.

Commits are read from the .git files directly. unpick never runs git inside a component, because a
repository's own .git/config can make git run programs (Codex CVE-2026-19590..19593).
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from unpick import __version__, inventory

LOCKFILE = "unpick.lock.json"
SNAPSHOTS = Path.home() / ".unpick" / "snapshots"
SNAPSHOT_MAX = 512_000  # bytes; larger files are hashed, not snapshotted
TEXT_SUFFIX = {".md", ".mdc", ".json", ".jsonc", ".toml", ".yaml", ".yml", ".txt", ".sh", ".ps1", ".py", ".js",
               ".mjs", ".ts"}


SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


def _sha(text: str) -> str | None:
    return text.strip() if SHA.fullmatch(text.strip()) else None


def git_head(start: Path) -> str | None:
    """The checked-out commit, read from .git/HEAD and refs without running git.

    A component's own .git decides which file is read, so only a hex SHA is ever returned: a HEAD of
    `ref: ../../.ssh/id_rsa` must not put that file's contents into the lockfile."""
    try:
        return _git_head(start)
    except OSError:
        return None


def _git_head(start: Path) -> str | None:
    for d in [start, *start.parents]:
        git = d / ".git"
        if git.is_file():  # worktree or submodule: "gitdir: <path>"
            target = git.read_text(encoding="utf-8", errors="replace").partition("gitdir:")[2].strip()
            git = (d / target).resolve()
        if not git.is_dir():
            continue
        head = (git / "HEAD").read_text(encoding="utf-8", errors="replace").strip()
        if not head.startswith("ref:"):
            return _sha(head)
        ref = head.split(":", 1)[1].strip()
        if not ref.startswith("refs/") or ".." in ref.split("/"):
            return None
        loose = git / ref
        if loose.is_file():
            return _sha(loose.read_text(encoding="utf-8", errors="replace"))
        packed = git / "packed-refs"
        if packed.is_file():
            for line in packed.read_text(encoding="utf-8", errors="replace").splitlines():
                sha, _, name = line.partition(" ")
                if name == ref:
                    return _sha(sha)
        return None
    return None


def _snapshot(p: Path, digest: str) -> None:
    if p.suffix.lower() in TEXT_SUFFIX and p.stat().st_size <= SNAPSHOT_MAX:
        dest = SNAPSHOTS / digest[:2] / digest
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(p.read_bytes())


def file_hashes(path: Path, snapshot: bool = True) -> dict[str, str]:
    """Per-file SHA-256 for a component folder or file. Symlinks are recorded, never followed."""
    if path.is_file():
        files = [path]
        base = path.parent
    else:
        files = sorted(p for p in path.rglob("*") if (p.is_file() or p.is_symlink()) and ".git" not in p.relative_to(path).parts)
        base = path
    out = {}
    for p in files:
        rel = p.relative_to(base).as_posix()
        if p.is_symlink():
            out[rel] = "symlink:" + os.readlink(p)
            continue
        digest = inventory.sha256_file(p)
        out[rel] = digest
        if snapshot:
            _snapshot(p, digest)
    return out


def _redact_entry(cfg: Path, name: str) -> dict | None:
    """The MCP / hook entry as recorded: command, args, URL, and env as key -> sha256 of the value."""
    try:
        data = inventory.load_config(cfg, "")
    except (ValueError, OSError):
        return None
    for key in ("mcpServers", "servers", "context_servers", "mcp_servers", "mcp"):
        block = data.get(key) if isinstance(data, dict) else None
        if isinstance(block, dict) and isinstance(block.get(name), dict):
            e = dict(block[name])
            if isinstance(e.get("env"), dict):
                e["env"] = {k: "sha256:" + hashlib.sha256(str(v).encode()).hexdigest()[:16] for k, v in e["env"].items()}
            if isinstance(e.get("headers"), dict):
                e["headers"] = {k: "sha256:" + hashlib.sha256(str(v).encode()).hexdigest()[:16] for k, v in e["headers"].items()}
            return e
    return None


def record(c: dict) -> dict:
    path_s, _, entry = c["path"].partition("#")
    path = Path(path_s)
    r = {k: c[k] for k in ("kind", "host", "scope", "name", "version", "provenance", "sha256")}
    r["path"] = c["display_path"]
    if entry:
        r["entry"] = entry
        r["config"] = _redact_entry(path, entry)
    elif path.exists():
        r["files"] = file_hashes(path)
        r["commit"] = git_head(path if path.is_dir() else path.parent)
    return r


def lock(project: Path, out: Path | None = None, extra: list[Path] | None = None) -> dict:
    items = inventory.discover(project=project, extra=extra)
    data = {"tool": "unpick", "version": __version__, "locked_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "components": {c["path"]: record(c) for c in items}}
    target = out or project / LOCKFILE
    try:  # records saved by `unpick check` live in the same file; re-locking must not drop them
        prior = json.loads(target.read_text(encoding="utf-8")).get("approved") if target.is_file() else None
    except ValueError:
        prior = None
    if prior:
        data["approved"] = prior
    target.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return data


def _text_diff(old_digest: str, new_path: Path, rel: str) -> str | None:
    old = SNAPSHOTS / old_digest[:2] / old_digest
    if not old.is_file() or not new_path.is_file():
        return None
    a = old.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    b = new_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    return "".join(difflib.unified_diff(a, b, f"a/{rel}", f"b/{rel}"))


def _file_changes(old: dict, path: Path) -> list[dict]:
    new = file_hashes(path, snapshot=False)
    base = path if path.is_dir() else path.parent
    changes = []
    for rel in sorted(set(old) | set(new)):
        if old.get(rel) == new.get(rel):
            continue
        status = "changed"
        if rel not in old:
            status = "added"
        elif rel not in new:
            status = "removed"
        ch = {"file": rel, "status": status}
        if status == "changed" and not old[rel].startswith("symlink:"):
            ch["diff"] = _text_diff(old[rel], base / rel if path.is_dir() else path, rel)
        changes.append(ch)
    return changes


def _entry_changes(old: dict | None, new: dict | None) -> list[dict]:
    old, new = old or {}, new or {}
    return [{"field": k, "old": old.get(k), "new": new.get(k)} for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]


def verify(project: Path, lockfile: Path | None = None, rescan: bool = True) -> dict:
    from unpick import scan

    lf = lockfile or project / LOCKFILE
    if not lf.is_file():
        raise FileNotFoundError(f"no lockfile at {lf}; run `unpick lock` first")
    data = json.loads(lf.read_text(encoding="utf-8"))
    if not data.get("components") and "locked_at" not in data:  # only `unpick check` records so far: nothing to compare
        raise FileNotFoundError(f"no lockfile components at {lf}; run `unpick lock` first")
    locked = data["components"]
    current = {c["path"]: c for c in inventory.discover(project=project)}
    report = {"lockfile": str(lf), "added": [], "removed": [], "changed": [], "unchanged": 0}
    for key in sorted(set(locked) | set(current)):
        if key not in current:
            report["removed"].append(locked[key])
            continue
        c = current[key]
        if key not in locked:
            report["added"].append({k: c[k] for k in ("kind", "host", "name", "display_path", "sha256")})
            continue
        old = locked[key]
        path_s, _, entry = key.partition("#")
        item = {"kind": c["kind"], "host": c["host"], "name": c["name"], "path": c["display_path"]}
        if entry:
            fields = _entry_changes(old.get("config"), _redact_entry(Path(path_s), entry))
            if fields:
                report["changed"].append({**item, "config_changes": fields})
            else:
                report["unchanged"] += 1
            continue
        commit = git_head(Path(path_s) if Path(path_s).is_dir() else Path(path_s).parent)
        if c["sha256"] == old["sha256"] and commit == old.get("commit"):
            report["unchanged"] += 1
            continue
        item["files"] = _file_changes(old.get("files", {}), Path(path_s))
        if commit != old.get("commit"):
            item["commit"] = {"old": old.get("commit"), "new": commit}
        if rescan:
            res = scan.scan(Path(path_s), decision_files=None)
            item["scan"] = {"open": len(res.findings), "findings": [f.to_dict() for f in res.findings]}
        report["changed"].append(item)
    report["ok"] = not (report["added"] or report["removed"] or report["changed"])
    return report
