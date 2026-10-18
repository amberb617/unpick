"""The harness: run the open-source scanners a person already has, in their offline modes.

Every backend is optional. runthrough is fully useful with none installed. Adding a scanner means adding
one file in this folder that defines:

    NAME, MAINTAINER, LICENSE, HOMEPAGE
    TESTED_VERSION          -- the version the adapter and its recorded fixture were checked against
    INSTALL                 -- pip requirement string pinned to TESTED_VERSION, or None
    NETWORK                 -- plain-language description of network calls made by COMMAND, or "none"
    NEEDS_ONLINE            -- True if COMMAND makes a network call (then it only runs with --online or --boxed)
    applies(target) -> bool -- does this scanner understand the target?
    version() -> str|None   -- installed version, or None if not installed
    command(target) -> list[str]
    parse(stdout: str, target: Path) -> list[Finding]

See CONTRIBUTING.md.
"""

from __future__ import annotations

import importlib
import pkgutil
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from runthrough.finding import Finding

TIMEOUT = 300


@dataclass
class BackendRun:
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    unavailable: bool = False


def adapters() -> dict:
    out = {}
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{info.name}")
        out[mod.NAME] = mod
    return dict(sorted(out.items()))


def describe() -> list[dict]:
    rows = []
    for name, mod in adapters().items():
        rows.append({
            "name": name, "installed": mod.version() is not None, "version": mod.version(),
            "tested_version": mod.TESTED_VERSION, "maintainer": mod.MAINTAINER, "license": mod.LICENSE,
            "network": mod.NETWORK, "needs_online": mod.NEEDS_ONLINE, "homepage": mod.HOMEPAGE,
            "unverified": getattr(mod, "UNVERIFIED", None),
        })
    return rows


def run(name: str, target: Path, boxed: bool = False, online: bool = False) -> BackendRun:
    from runthrough import box

    mods = adapters()
    meta = {"kind": "backend", "name": name, "source": f"backend:{name}"}
    if name not in mods:
        return BackendRun(errors=[f"unknown backend {name!r}"], meta={**meta, "status": "unknown"}, unavailable=True)
    mod = mods[name]
    ver = mod.version()
    meta.update(version=ver, tested_version=mod.TESTED_VERSION, network=mod.NEEDS_ONLINE and not boxed,
                network_detail=mod.NETWORK, boxed=boxed)
    if ver is None:
        return BackendRun(meta={**meta, "status": "not installed"}, unavailable=True)
    if not mod.applies(target):
        return BackendRun(meta={**meta, "status": "not applicable", "network": False})
    if mod.NEEDS_ONLINE and not (online or boxed):
        return BackendRun(errors=[f"{name} makes a network call ({mod.NETWORK}); pass --online to allow it or --boxed to cut it off"],
                          meta={**meta, "status": "skipped: needs --online", "network": False}, unavailable=True)
    argv = mod.command(target)
    try:
        if boxed:
            proc = box.run(argv, read_only=[target.resolve()], tool=name)
        else:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT, encoding="utf-8", errors="replace")
    except box.NoBox as e:
        return BackendRun(errors=[str(e)], meta={**meta, "status": "no box available"}, unavailable=True)
    except (OSError, subprocess.TimeoutExpired) as e:
        return BackendRun(errors=[f"{name}: {e}"], meta={**meta, "status": "error", "argv": argv})
    meta.update(argv=argv, exit_code=proc.returncode, status="ran")
    try:
        findings = mod.parse(proc.stdout, target)
    except Exception as e:  # a parser bug must not hide the built-in results
        return BackendRun(errors=[f"{name}: could not parse output ({e}); stderr: {proc.stderr[-500:]}"],
                          meta={**meta, "status": "parse error"})
    return BackendRun(findings=findings, meta=meta)


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def version_of(argv: list[str]) -> str | None:
    """Run a `--version` style command and return the first line, or None if the tool is missing."""
    if not shutil.which(argv[0]):
        return None
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (out.stdout or out.stderr).strip().splitlines()
    return text[0].strip() if text else "unknown"


def install(name: str, online: bool, docker: bool = False) -> tuple[int, str]:
    """Install a backend's pinned version. This downloads from PyPI (and Docker Hub with --docker), so it requires --online."""
    from runthrough import box

    mods = adapters()
    if name not in mods:
        return 2, f"unknown backend {name!r}; see `runthrough backends`"
    mod = mods[name]
    if not online:
        return 2, f"installing {name} downloads {mod.INSTALL or 'it'} from the internet; re-run with --online"
    if not mod.INSTALL:
        return 2, f"{name} is not pip-installable; see {mod.HOMEPAGE}"
    if docker:
        if not shutil.which("docker"):
            return 2, "docker not found"
        return box.build_image(name, mod.INSTALL)
    for tool in (["pipx", "install", mod.INSTALL], ["uv", "tool", "install", mod.INSTALL]):
        if shutil.which(tool[0]):
            p = subprocess.run(tool, capture_output=True, text=True)
            return p.returncode, (p.stdout + p.stderr).strip()
    return 2, "need pipx or uv to install backends into their own environment"
