"""Install-time gate: a pre-tool hook that runs `check` before an agent installs a skill, plugin or MCP server.

The watcher sees a file after it lands, and an agent may load it before the scan finishes; the hook is
the real control. Formats verified 2026-10-18 (docs/verified/phase3.md):

  * Claude Code: PreToolUse in ~/.claude/settings.json. stdin JSON has tool_name and tool_input; exit 2
    with a reason on stderr blocks the call. Installs arrive as Bash (`claude mcp add`, `npx skills add`)
    or as Edit/Write on an MCP config file. `/plugin install` typed by you is not a tool call, so no
    hook can see it.
  * Codex CLI: the same PreToolUse schema in ~/.codex/hooks.json.
  * Cursor: beforeShellExecution in ~/.cursor/hooks.json; stdout {"permission": "deny"} blocks.

When the hook cannot check something it denies the call and says why (fail closed). Set
UNPICK_HOOK_FAIL_OPEN=1 to let unverifiable installs through with a warning; a block is never overridden.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import sys
import tempfile
from pathlib import Path

from unpick.finding import SEVERITIES

COMMAND = "unpick hook run {agent}"
MARK = "unpick hook run"  # in docs and tests; matching uses MARK_RX, which also sees unpick.exe and quoted paths
MARK_RX = re.compile(r"unpick(?:\.exe)?[\"']?\s+hook\s+run\b|-m\s+unpick\s+hook\s+run\b", re.I)
CONFIG_NAMES = (".mcp.json", ".claude.json", "mcp.json", "mcp_config.json", "claude_desktop_config.json",
                "settings.json", "settings.local.json", "opencode.json", "opencode.jsonc", "config.toml", "hooks.json")

INSTALLS = [
    (re.compile(r"\bclaude\s+mcp\s+add(?:-json)?\b(?P<rest>.*)"), "mcp"),
    (re.compile(r"\bcodex\s+mcp\s+add\b(?P<rest>.*)"), "mcp"),
    (re.compile(r"\bgemini\s+(?:mcp\s+add|extensions?\s+install)\b(?P<rest>.*)"), "mcp"),
    (re.compile(r"\bcode(?:-insiders)?\s+--add-mcp\b(?P<rest>.*)"), "mcp"),
    (re.compile(r"\bclaude\s+plugin\s+(?:install|marketplace\s+add)\b(?P<rest>.*)"), "plugin"),
    (re.compile(r"\b(?:npx|pnpm\s+dlx|bunx)\s+(?:-y\s+)?skills(?:@[\w.-]+)?\s+(?:add|a|install|i|use)\b(?P<rest>.*)"), "skill"),
    (re.compile(r"\bgit\s+(?:-c\s+\S+\s+)*clone\b(?P<rest>.*(?:skills|\.claude|\.codex|\.cursor|\.opencode)\S*)"), "skill"),
]
PKG = re.compile(r"(?:^|\s)(?:npx|bunx|pnpm\s+dlx)\s+(?:-y\s+)?((?:@[\w.-]+/)?[\w.-]+(?:@[\w.+-]+)?)")
UVX = re.compile(r"(?:^|\s)uvx\s+([\w.-]+(?:==[\w.+-]+)?)")
URL = re.compile(r"https://(?:github\.com|gitlab\.com|codeberg\.org)/[\w./-]+")
GH_SHORT = re.compile(r"(?:^|\s)([\w.-]+/[\w.-]+)(?:@[\w.-]+)?(?=\s|$)")


# ---------------------------------------------------------------- deciding
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][\w]*)\1")
WRAPPERS = {"sudo", "env", "command", "exec", "time", "nohup", "nice", "builtin"}
SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", "|&", ";;"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}


SUBST = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")


def _strip_heredocs(script: str) -> str:
    """Drop heredoc bodies: their text is data handed to a program, not commands the shell runs.

    A quoted delimiter (<<'EOF') makes the whole body plain text. An unquoted one (<<EOF) still runs its
    $(...) and backtick substitutions, so those are kept as commands of their own."""
    out, lines, i = [], script.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        docs = [(m.group(2), bool(m.group(1))) for m in HEREDOC.finditer(line)]
        i += 1
        for end, quoted in docs:
            while i < len(lines) and lines[i].strip() != end:
                if not quoted:
                    out.extend(a or b for a, b in SUBST.findall(lines[i]))
                i += 1
            i += 1  # the terminator line
    return "\n".join(out)


def commands(script: str) -> list[list[str]] | None:
    """Split a shell script into simple commands (lists of words). Quoted text stays one word, heredoc
    bodies are skipped, and `sh -c '...'` is opened up. None when the script cannot be parsed."""
    try:
        lex = shlex.shlex(_strip_heredocs(script).replace("\n", " ; "), posix=True, punctuation_chars=";&|()")
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return None
    out, cur = [], []
    for t in tokens + [";"]:
        if t in SEPARATORS:
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(t)
    expanded = []
    for words in out:
        while words and (words[0] in WRAPPERS or re.fullmatch(r"[A-Za-z_]\w*=.*", words[0])):
            words = words[1:]  # sudo, env FOO=bar, plain assignments
        if len(words) >= 3 and Path(words[0]).name in SHELLS and words[1] == "-c":
            expanded.extend(commands(words[2]) or [words])
        elif words and words[0] == "eval":
            expanded.extend(commands(" ".join(words[1:])) or [words])
        elif words:
            expanded.append(words)
    return expanded


def targets(command: str) -> list[str]:
    """What an install command would fetch, as `check` refs. Empty if this is not an install.

    Matching runs on each real shell command, so install text inside a heredoc, a quoted string or a
    comment is not mistaken for an install. If the script cannot be parsed, the whole text is matched,
    which errs toward checking (and blocking) rather than letting something through."""
    parsed = commands(command)
    if parsed is None:
        return _targets_in(command, anchored=False)
    out = []
    for words in parsed:
        out.extend(_targets_in(" ".join(words), anchored=True))
    return out


def _targets_in(command: str, anchored: bool) -> list[str]:
    out = []
    for rx, kind in INSTALLS:
        m = rx.match(command) if anchored else rx.search(command)
        if not m:
            continue
        rest = m.group("rest")
        if (u := URL.search(rest)):
            out.append(u.group(0).rstrip("/"))
        elif kind == "mcp" and (p := PKG.search(rest)):
            out.append("npm:" + p.group(1))
        elif kind == "mcp" and (p := UVX.search(rest)):
            out.append("pypi:" + p.group(1))
        elif kind == "skill" and (g := GH_SHORT.search(rest)):
            out.append(f"https://github.com/{g.group(1)}")
        else:
            out.append(f"unverifiable:{kind}:{rest.strip()[:80]}")
    return out


def _is_config(path: str) -> bool:
    return Path(path).name in CONFIG_NAMES


def decide(event: dict, min_severity: str = "high", runner=None) -> tuple[bool, str]:
    """(allowed, message). `runner(ref) -> meta` defaults to unpick.check.run."""
    tool = event.get("tool_name") or ""
    ti = event.get("tool_input") or {}
    if tool in ("Bash", "PowerShell", "shell", "beforeShellExecution") or "command" in ti:
        refs = targets(str(ti.get("command") or event.get("command") or ""))
        if not refs:
            return True, ""
        return _check_refs(refs, min_severity, runner)
    if tool in ("Edit", "Write", "MultiEdit") and _is_config(str(ti.get("file_path", ""))):
        return _check_edit(ti, min_severity)
    return True, ""


def _too_severe(findings: list[dict], min_severity: str) -> list[dict]:
    floor = SEVERITIES.index(min_severity)
    return [f for f in findings if SEVERITIES.index(f["severity"]) >= floor and f.get("decision") != "accept"]


def _summary(findings: list[dict]) -> str:
    return "; ".join(f"{f['severity']} {f['rule_id']} {f['path']}:{f['line']} {f['message'][:80]}" for f in findings[:5])


def _check_refs(refs, min_severity, runner):
    from unpick import check, quarantine

    runner = runner or (lambda ref: check.run(ref))
    for ref in refs:
        if ref.startswith("unverifiable:"):
            return _unverifiable(f"unpick cannot tell what this install fetches ({ref.split(':', 2)[2]})")
        try:
            meta = runner(ref)
        except (quarantine.Refused, OSError) as e:
            return _unverifiable(f"unpick could not check {ref}: {e}")
        bad = _too_severe(meta["scan"]["findings"], min_severity)
        if bad:
            return False, (f"unpick blocked installing {ref}: {len(bad)} unaccepted finding(s) at {min_severity} or above. "
                           f"{_summary(bad)}. Review: unpick check {ref}  (quarantine id {meta['id']})")
    return True, f"unpick checked {', '.join(refs)}: nothing at {min_severity} or above"


def _check_edit(ti, min_severity):
    from unpick import scan

    path = Path(str(ti.get("file_path")))
    if "content" in ti:
        new = str(ti["content"])
    else:
        old = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        new = old
        for e in ti.get("edits") or [ti]:
            new = new.replace(str(e.get("old_string", "")), str(e.get("new_string", "")), 1)
    with tempfile.TemporaryDirectory() as d:
        mirror = Path(d) / Path(*path.parts[-2:]) if len(path.parts) >= 2 else Path(d) / path.name
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(new, encoding="utf-8")
        res = scan.scan(Path(d), decision_files=None)
    bad = _too_severe([f.to_dict() for f in res.findings], min_severity)
    if bad:
        return False, f"unpick blocked this edit to {path.name}: {_summary(bad)}"
    return True, ""


def _unverifiable(msg: str) -> tuple[bool, str]:
    if os.environ.get("UNPICK_HOOK_FAIL_OPEN") == "1":
        return True, f"warning: {msg} (allowed because UNPICK_HOOK_FAIL_OPEN=1)"
    return False, f"{msg}. Check it yourself with `unpick check`, or set UNPICK_HOOK_FAIL_OPEN=1 to allow unverified installs."


# ---------------------------------------------------------------- the hook process
def run(agent: str, stdin=None, stdout=None, stderr=None, min_severity: str | None = None) -> int:
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    try:
        event = json.loads(stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0  # not ours to judge; never break the agent on malformed input
    sev = min_severity or os.environ.get("UNPICK_HOOK_MIN_SEVERITY", "high")
    if agent == "cursor" and "command" in event and "tool_name" not in event:
        event = {"tool_name": "beforeShellExecution", "tool_input": {"command": event["command"]}}
    allowed, msg = decide(event, sev)
    if agent == "cursor":
        stdout.write(json.dumps({"permission": "allow" if allowed else "deny", "user_message": msg, "agent_message": msg}))
        return 0
    if not allowed:
        stderr.write(msg + "\n")
        return 2
    return 0


# ---------------------------------------------------------------- install / uninstall
def settings_path(agent: str) -> Path:
    home = Path.home()
    return {"claude-code": home / ".claude" / "settings.json", "codex": home / ".codex" / "hooks.json",
            "cursor": home / ".cursor" / "hooks.json"}[agent]


def _ours(entry) -> bool:
    return bool(MARK_RX.search(json.dumps(entry).replace("\\\\", "/")))


def _quote(path: str) -> str:
    """Quote a program path for the shell the agent runs hooks in: POSIX quoting, or Windows double quotes."""
    if os.name == "nt":
        return f'"{path}"' if " " in path else path
    return shlex.quote(path)


def _exe() -> str:
    found = shutil.which("unpick")
    return _quote(found) if found else f"{_quote(sys.executable)} -m unpick"


def _entry(agent: str) -> dict:
    cmd = COMMAND.format(agent=agent).replace("unpick", _exe(), 1)
    if agent == "cursor":
        return {"command": cmd}
    return {"matcher": "Bash|PowerShell|Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": cmd, "timeout": 300}]}


def planned(agent: str, install: bool) -> tuple[Path, dict, dict]:
    path = settings_path(agent)
    before = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    after = json.loads(json.dumps(before))
    if agent == "cursor":
        after.setdefault("version", 1)
        hooks = after.setdefault("hooks", {}).setdefault("beforeShellExecution", [])
        hooks[:] = [h for h in hooks if not _ours(h)]
    else:
        hooks = after.setdefault("hooks", {}).setdefault("PreToolUse", [])
        hooks[:] = [h for h in hooks if not _ours(h)]
    if install:
        hooks.append(_entry(agent))
    if not hooks:
        key = "beforeShellExecution" if agent == "cursor" else "PreToolUse"
        after["hooks"].pop(key, None)
        if not after["hooks"]:
            after.pop("hooks")
            if agent == "cursor":
                after.pop("version", None)  # only describes the hooks block, which is now gone
    return path, before, after


def apply(agent: str, install: bool, dry_run: bool) -> dict:
    import difflib
    from datetime import UTC, datetime

    path, before, after = planned(agent, install)
    diff = "".join(difflib.unified_diff(json.dumps(before, indent=2).splitlines(True), json.dumps(after, indent=2).splitlines(True),
                                        str(path), str(path) + " (after)"))
    if dry_run or before == after:
        return {"path": str(path), "changed": before != after, "dry_run": dry_run, "diff": diff}
    if path.is_file():
        backup = path.with_name(path.name + f".unpick-backup-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}")
        shutil.copy2(path, backup)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path), "changed": True, "dry_run": False, "diff": diff}
