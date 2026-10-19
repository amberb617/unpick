"""`unpick inventory`: find the AI components already on this machine and in the current project.

Locations come from data/locations.json, one entry per host, kind, scope and OS, each checked against the
host's current documentation (see docs/verified/inventory.md). Inventory reads only what identifies a
component: a skill's frontmatter name, a plugin manifest's name and version, an MCP config's server
entries, a hook's event. It never reads skill bodies or scripts; `scan` does that.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import platform
import re
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import yaml

from unpick.resources import load_json

PLUGIN_MANIFESTS = (".claude-plugin/plugin.json", "plugin.json", "gemini-extension.json", "package.json")
MAX_DEPTH = 5


def current_os() -> str:
    return {"Darwin": "mac", "Windows": "windows"}.get(platform.system(), "linux")


def expand(path: str, project: Path) -> list[Path]:
    """Expand ~, %VARS% and globs. Project-scope paths are relative to the project root."""
    p = os.path.expanduser(path)
    missing = False

    def env(m):
        nonlocal missing
        v = os.environ.get(m.group(1))
        if v is None:
            missing = True
        return v or ""

    p = re.sub(r"%([A-Za-z_]+)%", env, p)
    p = re.sub(r"\$\{?([A-Z_][A-Z0-9_]*)\}?", lambda m: os.environ.get(m.group(1), m.group(0)), p)
    if missing:
        return []
    if not os.path.isabs(p):
        p = str(project / p)
    if any(c in p for c in "*?["):
        return [Path(x) for x in sorted(glob.glob(p, recursive=True))]
    return [Path(p)]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(d: Path) -> str:
    """Directory hash: sha256 over sorted (relative path, file hash) pairs. Symlinks are hashed as links, not followed."""
    h = hashlib.sha256()
    for p in sorted(d.rglob("*")):
        rel = p.relative_to(d).as_posix()
        if p.is_symlink():
            h.update(f"L {rel} -> {os.readlink(p)}\n".encode())
        elif p.is_file():
            h.update(f"F {rel} {sha256_file(p)}\n".encode())
    return h.hexdigest()


def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments and trailing commas, leaving string contents alone."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        else:
            out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_config(p: Path, fmt: str):
    text = p.read_text(encoding="utf-8", errors="replace")
    if fmt == "toml" or p.suffix == ".toml":
        return tomllib.loads(text)
    if fmt == "yaml" or p.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(strip_jsonc(text))


def dig(obj, dotted: str):
    for part in dotted.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def _frontmatter_name(md: Path) -> str | None:
    try:
        with md.open(encoding="utf-8", errors="replace") as fh:
            if fh.readline().strip() != "---":
                return None
            for _ in range(40):
                line = fh.readline()
                if not line or line.strip() == "---":
                    return None
                m = re.match(r"\s*name\s*:\s*['\"]?([^'\"\n#]+)", line)
                if m:
                    return m.group(1).strip()
    except OSError:
        return None
    return None


def _git_remote(start: Path) -> str | None:
    for d in [start, *start.parents]:
        cfg = d / ".git" / "config"
        if cfg.is_file():
            m = re.search(r'\[remote "origin"\][^\[]*?url\s*=\s*(\S+)', cfg.read_text(encoding="utf-8", errors="replace"))
            return m.group(1) if m else None
    return None


def _manifest(d: Path) -> tuple[str | None, str | None, str | None]:
    for rel in PLUGIN_MANIFESTS:
        m = d / rel
        if m.is_file():
            try:
                data = json.loads(m.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if isinstance(data, dict):
                return data.get("name"), data.get("version"), rel
    return None, None, None


def _stat(p: Path) -> tuple[int, str]:
    if p.is_dir():
        size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file() and not f.is_symlink())
        mtime = max([f.stat().st_mtime for f in p.rglob("*") if f.is_file() and not f.is_symlink()] or [p.stat().st_mtime])
    else:
        size, mtime = p.stat().st_size, p.stat().st_mtime
    return size, datetime.fromtimestamp(mtime, UTC).isoformat(timespec="seconds")


def _display(p: Path | str) -> str:
    s = str(p)
    home = str(Path.home())
    return "~" + s[len(home):] if s.startswith(home) else s


def _component(kind, host, scope, path: Path, name, version=None, provenance=None, sha=None, entry=None, loc=None):
    size, modified = _stat(path)
    if sha is None:
        sha = sha256_dir(path) if path.is_dir() else sha256_file(path)
    if provenance is None:
        provenance = _git_remote(path if path.is_dir() else path.parent)
    return {
        "kind": kind, "host": host, "scope": scope, "path": str(path) + (f"#{entry}" if entry else ""),
        "display_path": _display(path) + (f"#{entry}" if entry else ""), "name": name or path.name,
        "version": version, "sha256": sha, "size": size, "modified": modified, "provenance": provenance,
        "location_verified": (loc or {}).get("verified", True), "source": (loc or {}).get("source"),
    }


def _skills(root: Path, host, scope, loc):
    for md in sorted(root.glob("*/SKILL.md")) + sorted(root.glob("*/*/SKILL.md")):
        d = md.parent
        yield _component("skill", host, scope, d, _frontmatter_name(md) or d.name, loc=loc)


def _plugins(root: Path, host, scope, loc):
    seen = set()
    for depth in range(1, MAX_DEPTH + 1):
        for d in sorted(root.glob("/".join(["*"] * depth))):
            if not d.is_dir() or any(str(d).startswith(s + os.sep) for s in seen):
                continue
            name, version, rel = _manifest(d)
            if rel and rel != "package.json":
                seen.add(str(d))
                yield _component("plugin" if "extension" not in rel else "extension", host, scope, d, name, version, loc=loc)


def _mcp(cfg: Path, host, scope, key, fmt, loc):
    try:
        data = load_config(cfg, fmt)
    except (ValueError, OSError, yaml.YAMLError, tomllib.TOMLDecodeError):
        return
    servers = dig(data, key) if key else None
    containers = [servers] if isinstance(servers, (dict, list)) else []
    if host == "claude-code" and cfg.name == ".claude.json" and isinstance(data.get("projects"), dict):
        containers += [p.get("mcpServers") for p in data["projects"].values() if isinstance(p, dict)]
    for servers in containers:
        items = servers.items() if isinstance(servers, dict) else ((s.get("name", str(i)), s) for i, s in enumerate(servers or []))
        for name, entry in items:
            if not isinstance(entry, dict):
                continue
            canon = json.dumps(entry, sort_keys=True).encode()
            cmd = entry.get("command") or entry.get("url") or entry.get("serverUrl") or ""
            args = entry.get("args") or []
            prov = " ".join([str(cmd), *map(str, args)])[:200] if cmd else None  # command and args only, never env
            yield _component("mcp-server", host, scope, cfg, name, provenance=prov, sha=hashlib.sha256(canon).hexdigest(),
                             entry=name, loc=loc)


def _npm_plugins(cfg: Path, scope, loc):
    """OpenCode's `plugin` array names npm packages that load into the agent."""
    try:
        data = load_config(cfg, "jsonc")
    except (ValueError, OSError):
        return
    for name in data.get("plugin", []) if isinstance(data, dict) else []:
        if isinstance(name, str):
            yield _component("plugin", "opencode", scope, cfg, name, provenance=f"npm:{name}",
                             sha=hashlib.sha256(name.encode()).hexdigest(), entry=f"plugin:{name}", loc=loc)


def _hooks(cfg: Path, host, scope, key, fmt, loc):
    try:
        data = load_config(cfg, fmt)
    except (ValueError, OSError, yaml.YAMLError, tomllib.TOMLDecodeError):
        return
    hooks = dig(data, key) if key else None
    if not isinstance(hooks, dict):
        return
    for event, groups in hooks.items():
        for i, group in enumerate(groups if isinstance(groups, list) else [groups]):
            canon = json.dumps(group, sort_keys=True).encode()
            matcher = group.get("matcher", "*") if isinstance(group, dict) else "*"
            yield _component("hook", host, scope, cfg, f"{event}[{matcher}]", sha=hashlib.sha256(canon).hexdigest(),
                             entry=f"{event}.{i}", provenance=None, loc=loc)


def from_location(loc: dict, project: Path):
    if current_os() not in loc.get("os", ["mac", "linux", "windows"]):
        return
    if loc["scope"] == "project" and not project:
        return
    for p in expand(loc["path"], project):
        if not p.exists():
            continue
        kind, host, scope = loc["kind"], loc["host"], loc["scope"]
        if kind in ("skills-root",) and p.is_dir():
            yield from _skills(p, host, scope, loc)
        elif kind == "skill-dir" and p.is_dir():
            yield _component("skill", host, scope, p, _frontmatter_name(p / "SKILL.md") or p.name, loc=loc)
        elif kind in ("plugin-root", "extension-root") and p.is_dir():
            yield from _plugins(p, host, scope, loc)
        elif kind == "mcp-config" and p.is_file():
            yield from _mcp(p, host, scope, loc.get("mcp_key"), loc.get("format"), loc)
            if host == "opencode":
                yield from _npm_plugins(p, scope, loc)
        elif kind == "autorun-file" and p.is_file():
            yield _component("autorun-file", host, scope, p, p.name, loc=loc)
        elif kind == "settings-hooks" and p.is_file():
            yield from _hooks(p, host, scope, loc.get("hooks_key") or "hooks", loc.get("format"), loc)
        elif kind == "rules-dir" and p.is_dir():
            for f in sorted(x for x in p.rglob("*") if x.is_file()):
                yield _component("rules-file", host, scope, f, f.name, loc=loc)
        elif kind in ("rules-file", "instructions-file", "rules-dir") and p.is_file():
            yield _component("rules-file" if kind != "instructions-file" else "instructions-file", host, scope, p, p.name, loc=loc)


def classify_extra(p: Path):
    """--add-path: work out what a user-supplied path is."""
    if p.is_dir() and (p / "SKILL.md").is_file():
        yield _component("skill", "user-added", "user", p, _frontmatter_name(p / "SKILL.md") or p.name)
    elif p.is_dir():
        yield from _skills(p, "user-added", "user", None)
        yield from _plugins(p, "user-added", "user", None)
    elif p.suffix in (".json", ".jsonc", ".toml", ".yaml", ".yml"):
        found = False
        for key in ("mcpServers", "mcp_servers", "servers", "context_servers", "mcp.servers"):
            for c in _mcp(p, "user-added", "user", key, "", None):
                found = True
                yield c
        if not found:
            yield _component("file", "user-added", "user", p, p.name)
    elif p.is_file():
        yield _component("rules-file" if p.suffix in (".md", ".mdc") else "file", "user-added", "user", p, p.name)


def discover(project: Path | None = None, extra: list[Path] | None = None, config: Path | None = None) -> list[dict]:
    project = (project or Path.cwd()).resolve()
    locations = list(load_json("locations.json"))
    if config:
        cfg = load_config(config, "")
        locations += cfg.get("locations", []) if isinstance(cfg, dict) else []
        extra = list(extra or []) + [Path(os.path.expanduser(p)) for p in (cfg.get("paths", []) if isinstance(cfg, dict) else [])]
    out, seen = [], set()
    for loc in locations:
        for c in from_location(loc, project):
            if c["path"] not in seen:
                seen.add(c["path"])
                out.append(c)
    for p in extra or []:
        for c in classify_extra(p.resolve()):
            if c["path"] not in seen:
                seen.add(c["path"])
                out.append(c)
    return out
