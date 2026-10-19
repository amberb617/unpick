"""Fetch a component into ~/.unpick/quarantine/<timestamp>-<name>/ without running any of it.

  * git: shallow clone with hooks, templates, fsmonitor, submodules and symlinks off, and no system or
    global git config, so neither the remote nor the checked-out .git can make git run a program.
  * archives (.zip, .tar.gz, .tgz, .tar): every member is checked before anything is written. Absolute
    paths, "..", symlinks, hard links and device files are refused; total size and file count are capped
    (zip bombs).
  * npm and PyPI: the registry metadata gives the tarball URL and its published digest; the download is
    checked against that digest and extracted as an archive. No npm or pip runs, so no install script runs.
  * a local path is copied, symlinks recorded and not followed.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

ROOT = Path.home() / ".unpick" / "quarantine"
MAX_TOTAL = 200_000_000
MAX_FILES = 20_000
UA = {"User-Agent": "unpick (https://github.com/amberb617/unpick)"}
META = ".unpick-check.json"


class Refused(RuntimeError):
    pass


@dataclass
class Source:
    kind: str  # git | npm | pypi | archive | path
    ref: str
    name: str
    version: str | None = None
    extra: dict = field(default_factory=dict)


GITHUB = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?(?:/tree/([^/\s]+)(/.*)?)?/?$")


def parse(ref: str) -> Source:
    if ref.startswith("npm:"):
        pkg = ref[4:]
        name, _, ver = pkg.rpartition("@") if pkg.count("@") > (1 if pkg.startswith("@") else 0) else (pkg, "", "")
        return Source("npm", ref, name or pkg, ver or None)
    if ref.startswith("pypi:"):
        name, _, ver = ref[5:].partition("==")
        return Source("pypi", ref, name, ver or None)
    if m := GITHUB.match(ref):
        owner, repo, branch, sub = m.groups()
        return Source("git", f"https://github.com/{owner}/{repo}.git", repo, branch,
                      {"owner": owner, "repo": repo, "subdir": (sub or "").strip("/")})
    if ref.startswith(("https://", "git@")) and (ref.endswith(".git") or "gitlab" in ref or "codeberg" in ref):
        return Source("git", ref, Path(ref.rstrip("/")).stem)
    if ref.startswith("https://") and re.search(r"\.(zip|tar\.gz|tgz|tar)$", ref):
        return Source("archive", ref, Path(ref).name.split(".")[0])
    p = Path(ref).expanduser()
    if p.exists():
        kind = "archive" if p.is_file() and re.search(r"\.(zip|tar\.gz|tgz|tar)$", p.name) else "path"
        return Source(kind, str(p.resolve()), p.name.split(".")[0])
    raise Refused(f"cannot tell what {ref!r} is: use a GitHub URL, a git URL, npm:<pkg>[@v], pypi:<pkg>[==v], an archive or a path")


def _dest(name: str) -> Path:
    safe = re.sub(r"[^\w.-]+", "-", name)[:60] or "component"
    d = ROOT / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{safe}"
    d.mkdir(parents=True, exist_ok=False)
    return d


def _member_ok(name: str) -> PurePosixPath:
    p = PurePosixPath(name.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or re.match(r"^[A-Za-z]:", name):
        raise Refused(f"archive member escapes the folder: {name}")
    return p


def safe_extract(data: bytes, dest: Path, strip_top: bool = False) -> int:
    """Extract a zip or tar archive held in memory. Returns the number of files written."""
    entries: list[tuple[PurePosixPath, bytes]] = []
    total = 0
    if data[:4] == b"PK\x03\x04":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise Refused(f"archive contains a symlink: {info.filename}")
                total += info.file_size
                if total > MAX_TOTAL or len(entries) > MAX_FILES:
                    raise Refused("archive too large when unpacked (possible zip bomb)")
                entries.append((_member_ok(info.filename), z.read(info)))
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as t:
            for m in t.getmembers():
                if m.isdir():
                    continue
                if not m.isfile():
                    raise Refused(f"archive contains a link or device file: {m.name}")
                total += m.size
                if total > MAX_TOTAL or len(entries) > MAX_FILES:
                    raise Refused("archive too large when unpacked (possible zip bomb)")
                f = t.extractfile(m)
                entries.append((_member_ok(m.name), f.read() if f else b""))
    for rel, body in entries:
        parts = rel.parts[1:] if strip_top and len(rel.parts) > 1 else rel.parts
        out = dest.joinpath(*parts)
        if not out.resolve().is_relative_to(dest.resolve()):
            raise Refused(f"archive member escapes the folder: {rel}")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        out.chmod(0o644)  # nothing extracted is executable
    return len(entries)


def _get(url: str, timeout: int = 60) -> bytes:
    if not url.startswith("https://"):
        raise Refused(f"refusing non-https download: {url}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - https only, checked above
        return r.read(MAX_TOTAL + 1)


def _get_json(url: str):
    return json.loads(_get(url, 30).decode("utf-8"))


def git_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="",
               GIT_LFS_SKIP_SMUDGE="1")
    return env


GIT_SAFE = ["-c", "core.hooksPath=" + os.devnull, "-c", "core.fsmonitor=false", "-c", "core.symlinks=false",
            "-c", "protocol.file.allow=never", "-c", "protocol.ext.allow=never", "-c", "submodule.recurse=false",
            "-c", "filter.lfs.smudge=", "-c", "filter.lfs.process=", "-c", "filter.lfs.required=false"]


def fetch_git(src: Source, dest: Path) -> dict:
    argv = ["git", *GIT_SAFE, "clone", "--depth", "1", "--no-recurse-submodules", "--template=", "--quiet"]
    if src.version:
        argv += ["--branch", src.version]
    argv += ["--", src.ref, str(dest / "repo")]
    p = subprocess.run(argv, capture_output=True, text=True, env=git_env(), timeout=300)
    if p.returncode != 0:
        raise Refused(f"git clone failed: {p.stderr.strip()[-300:]}")
    from unpick.lock import git_head
    commit = git_head(dest / "repo")
    if src.version and re.fullmatch(r"[0-9a-f]{40}", src.version) and commit != src.version:
        # Claude Code CVE-2026-86063: a branch named like a SHA wins over the commit you pinned.
        raise Refused(f"asked for commit {src.version} but got {commit}: a branch or tag is named like that SHA")
    root = dest / "repo" / src.extra.get("subdir", "") if src.extra.get("subdir") else dest / "repo"
    return {"commit": commit, "root": str(root)}


def fetch_npm(src: Source, dest: Path) -> dict:
    meta = _get_json(f"https://registry.npmjs.org/{src.name.replace('/', '%2F')}")
    ver = src.version or meta["dist-tags"]["latest"]
    info = meta["versions"][ver]
    data = _get(info["dist"]["tarball"])
    integ = info["dist"].get("integrity", "")
    if integ.startswith("sha512-"):
        if base64.b64encode(hashlib.sha512(data).digest()).decode() != integ[7:]:
            raise Refused("tarball does not match the registry's sha512 integrity")
    elif hashlib.sha1(data).hexdigest() != info["dist"].get("shasum"):  # noqa: S324 - registry's own legacy digest
        raise Refused("tarball does not match the registry's shasum")
    safe_extract(data, dest / "package", strip_top=True)
    return {"version": ver, "root": str(dest / "package"), "integrity": integ or info["dist"].get("shasum"),
            "registry": meta}


def fetch_pypi(src: Source, dest: Path) -> dict:
    url = f"https://pypi.org/pypi/{src.name}/{src.version}/json" if src.version else f"https://pypi.org/pypi/{src.name}/json"
    meta = _get_json(url)
    files = meta["urls"]
    pick = next((f for f in files if f["packagetype"] == "sdist"), None) or next(f for f in files if f["filename"].endswith(".whl"))
    data = _get(pick["url"])
    if hashlib.sha256(data).hexdigest() != pick["digests"]["sha256"]:
        raise Refused("download does not match PyPI's sha256")
    safe_extract(data, dest / "package", strip_top=pick["packagetype"] == "sdist")
    return {"version": meta["info"]["version"], "root": str(dest / "package"), "sha256": pick["digests"]["sha256"],
            "registry": meta}


def fetch_archive(src: Source, dest: Path) -> dict:
    data = _get(src.ref) if src.ref.startswith("https://") else Path(src.ref).read_bytes()
    n = safe_extract(data, dest / "package")
    return {"root": str(dest / "package"), "sha256": hashlib.sha256(data).hexdigest(), "files": n}


def fetch_path(src: Source, dest: Path) -> dict:
    target = dest / "package"
    p = Path(src.ref)
    if p.is_file():
        target.mkdir()
        shutil.copy2(p, target / p.name)
    else:
        shutil.copytree(p, target, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    return {"root": str(target)}


FETCHERS = {"git": fetch_git, "npm": fetch_npm, "pypi": fetch_pypi, "archive": fetch_archive, "path": fetch_path}
NETWORK = {"git": True, "npm": True, "pypi": True, "archive": None, "path": False}


def needs_network(src: Source) -> bool:
    if src.kind == "archive":
        return src.ref.startswith("https://")
    return bool(NETWORK[src.kind])


def fetch(src: Source) -> tuple[Path, dict]:
    dest = _dest(src.name)
    try:
        info = FETCHERS[src.kind](src, dest)
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    return dest, info


def save_meta(dest: Path, meta: dict) -> None:
    (dest / META).write_text(json.dumps(meta, indent=2, ensure_ascii=True, default=str) + "\n", encoding="utf-8")


def load_meta(check_id: str) -> tuple[Path, dict]:
    d = ROOT / check_id
    if not (d / META).is_file():
        raise Refused(f"no check with id {check_id!r} in {ROOT}")
    return d, json.loads((d / META).read_text(encoding="utf-8"))
