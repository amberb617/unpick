"""How an MCP server is launched: unpinned packages, outdated mcp-remote, plain-HTTP remotes, hidden binaries.

`npx -y some-mcp` runs whatever version the registry serves today, so a server that was clean when you
added it can change under you (the postmark-mcp pattern: clean for 15 versions, then a BCC line;
https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html). mcp-remote before 0.1.16 lets a
malicious remote server run commands on your machine (CVE-2025-6514,
https://nvd.nist.gov/vuln/detail/CVE-2025-6514). Remote servers over plain http send your tokens in clear.
"""

from __future__ import annotations

import re

from unpick.checks import Hit
from unpick.checks._config import host_kind, line_of, load

RULE_ID = "RT-MCP-LAUNCH"
TITLE = "Risky MCP server launch"
SEVERITY = "medium"
WHY = "This MCP server entry runs an unpinned package, a known-vulnerable launcher, a plain-HTTP remote or a binary hidden in your home folder, so what runs can change or be intercepted."
FALSE_POSITIVE = "Quick-start docs often use unpinned `npx -y`; pin the version once you have reviewed it, and the finding goes away."

KEYS = ("mcpServers", "servers", "context_servers", "mcp_servers", "mcp")
RUNNERS = {"npx": "-y", "bunx": None, "pnpm": "dlx", "uvx": None, "pipx": "run"}
PINNED = re.compile(r"@\d|==\d|@sha256:|^[./]")


def _servers(data):
    for key in KEYS:
        block = data.get(key) if isinstance(data, dict) else None
        if isinstance(block, dict):
            yield from block.items()


def _package(args: list[str]) -> str | None:
    for a in args:
        if not a.startswith("-") and a not in ("dlx", "run", "exec"):
            return a
    return None


def _mcp_remote_version(pkg: str) -> tuple[int, ...] | None:
    m = re.match(r"mcp-remote@(\d+)\.(\d+)\.(\d+)", pkg)
    return tuple(int(x) for x in m.groups()) if m else None


def applies(doc):
    return doc.is_json or doc.name.endswith(".toml")


def run(doc):
    data = load(doc)
    for name, entry in _servers(data):
        if not isinstance(entry, dict):
            continue
        line = line_of(doc, f'"{name}"', default=line_of(doc, name))
        cmd = str(entry.get("command") or "")
        args = [str(a) for a in entry.get("args") or []]
        url = entry.get("url") or entry.get("serverUrl") or ""
        exe = cmd.rsplit("/", 1)[-1].lower().removesuffix(".cmd").removesuffix(".exe")
        if exe in RUNNERS:
            pkg = _package(args)
            if pkg and pkg.split("/")[-1].startswith("mcp-remote"):
                ver = _mcp_remote_version(pkg)
                if ver is None or ver < (0, 1, 16):
                    yield Hit(line, f"{name}: mcp-remote {'unpinned' if ver is None else '.'.join(map(str, ver))} "
                                    "(versions before 0.1.16 allow command execution, CVE-2025-6514)", "high", {"server": name})
                    continue
            if pkg and not PINNED.search(pkg.split("/", 1)[-1] if pkg.startswith("@") else pkg):
                yield Hit(line, f"{name}: {exe} runs {pkg} without a pinned version", None, {"server": name, "package": pkg})
        if re.match(r"(~|\$HOME|%USERPROFILE%|/(Users|home)/[^/]+)/\.[^/]+/", cmd):
            yield Hit(line, f"{name}: runs a program from a hidden folder in your home directory: {cmd}", "high", {"server": name})
        if isinstance(url, str) and url.startswith("http://") and host_kind(url) != "loopback":
            yield Hit(line, f"{name}: remote MCP server over plain http: {url}", "high", {"server": name, "url": url})
