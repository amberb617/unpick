"""First-run setup: find the agents on this machine, ask what to turn on, show every change, then make it.

It strings together pieces that already exist: `unpick hook install` for each agent, and the watcher's
run-at-login recipe (`unpick watch --print-service`), which it saves and starts for you. Nothing is written
until you confirm the plan, and every settings file it touches gets a timestamped backup first.
`unpick setup --undo` removes all of it.

Only agents with a verified hook format are offered (see hook.py). Others are still covered by the watcher,
which notices what lands in their folders after the fact.
"""

from __future__ import annotations

import importlib.util
import os
import platform
import subprocess
from collections.abc import Callable
from pathlib import Path

from unpick import hook, watch

AGENTS = {"claude-code": ("Claude Code", ".claude"), "codex": ("Codex CLI", ".codex"), "cursor": ("Cursor", ".cursor")}
LABEL = "dev.unpick.watch"  # matches the label in watch.service("launchd")
UNIT = "unpick-watch"
TASK = "unpick watch"

Ask = Callable[[str, list[str], str], str]  # (question, choices, default) -> one of choices


def detected() -> list[str]:
    return [a for a, (_, folder) in AGENTS.items() if (Path.home() / folder).is_dir()]


def can_watch() -> bool:
    return importlib.util.find_spec("watchdog") is not None


def interview(ask: Ask) -> dict:
    agents = [a for a in detected() if ask(f"Check what {AGENTS[a][0]} installs, and block what looks risky?",
                                           ["y", "n"], "y") == "y"]
    severity, fail_open = "high", False
    if agents:
        severity = ask("Block at which level? high = clear attacks only, medium = also suspicious, low = nearly everything",
                       ["high", "medium", "low"], "high")
        fail_open = ask("Some installs cannot be checked (a local script, a private package). Block them or allow with a warning?",
                        ["block", "allow"], "block") == "allow"
    watching, quarantine = False, None
    if can_watch():
        watching = ask("Also scan new add-ons in the background, starting at login?", ["y", "n"], "n") == "y"
        if watching and ask("Move add-ons with high-level findings out of your agents' reach automatically? "
                            "(undo with unpick restore)", ["y", "n"], "n") == "y":
            quarantine = "high"
    return {"agents": agents, "min_severity": severity, "fail_open": fail_open, "watch": watching, "quarantine": quarantine}


# ---------------------------------------------------------------- the run-at-login service
def service_kind() -> str:
    return {"Darwin": "launchd", "Windows": "windows"}.get(platform.system(), "systemd")


def service_file(kind: str) -> Path | None:
    home = Path.home()
    return {"launchd": home / "Library" / "LaunchAgents" / f"{LABEL}.plist",
            "systemd": home / ".config" / "systemd" / "user" / f"{UNIT}.service"}.get(kind)


def start_commands(kind: str, quarantine: str | None) -> list[list[str]]:
    if kind == "launchd":
        return [["launchctl", "bootstrap", f"gui/{os.getuid()}", str(service_file(kind))]]
    if kind == "systemd":
        return [["systemctl", "--user", "daemon-reload"], ["systemctl", "--user", "enable", "--now", UNIT]]
    return [["schtasks", "/Create", "/SC", "ONLOGON", "/TN", TASK, "/TR", watch.windows_command(watch.command(quarantine)), "/F"],
            ["schtasks", "/Run", "/TN", TASK]]


def stop_commands(kind: str) -> list[list[str]]:
    if kind == "launchd":
        return [["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"]]
    if kind == "systemd":
        return [["systemctl", "--user", "disable", "--now", UNIT]]
    return [["schtasks", "/End", "/TN", TASK], ["schtasks", "/Delete", "/TN", TASK, "/F"]]


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)
    return p.returncode, (p.stderr or p.stdout).strip()


# ---------------------------------------------------------------- plan, apply, undo
def plan(choices: dict) -> dict:
    """Everything apply() would do, computed without writing anything."""
    hooks = [hook.apply(a, install=True, dry_run=True, min_severity=choices["min_severity"], fail_open=choices["fail_open"])
             for a in choices["agents"]]
    svc = None
    if choices["watch"]:
        kind = service_kind()
        f = service_file(kind)
        svc = {"kind": kind, "file": str(f) if f else None, "commands": start_commands(kind, choices["quarantine"])}
    return {"hooks": hooks, "service": svc}


def apply(choices: dict, runner=_run) -> dict:
    hooks = [hook.apply(a, install=True, dry_run=False, min_severity=choices["min_severity"], fail_open=choices["fail_open"])
             for a in choices["agents"]]
    svc = _start(choices["quarantine"], runner) if choices["watch"] else None
    return {"hooks": hooks, "service": svc}


def _start(quarantine: str | None, runner) -> dict:
    kind = service_kind()
    for cmd in stop_commands(kind):
        runner(cmd)  # a re-run replaces the old service; failing here only means none was running
    f = service_file(kind)
    if f:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(watch.service(kind, quarantine), encoding="utf-8")
    errors = []
    for cmd in start_commands(kind, quarantine):
        code, out = runner(cmd)
        if code:
            errors.append(f"{' '.join(cmd)}: {out or f'exit {code}'}")
    return {"kind": kind, "file": str(f) if f else None, "errors": errors}


def undo(runner=_run) -> dict:
    hooks = [hook.apply(a, install=False, dry_run=False) for a in AGENTS]
    kind = service_kind()
    f = service_file(kind)
    removed = False
    if (f and f.is_file()) or kind == "windows":
        for cmd in stop_commands(kind):
            removed = runner(cmd)[0] == 0 or removed
        if f and f.is_file():
            f.unlink()
            removed = True
    return {"hooks": [h for h in hooks if h["changed"]], "service_removed": removed}
