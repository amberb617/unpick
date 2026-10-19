"""Shared helpers for checks that read agent and editor configuration files."""

from __future__ import annotations

import ipaddress
import json
import re
import tomllib
from urllib.parse import urlparse

VENDOR_HOSTS = ("api.anthropic.com", "api.openai.com", "generativelanguage.googleapis.com", "aiplatform.googleapis.com",
                "amazonaws.com", "openai.azure.com", "api.x.ai", "api.mistral.ai", "openrouter.ai")


def load(doc):
    """Parse a JSON, JSONC or TOML doc. Returns None when it is not one of those or does not parse."""
    from unpick.inventory import strip_jsonc
    try:
        if doc.name.endswith(".toml"):
            return tomllib.loads(doc.text)
        if doc.is_json:
            return json.loads(strip_jsonc(doc.text))
    except (ValueError, tomllib.TOMLDecodeError):
        return None
    return None


def dig(obj, *path):
    for p in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(p)
    return obj


def line_of(doc, *needles, default: int = 1) -> int:
    for n, line in enumerate(doc.lines, 1):
        if all(x in line for x in needles):
            return n
    return default


def host_kind(url: str) -> str:
    """'vendor', 'loopback' or 'other' for a base URL."""
    host = (urlparse(url if "://" in url else "https://" + url).hostname or "").lower()
    try:
        if ipaddress.ip_address(host).is_loopback:
            return "loopback"
    except ValueError:
        if host == "localhost":
            return "loopback"
    return "vendor" if any(host == v or host.endswith("." + v) for v in VENDOR_HOSTS) else "other"


def path_is(doc, *suffixes: str) -> bool:
    p = doc.path.as_posix().lower()
    return any(p.endswith(s) for s in suffixes)


REPO_SCRIPT = re.compile(r"(^|\s)(node|bun|deno|python3?|bash|sh|zsh|pwsh|powershell)\s+(\./|\.claude/|\.vscode/|\.cursor/|\.codex/|\.opencode/|scripts?/)"
                         r"|(^|\s)\./[\w./-]+|\$CLAUDE_PROJECT_DIR", re.I)
DOWNLOAD = re.compile(r"\b(curl|wget|iwr|irm|invoke-webrequest)\b|https?://", re.I)
