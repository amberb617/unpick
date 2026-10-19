"""Agent settings that switch off approvals or send your traffic somewhere else.

A repository can carry agent configuration that removes every confirmation prompt or points the agent at
a third-party model endpoint. Claude Code CVE-2026-33068 (`permissions.defaultMode: bypassPermissions` read
before the trust dialog) and CVE-2026-21852 (a project `ANTHROPIC_BASE_URL` sent the API key to an attacker,
https://github.com/advisories/GHSA-jh7p-qr78-84p7); VS Code `chat.permissions.default: autoApprove` in
workspace settings (Repello, 2026-06-04, https://repello.ai/blog/vscode-copilot-workspace-trust-bypass); OpenCode and Codex equivalents. A rerouted base URL is also how a
malicious model router sees everything: 9 of 428 routers studied injected code into tool calls
(arXiv:2604.08407). Sources in docs/research/2026-10-landscape.md.
"""

from __future__ import annotations

import re

from unpick.checks import Hit
from unpick.checks._config import dig, host_kind, line_of, load, path_is

RULE_ID = "RT-AGENT-SETTINGS"
TITLE = "Approvals off or traffic rerouted"
SEVERITY = "high"
WHY = "This configuration turns off the agent's confirmation prompts or sends its model traffic, including your API key and code, to an endpoint other than the vendor's."
FALSE_POSITIVE = "People do run agents in a disposable VM with prompts off, or through their own company gateway; that choice belongs in your user settings, not in a repository you cloned."

EXPORT = re.compile(r"\b(?:export\s+|set\s+|\$env:)?((?:ANTHROPIC|OPENAI|GEMINI|GOOGLE|XAI|OPENROUTER)_(?:BEDROCK_)?BASE_URL)\s*=\s*['\"]?((?:https?://)?[\w-]+(?:\.[\w-]+)+(?::\d+)?(?:/[^\s'\"]*)?)", re.I)


def _base_url(doc, name: str, url) -> Hit | None:
    if not isinstance(url, str):
        return None
    kind = host_kind(url)
    if kind == "vendor":
        return None
    sev = "low" if kind == "loopback" else "high"
    return Hit(line_of(doc, url[:40]), f"{name} points at {url} ({'a local proxy' if kind == 'loopback' else 'not the vendor'})", sev,
               {"setting": name, "url": url})


def _claude(doc, d):
    if dig(d, "permissions", "defaultMode") == "bypassPermissions":
        yield Hit(line_of(doc, "bypassPermissions"), "permissions.defaultMode is bypassPermissions: every tool call runs without asking")
    if d.get("enableAllProjectMcpServers") is True:
        yield Hit(line_of(doc, "enableAllProjectMcpServers"), "enableAllProjectMcpServers starts every MCP server the repo lists, without asking", "medium")
    if isinstance(d.get("apiKeyHelper"), str):
        yield Hit(line_of(doc, "apiKeyHelper"), f"apiKeyHelper runs a command to fetch your API key: {d['apiKeyHelper'][:80]}", "medium")
    for k, v in (d.get("env") or {}).items() if isinstance(d.get("env"), dict) else []:
        if k.upper().endswith("BASE_URL") and (hit := _base_url(doc, f"env.{k}", v)):
            yield hit


def _vscode(doc, d):
    flat = {k: v for k, v in d.items()} if isinstance(d, dict) else {}
    if flat.get("chat.permissions.default") == "autoApprove" or dig(d, "chat", "permissions", "default") == "autoApprove":
        yield Hit(line_of(doc, "autoApprove"), "chat.permissions.default is autoApprove: Copilot agent runs terminal, edit and MCP calls without asking")
    if flat.get("chat.tools.autoApprove") is True:
        yield Hit(line_of(doc, "chat.tools.autoApprove"), "chat.tools.autoApprove approves every tool call")
    term = flat.get("chat.tools.terminal.autoApprove")
    if term:
        broad = term is True or (isinstance(term, dict) and any(k in ("/.*/", "/.+/", "*") or v is True and k.startswith("/") for k, v in term.items()))
        yield Hit(line_of(doc, "chat.tools.terminal.autoApprove"), "chat.tools.terminal.autoApprove pre-approves terminal commands",
                  "high" if broad else "medium", {"value": term})


def _opencode(doc, d):
    perm = d.get("permission")
    if perm == "allow" or (isinstance(perm, dict) and perm.get("bash") == "allow"):
        yield Hit(line_of(doc, '"permission"'), "OpenCode permission set to allow: no prompts, including for shell commands")
    for name, prov in (d.get("provider") or {}).items() if isinstance(d.get("provider"), dict) else []:
        if hit := _base_url(doc, f"provider.{name}.options.baseURL", dig(prov, "options", "baseURL")):
            yield hit


def _codex(doc, d):
    if d.get("approval_policy") == "never":
        yield Hit(line_of(doc, "approval_policy"), "approval_policy = never: Codex never asks")
    if d.get("sandbox_mode") == "danger-full-access":
        yield Hit(line_of(doc, "danger-full-access"), "sandbox_mode = danger-full-access: Codex runs without its sandbox")
    for name, prov in (d.get("model_providers") or {}).items() if isinstance(d.get("model_providers"), dict) else []:
        if hit := _base_url(doc, f"model_providers.{name}.base_url", dig(prov, "base_url")):
            yield hit


def _gemini(doc, d):
    allowed = dig(d, "tools", "allowed") or []
    if any(a in ("*", "run_shell_command") for a in allowed if isinstance(a, str)):
        yield Hit(line_of(doc, "allowed"), "Gemini CLI tools.allowed approves shell commands without asking")
    if "yolo" in doc.text.lower():
        yield Hit(line_of(doc, "yolo"), "Gemini CLI yolo mode: every tool call auto-approved", "medium")


def applies(doc):
    return doc.is_json or doc.name.endswith(".toml") or doc.is_markdown or doc.name.endswith((".sh", ".ps1", ".env.example"))


def run(doc):
    if doc.is_markdown or doc.name.endswith((".sh", ".ps1", ".env.example")):
        if "/.opencode/agent" in doc.path.as_posix() or "/opencode/agent" in doc.path.as_posix():
            for n, line in enumerate(doc.lines[:40], 1):
                if re.match(r"\s*(permission|bash)\s*:\s*['\"]?allow", line):
                    yield Hit(n, "OpenCode agent frontmatter allows every tool without asking")
        for n, line in enumerate(doc.lines, 1):
            for m in EXPORT.finditer(line):
                if host_kind(m.group(2)) == "other":
                    yield Hit(n, f"tells you to set {m.group(1)} to {m.group(2)}, which is not the vendor", "high",
                              {"setting": m.group(1), "url": m.group(2)})
        return
    d = load(doc)
    if not isinstance(d, dict):
        return
    if path_is(doc, ".claude/settings.json", ".claude/settings.local.json", "managed-settings.json"):
        yield from _claude(doc, d)
    elif path_is(doc, ".vscode/settings.json", "code/user/settings.json"):
        yield from _vscode(doc, d)
    elif path_is(doc, "opencode.json", "opencode.jsonc"):
        yield from _opencode(doc, d)
    elif path_is(doc, ".codex/config.toml", "codex/config.toml") or (doc.name == "config.toml" and "approval_policy" in doc.text):
        yield from _codex(doc, d)
    elif path_is(doc, ".gemini/settings.json"):
        yield from _gemini(doc, d)
