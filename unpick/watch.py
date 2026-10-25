"""`unpick watch`: scan anything new or changed in the AI component folders as it lands.

This is a backstop, not a control. It sees a file after it is written, and an agent can load it before
the scan finishes; the install hook (`unpick hook install`) is what stops an install. The watcher posts a
desktop notification and appends to ~/.unpick/watch.log. With --quarantine high (opt-in) it also moves an
add-on with a serious warning out of the agent's folder at once, like antivirus quarantine; `unpick restore`
undoes it. Needs the `watch` extra (watchdog). Recipes to
run it at login: `unpick watch --print-service launchd|systemd|windows` (verified in docs/verified/phase3.md).
"""

from __future__ import annotations

import json
import platform
import shlex
import shutil
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from unpick import inventory, scan
from unpick.resources import load_json

LOG = Path.home() / ".unpick" / "watch.log"
DEBOUNCE = 2.0  # seconds: an install writes many files; scan once it settles


def watch_plan(project: Path) -> tuple[list[Path], list[Path]]:
    """(folders watched recursively, folders watched for their direct children only).

    Component folders (skills, plugins, rules directories) are watched recursively. A config file that
    (~/.claude.json, ~/.codex/config.toml, .mcp.json) is covered by watching its folder non-recursively,
    so unpick never watches your whole home tree or an agent's session logs."""
    deep, shallow = set(), set()
    for loc in load_json("locations.json"):
        if inventory.current_os() not in loc.get("os", []):
            continue
        for p in inventory.expand(loc["path"].split("*")[0].rstrip("/\\") or ".", project):
            if p.is_dir() and loc.get("format") == "dir":
                deep.add(p.resolve())
            elif p.parent.is_dir():
                shallow.add(p.parent.resolve())  # a config file: watch its folder, not the tree under it
    keep = sorted(deep, key=lambda p: len(p.parts))
    deep_roots = [p for i, p in enumerate(keep) if not any(p.is_relative_to(q) for q in keep[:i])]
    return deep_roots, sorted(s for s in shallow if s not in deep_roots)


def roots(project: Path) -> list[Path]:
    deep, shallow = watch_plan(project)
    return deep + shallow


def notify(title: str, body: str) -> None:
    """Desktop notification with no extra dependencies. Failures are ignored; the log is the record."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["osascript", "-e", f"display notification {json.dumps(body)} with title {json.dumps(title)}"],
                           timeout=5, capture_output=True)
        elif system == "Linux" and shutil.which("notify-send"):
            subprocess.run(["notify-send", title, body], timeout=5, capture_output=True)
        elif system == "Windows":
            ps = ("Add-Type -AssemblyName System.Windows.Forms; $n = New-Object System.Windows.Forms.NotifyIcon; "
                  "$n.Icon = [System.Drawing.SystemIcons]::Warning; $n.Visible = $true; "
                  f"$n.ShowBalloonTip(10000, {json.dumps(title)}, {json.dumps(body)}, 'Warning'); Start-Sleep 10; $n.Dispose()")
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        pass


def log(entry: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": datetime.now(UTC).isoformat(timespec="seconds"), **entry}, ensure_ascii=True) + "\n")


def component_root(path: Path, watched: list[Path]) -> Path:
    """The folder to scan for a changed file: its first-level folder under the watched root (a skill or plugin)."""
    for r in watched:
        if path.is_relative_to(r):
            rel = path.relative_to(r).parts
            return r / rel[0] if len(rel) > 1 else path
    return path


def _fingerprint(p: Path) -> tuple:
    files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file())
    return tuple((str(f), f.stat().st_ino, f.stat().st_mtime_ns, f.stat().st_size) for f in files[:2000])


def _changed_since(p: Path, before: tuple) -> bool:
    return _fingerprint(p) != before


def owning_component(changed: Path) -> Path | None:
    """The deepest inventoried skill or plugin folder that contains the changed path, or None.

    Config files and shared caches are never quarantined whole: one bad entry must not take ~/.claude.json
    or a whole marketplace cache away from the agent."""
    hits = []
    for c in inventory.discover(project=Path.cwd()):
        p, _, entry = c["path"].partition("#")
        if entry or c["kind"] not in ("skill", "plugin", "extension"):
            continue
        root = Path(p)
        if root.is_dir() and not root.is_symlink() and (changed == root or changed.is_relative_to(root)):
            hits.append(root)
    return max(hits, key=lambda r: len(r.parts)) if hits else None


def scan_and_report(target: Path, quarantine_at: str | None = None) -> dict:
    """Scan what landed; with quarantine_at ("high" or "medium"), move it out of the agent's reach at that severity."""
    from unpick import isolate
    from unpick.finding import SEVERITIES
    if not target.exists():
        return {"path": str(target), "status": "removed"}
    owner = owning_component(target) if quarantine_at else None
    before = _fingerprint(owner or target)  # what gets moved is the owner, so that is what must not change meanwhile
    res = scan.scan(target)
    high = [f for f in res.findings if f.severity == "high"]
    entry = {"path": str(target), "open": len(res.findings), "high": len(high),
             "top": [f"{f.rule_id} {f.path}:{f.line}" for f in res.findings[:3]]}
    if quarantine_at:
        floor = SEVERITIES.index(quarantine_at)
        if any(SEVERITIES.index(f.severity) >= floor for f in res.findings):
            if owner is None:
                entry["quarantine_skipped"] = "not a whole add-on folder (a config file or a shared cache); review it with unpick recover"
            elif _changed_since(owner, before):
                entry["quarantine_skipped"] = "it changed while it was being scanned; it will be scanned again"
            else:
                try:
                    r = isolate.isolate({"path": str(owner), "name": owner.name}, reason=f"watch: {entry['top'][0]}")
                    entry["quarantined"] = r["id"]
                except isolate.CannotIsolate as e:
                    entry["quarantine_error"] = str(e)
    log(entry)
    if entry.get("quarantined"):
        notify("unpick moved an AI add-on to quarantine",
               f"{target.name}: {len(high)} serious warning(s). Undo with: unpick restore {entry['quarantined']}")
    elif res.findings:
        notify("unpick: new AI component needs a look",
               f"{target.name}: {len(res.findings)} finding(s), {len(high)} high. Run: unpick scan {target}")
    return entry


def run(project: Path, once: bool = False, quarantine_at: str | None = None) -> None:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError as e:
        raise SystemExit("unpick watch needs the watch extra: pipx install 'unpick[watch]'") from e
    deep, shallow = watch_plan(project)
    watched = deep + shallow
    pending: dict[Path, float] = {}
    lock = threading.Lock()

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            if event.is_directory and event.event_type == "modified":
                return
            p = Path(event.src_path)
            if any(part in scan.SKIP_DIRS for part in p.parts) or p.name.endswith((".swp", "~", ".tmp")):
                return
            with lock:
                pending[component_root(p, watched)] = time.monotonic()

    obs = Observer()
    for r in deep:
        obs.schedule(Handler(), str(r), recursive=True)
    for r in shallow:
        obs.schedule(Handler(), str(r), recursive=False)
    obs.start()
    print(f"unpick watch: {len(watched)} folder(s), log {LOG}. This is a backstop; the install hook is the control.", flush=True)
    try:
        while True:
            time.sleep(0.5)
            now = time.monotonic()
            with lock:
                ready = [p for p, t in pending.items() if now - t >= DEBOUNCE]
                for p in ready:
                    pending.pop(p)
            for p in ready:
                scan_and_report(p, quarantine_at)
            if once and ready:
                break
    except KeyboardInterrupt:
        pass
    finally:
        obs.stop()
        obs.join()


def command(quarantine_at: str | None = None) -> list[str]:
    exe = shutil.which("unpick")
    argv = [exe] if exe else [sys.executable, "-m", "unpick"]  # never split: a home folder can have a space in it
    return argv + ["watch"] + (["--quarantine", quarantine_at] if quarantine_at else [])


def windows_command(argv: list[str]) -> str:
    return " ".join(f'"{a}"' if " " in a else a for a in argv)


def service(kind: str, quarantine_at: str | None = None) -> str:
    argv = command(quarantine_at)
    if kind == "launchd":
        args = "".join(f"\n    <string>{a}</string>" for a in argv)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<!-- Save as ~/Library/LaunchAgents/dev.unpick.watch.plist, then:
     launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/dev.unpick.watch.plist -->
<plist version="1.0">
<dict>
  <key>Label</key><string>dev.unpick.watch</string>
  <key>ProgramArguments</key>
  <array>{args}
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>/tmp/unpick-watch.err</string>
</dict>
</plist>
"""
    if kind == "systemd":
        return f"""# Save as ~/.config/systemd/user/unpick-watch.service, then:
#   systemctl --user daemon-reload && systemctl --user enable --now unpick-watch
[Unit]
Description=unpick watch: scan new AI components as they land

[Service]
ExecStart={shlex.join(argv)}
Restart=on-failure

[Install]
WantedBy=default.target
"""
    if kind == "windows":
        cmd = windows_command(argv)
        return f"""# PowerShell (5.1 or 7). Runs at logon for the current user. /TR is limited to 262 characters.
schtasks /Create /SC ONLOGON /TN "unpick watch" /TR '{cmd}' /F
# Remove with: schtasks /Delete /TN "unpick watch" /F
"""
    raise ValueError("kind must be launchd, systemd or windows")
