"""`unpick outdated --online`: newer upstream versions of what you locked, read before you update.

For npm and PyPI MCP servers it compares the pinned version with the registry's latest and flags a change
of publisher between them (the postmark-mcp pattern was a new version from the same impostor; the
skills.sh campaign swapped content under the same name). For git components it fetches the new commit
into quarantine, diffs it file by file against the installed copy, and scans it, so you read the diff
before updating. Network: registry and GitHub API lookups by name, and the fetch; listed in README.
"""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from unpick import lock, provenance, quarantine, scan

NPX = re.compile(r"\b(?:npx|bunx|pnpm\s+dlx)\s+(?:-y\s+)?((?:@[\w.-]+/)?[\w.-]+)(?:@([\w.+-]+))?")
UVX = re.compile(r"\buvx\s+([\w.-]+)(?:==([\w.+-]+))?")
GH_REMOTE = re.compile(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?$")


def _npm(pkg: str, pinned: str | None) -> dict:
    meta = quarantine._get_json(f"https://registry.npmjs.org/{pkg.replace('/', '%2F')}")
    latest = meta["dist-tags"]["latest"]
    out = {"kind": "npm", "package": pkg, "pinned": pinned, "latest": latest, "outdated": bool(pinned) and pinned != latest}
    if pinned and pinned in meta["versions"]:
        old = (meta["versions"][pinned].get("_npmUser") or {}).get("name")
        new = (meta["versions"][latest].get("_npmUser") or {}).get("name")
        out["publisher_changed"] = old != new
        out["publishers"] = {"pinned": old, "latest": new}
    if not pinned:
        out["note"] = "not pinned: every launch runs whatever version is latest"
    return out


def _pypi(pkg: str, pinned: str | None) -> dict:
    meta = quarantine._get_json(f"https://pypi.org/pypi/{pkg}/json")
    latest = meta["info"]["version"]
    return {"kind": "pypi", "package": pkg, "pinned": pinned, "latest": latest, "outdated": bool(pinned) and pinned != latest}


def _git(c: dict, path: Path, fetch: bool) -> dict | None:
    m = GH_REMOTE.search(c.get("provenance") or "")
    if not m or not c.get("commit"):
        return None
    owner, repo = m.groups()
    card = provenance.github(owner, repo)
    head, _ = provenance._json(f"https://api.github.com/repos/{owner}/{repo}/commits/{card['default_branch']}")
    out = {"kind": "git", "repo": f"{owner}/{repo}", "pinned": c["commit"], "latest": head["sha"],
           "outdated": head["sha"] != c["commit"], "moved": card["renamed_or_transferred"]}
    if out["outdated"] and fetch:
        src = quarantine.Source("git", f"https://github.com/{owner}/{repo}.git", repo, None, {"owner": owner, "repo": repo})
        dest, info = quarantine.fetch(src)
        new_root = Path(info["root"])
        rel = path.relative_to(_repo_root(path)) if _repo_root(path) else Path()
        new_dir = new_root / rel
        out["quarantine"] = str(dest)
        out["diff"] = tree_diff(path, new_dir)
        res = scan.scan(new_dir, decision_files=[])
        out["scan_open"] = len(res.findings)
    return out


def _repo_root(p: Path) -> Path | None:
    for d in [p, *p.parents]:
        if (d / ".git").exists():
            return d
    return None


def tree_diff(old: Path, new: Path) -> str:
    """Unified diff of every text file between two folders, ignoring .git."""
    def files(root: Path):
        return {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}
    a, b = files(old), files(new)
    out = []
    for rel in sorted(set(a) | set(b)):
        x = a[rel].read_text(encoding="utf-8", errors="replace").splitlines(True) if rel in a else []
        y = b[rel].read_text(encoding="utf-8", errors="replace").splitlines(True) if rel in b else []
        if x != y:
            out.append("".join(difflib.unified_diff(x, y, f"installed/{rel}", f"upstream/{rel}")))
    return "".join(out)


def outdated(project: Path, fetch: bool = True) -> list[dict]:
    lf = project / lock.LOCKFILE
    if not lf.is_file():
        raise FileNotFoundError(f"no lockfile at {lf}; run `unpick lock` first")
    comps = json.loads(lf.read_text(encoding="utf-8"))["components"]
    rows = []
    for key, c in comps.items():
        prov = c.get("provenance") or ""
        try:
            if c["kind"] == "mcp-server" and (m := NPX.search(prov)):
                rows.append({"name": c["name"], **_npm(m.group(1), m.group(2))})
            elif c["kind"] == "mcp-server" and (m := UVX.search(prov)):
                rows.append({"name": c["name"], **_pypi(m.group(1), m.group(2))})
            elif c.get("commit") and (r := _git(c, Path(key.partition("#")[0]), fetch)):
                rows.append({"name": c["name"], **r})
        except (OSError, KeyError, ValueError, quarantine.Refused) as e:
            rows.append({"name": c["name"], "error": str(e)[:200]})
    return rows
