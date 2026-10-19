"""Autorun: project files that run code the moment you open the folder or start an agent session.

The Shai-Hulud "CHAINDROP" npm worm (2026-08-04) commits two files into the repositories it reaches: a
`.claude/settings.json` with a SessionStart hook running `node .claude/setup.mjs`, and a `.vscode/tasks.json`
task that runs on folder open. Cloning the repo is harmless; opening it in the editor or the agent is not.
https://blog.gitguardian.com/keyv-mini-shai-hulud/ ; the tensorlake compromise (2026-10-08) did the same,
https://socket.dev/blog/tensorlake-compromise . Claude Code CVE-2026-40068 ran project hooks before the
trust prompt: https://advisories.gitlab.com/npm/@anthropic-ai/claude-code/CVE-2026-40068/
"""

from __future__ import annotations

from unpick.checks import Hit
from unpick.checks._config import DOWNLOAD, REPO_SCRIPT, dig, line_of, load, path_is

RULE_ID = "RT-AUTORUN"
TITLE = "Runs code on open"
SEVERITY = "high"
WHY = "This project file makes your editor or agent run a command as soon as the folder is opened or a session starts, before you have read anything."
FALSE_POSITIVE = "Teams do commit formatter or test hooks on purpose; check that the command is one you recognise and that the script it runs is in the commit you reviewed."

EARLY_EVENTS = {"SessionStart", "UserPromptSubmit", "Setup", "InstructionsLoaded"}
HOOK_FILES = (".claude/settings.json", ".claude/settings.local.json", ".cursor/hooks.json", ".codex/hooks.json",
              ".gemini/settings.json", "hooks/hooks.json")


def applies(doc):
    return path_is(doc, *HOOK_FILES, ".vscode/tasks.json")


def _commands(group) -> list[str]:
    if isinstance(group, dict):
        cmds = [group["command"]] if isinstance(group.get("command"), str) else []
        for h in group.get("hooks", []) if isinstance(group.get("hooks"), list) else []:
            cmds += _commands(h)
        return cmds
    if isinstance(group, list):
        return [c for g in group for c in _commands(g)]
    return []


def _hooks(doc, data):
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return
    for event, groups in hooks.items():
        for cmd in _commands(groups):
            early = event in EARLY_EVENTS
            local = bool(REPO_SCRIPT.search(cmd))
            fetch = bool(DOWNLOAD.search(cmd))
            if not (early or local or fetch or "permissionDecision" in cmd):
                continue
            sev = "high" if (early and (local or fetch)) or fetch or "permissionDecision" in cmd else "medium"
            what = "runs a command"
            if local:
                what = "runs a script from this repository"
            elif fetch:
                what = "downloads"
            yield Hit(line_of(doc, cmd[:40]), f"{event} hook {what}: {cmd[:120]}", sev, {"event": event, "command": cmd})


def _tasks(doc, data):
    for task in (data.get("tasks") or []) if isinstance(data, dict) else []:
        if isinstance(task, dict) and dig(task, "runOptions", "runOn") == "folderOpen":
            cmd = " ".join(str(x) for x in [task.get("command", ""), *task.get("args", [])])
            yield Hit(line_of(doc, "folderOpen"), f"VS Code task runs on folder open: {cmd[:120]}", "high",
                      {"task": task.get("label"), "command": cmd})


def run(doc):
    data = load(doc)
    if data is None:
        return
    if path_is(doc, ".vscode/tasks.json"):
        yield from _tasks(doc, data)
    else:
        yield from _hooks(doc, data)
