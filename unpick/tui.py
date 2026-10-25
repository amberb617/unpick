"""Home screen: what `unpick` with no arguments opens in a terminal. Needs the `tui` extra (Textual).

One look answers three questions: are my agents protected, what is installed and does any of it need a look,
and has the watcher flagged anything. Every action hands the terminal to the same CLI command you could type
(setup, check, scan), then comes back. Nothing here touches the network; only `check` does, when you ask.

Scan results are grouped by place (a skill folder, or a config file that can hold several MCP servers or
hooks), because a finding in a shared config file cannot be pinned on one of the servers in it.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from rich.text import Text

from unpick import hook, setup, watch

BUCKETS = ("high", "medium", "low", "nothing found", "not read")
COLOR = {"high": "#ff4e4e", "medium": "#ffc000", "low": "#c9d6f0", "nothing found": "#5a935a", "not read": "#aa9ff3"}
SEVERITY_RX = re.compile(r"--min-severity\s+(\w+)")
LOGO = """\
██╗   ██╗███╗   ██╗██████╗ ██╗ ██████╗██╗  ██╗
██║   ██║████╗  ██║██╔══██╗██║██╔════╝██║ ██╔╝
██║   ██║██╔██╗ ██║██████╔╝██║██║     █████╔╝
██║   ██║██║╚██╗██║██╔═══╝ ██║██║     ██╔═██╗
╚██████╔╝██║ ╚████║██║     ██║╚██████╗██║  ██╗
 ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝╚═╝  ╚═╝
"""
LOGO_COLORS = ("#ff97bf", "#f99ac6", "#e99fd6", "#d3a1e6", "#bea0ef", "#aa9ff3")  # pink to lavender, top to bottom


# ---------------------------------------------------------------- what the screen shows (no Textual needed)
def protection() -> list[dict]:
    rows = []
    for agent, (label, folder) in setup.AGENTS.items():
        path = hook.settings_path(agent)
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        except (OSError, json.JSONDecodeError):
            data = {}
        cmds = [s for s in hook._strings(data) if hook.MARK_RX.search(s)]
        level = SEVERITY_RX.search(cmds[0]) if cmds else None
        rows.append({"agent": agent, "label": label, "installed": (Path.home() / folder).is_dir(), "hooked": bool(cmds),
                     "level": level.group(1) if level else os.environ.get("UNPICK_HOOK_MIN_SEVERITY", "high"),
                     "fail_open": any("--fail-open" in c for c in cmds)})
    return rows


def watcher() -> bool | None:
    """True if the run-at-login watcher is set up, False if not, None where unpick cannot tell (Windows)."""
    f = setup.service_file(setup.service_kind())
    return f.is_file() if f else None


def alerts(limit: int = 4) -> list[dict]:
    try:
        lines = watch.LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("open"):
            out.append(e)
        if len(out) == limit:
            break
    return out


def places(items: list[dict]) -> list[Path]:
    return sorted({Path(i["path"]) for i in items if Path(i["path"]).exists()})


def bucket(result) -> str:
    """Worst open finding at this place. A place that could not be read is never shown as clean."""
    if result.exit_code == 2:
        return "not read"
    for sev in ("high", "medium", "low"):
        if any(f.severity == sev for f in result.findings):
            return sev
    return "nothing found"


def bars(counts: dict, width: int = 24) -> Text:
    top = max(counts.values(), default=0) or 1
    t = Text()
    for b in BUCKETS:
        n = counts.get(b, 0)
        t.append(f"{b:<14}", style="#95adda")
        t.append("█" * max(round(width * n / top), 1 if n else 0), style=COLOR[b])
        t.append(f" {n}\n", style="bold")
    return t


def next_steps(rows: list[dict]) -> list[str]:
    steps = []
    if not any(r["hooked"] for r in rows if r["installed"]):
        steps.append("Press s to protect your agents. It shows every change before making it.")
    steps.append("Press c to check a skill, MCP server or plugin before you install it.")
    steps.append("Press i to see every add-on on this machine, worst first.")
    return steps


# ---------------------------------------------------------------- the app
def run() -> None:
    from unpick.tui_app import Home

    Home().run()
