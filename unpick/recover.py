"""`unpick recover <component | --all> [--since <datetime>]`: when it got through.

Assume the worst and act in order:
  1. Contain: move the component into ~/.unpick/quarantine/incident-<ts>/, remove its entries from agent
     configs (each edited file is backed up first), and list running processes started from it.
  2. What could it reach: credentials and private files reachable from the agent's environment, as a
     rotation checklist grouped by provider with the official rotation page (data/rotation.json).
  3. What did the agent do: the flight recorder plus the agents' own session logs for the window.
  4. What changed on disk: `verify` against the last lockfile, plus files modified since --since.
  5. Egress going forward: free tools that log outbound connections.
  6. Report: a plain-language incident summary to hand to someone more technical, and where to report
     the component.

Secret values are never printed or written: names and locations only. If a credential stealer ran,
rotation is not optional, and nothing here can undo what was already sent. Containment only happens with
--yes; without it, recover prints exactly what it would move and edit.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from unpick import inventory, lock
from unpick.resources import load_json

INCIDENTS = Path.home() / ".unpick" / "quarantine"
SECRET_ENV = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|ACCESS_KEY|PRIVATE_KEY|CREDENTIAL|SESSION|AUTH)", re.I)
HOME_CANDIDATES = [
    "~/.ssh", "~/.aws/credentials", "~/.aws/config", "~/.config/gcloud", "~/.azure", "~/.npmrc", "~/.pypirc",
    "~/.netrc", "~/.git-credentials", "~/.config/gh/hosts.yml", "~/.docker/config.json", "~/.kube/config",
    "~/.cargo/credentials.toml", "~/.config/hub", "~/.huggingface/token", "~/.cache/huggingface/token",
    "~/Library/Keychains", "~/Library/Application Support/Google/Chrome", "~/Library/Application Support/Firefox",
    "~/Library/Application Support/BraveSoftware", "~/Library/Safari", "~/.config/google-chrome", "~/.mozilla/firefox",
    "~/.config/BraveSoftware", "%LOCALAPPDATA%/Google/Chrome/User Data", "%APPDATA%/Mozilla/Firefox",
    "%LOCALAPPDATA%/Microsoft/Edge/User Data", "~/Library/Application Support/Exodus", "~/.electrum",
    "~/Library/Application Support/Claude/claude_desktop_config.json", "~/.claude.json", "~/.codex/auth.json",
    "~/.gemini/oauth_creds.json",
]


def now_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------- 1. contain
def find_component(query: str, project: Path) -> list[dict]:
    p = Path(query).expanduser()
    items = inventory.discover(project=project)
    if p.exists():
        rp = str(p.resolve())
        return [c for c in items if c["path"].partition("#")[0] == rp] or [{"kind": "path", "name": p.name, "path": rp, "host": "-"}]
    return [c for c in items if c["name"] == query]


def _processes() -> list[tuple[int, str]]:
    try:
        if platform.system() == "Windows":
            ps = ("Get-CimInstance Win32_Process | ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }")
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=30).stdout
            rows = [line.split("\t", 1) for line in out.splitlines() if "\t" in line]
        else:
            out = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, timeout=30).stdout
            rows = [line.strip().split(None, 1) for line in out.splitlines() if line.strip()]
        return [(int(r[0]), r[1]) for r in rows if len(r) == 2 and r[0].isdigit()]
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return []


def running_from(c: dict) -> list[dict]:
    needles = [c["path"].partition("#")[0]] if c.get("kind") != "mcp-server" else []
    if c.get("provenance"):
        needles += [w for w in str(c["provenance"]).split() if len(w) > 6 and not w.startswith("-")][:3]
    me = os.getpid()
    return [{"pid": pid, "command": cmd[:200]} for pid, cmd in _processes()
            if pid != me and any(n and n in cmd for n in needles)]


def containment_plan(c: dict) -> list[dict]:
    path_s, _, entry = c["path"].partition("#")
    if entry:
        return [{"action": "remove-entry", "file": path_s, "entry": entry, "kind": c["kind"]}]
    return [{"action": "move", "from": path_s}]


def _remove_entry(cfg: Path, entry: str, kind: str) -> str:
    if cfg.suffix == ".toml":
        return f"edit {cfg} by hand and delete the [{'mcp_servers.' + entry}] table (unpick does not rewrite TOML)"
    data = inventory.load_config(cfg, "")
    removed = False
    for key in ("mcpServers", "servers", "context_servers", "mcp"):
        block = data.get(key) if isinstance(data, dict) else None
        if isinstance(block, dict) and entry in block:
            block.pop(entry)
            removed = True
    if kind == "hook" and isinstance(data.get("hooks"), dict):
        event, _, idx = entry.partition(".")
        groups = data["hooks"].get(event)
        if isinstance(groups, list) and idx.isdigit() and int(idx) < len(groups):
            groups.pop(int(idx))
            removed = True
    if not removed:
        return f"{entry} not found in {cfg}"
    backup = cfg.with_name(cfg.name + f".unpick-incident-{now_stamp()}")
    shutil.copy2(cfg, backup)
    cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return f"removed {entry} from {cfg} (backup {backup.name}; comments in the original are only in the backup)"


def contain(c: dict, incident: Path) -> list[str]:
    done = []
    for step in containment_plan(c):
        if step["action"] == "remove-entry":
            done.append(_remove_entry(Path(step["file"]), step["entry"], step["kind"]))
        else:
            src = Path(step["from"])
            if src.exists():
                dest = incident / "component" / src.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), dest)
                done.append(f"moved {src} to {dest}")
    return done


# ---------------------------------------------------------------- 2. what could it reach
def _rotation_rules() -> list[dict]:
    try:
        return load_json("rotation.json")
    except FileNotFoundError:
        return []


def reach(project: Path) -> dict:
    found_files = []
    for cand in HOME_CANDIDATES:
        for p in inventory.expand(cand, project):
            if p.exists():
                found_files.append(str(p))
    for p in sorted(project.rglob(".env*"))[:50]:
        if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts:
            found_files.append(str(p))
    env_names = sorted(k for k in os.environ if SECRET_ENV.search(k))
    checklist: dict[str, dict] = {}
    for rule in _rotation_rules():
        rx = [re.compile(m, re.I) for m in rule.get("matches", [])]
        # Rules are written with "/"; compare Windows paths in the same form.
        hits = [f for f in found_files if any(r.search(Path(f).as_posix()) for r in rx)] + \
            [e for e in env_names if any(r.search(e) for r in rx)]
        if hits:
            checklist[rule["id"]] = {**{k: rule.get(k) for k in ("provider", "what", "how", "url", "cli")}, "because": hits[:8]}
    covered = {h for v in checklist.values() for h in v["because"]}
    return {"files": found_files, "env_names": env_names, "rotate": checklist,
            "unmatched": [x for x in found_files + env_names if x not in covered]}


# ---------------------------------------------------------------- 4. what changed on disk
def _files_under(root: Path):
    if root.is_file():
        return [root]
    return root.rglob("*") if root.is_dir() else []


def changed_on_disk(project: Path, since: datetime | None) -> dict:
    out: dict = {"lockfile": None, "recent": []}
    try:
        out["lockfile"] = lock.verify(project, rescan=False)
    except FileNotFoundError as e:
        out["lockfile_error"] = str(e)
    if since:
        roots = {Path(c["path"].partition("#")[0]) for c in inventory.discover(project=project)} | {project}
        seen = set()
        for r in roots:
            for p in _files_under(r):
                if p in seen or not p.is_file() or ".git" in p.parts or "node_modules" in p.parts:
                    continue
                seen.add(p)
                mtime = datetime.fromtimestamp(p.stat().st_mtime, UTC)
                if mtime >= since:
                    out["recent"].append({"file": str(p), "modified": mtime.isoformat(timespec="seconds")})
                if len(out["recent"]) >= 500:
                    break
        out["recent"].sort(key=lambda x: x["modified"])
    return out


# ---------------------------------------------------------------- 5 and 6: egress and where to report
EGRESS = {
    "Darwin": "Install LuLu (free, Objective-See) to see and block outbound connections per program.",
    "Linux": "Install OpenSnitch (free) to see and block outbound connections per program.",
    "Windows": "Turn on Windows Firewall logging of allowed connections (admin PowerShell): "
               "Set-NetFirewallProfile -All -LogAllowed True. Windows Firewall does not block outbound traffic by default.",
}


def abuse_channel(c: dict) -> list[dict]:
    try:
        channels = load_json("abuse_channels.json")
    except FileNotFoundError:
        return []
    prov = f"{c.get('provenance') or ''} {c.get('path') or ''}".lower()
    picks = []
    for ch in channels:
        key = ch["registry"].lower()
        if (("npm" in key and ("npx" in prov or "npm" in prov)) or ("pypi" in key and ("uvx" in prov or "pypi" in prov))
                or ("github" in key and "github.com" in prov) or ("clawhub" in key and "openclaw" in prov)):
            picks.append(ch)
    return picks


# ---------------------------------------------------------------- 3. what did the agent do
URL_RX = re.compile(r"https?://[^\s'\"<>)]+")
SHELL_TOOLS = {"bash", "powershell", "exec", "shell", "run_shell_command", "run_shell", "local_shell", "terminal"}


def _sensitive():
    from unpick.checks.sensitive_paths import _patterns
    return _patterns()


def flag_events(events: list[dict], component_name: str | None) -> list[dict]:
    """Annotate each event with why it matters. Events with no reason are kept out of the report body."""
    from unpick.checks.encoded_execution import PIPES
    sens = _sensitive()
    out = []
    for e in events:
        blob = json.dumps(e.get("input") or {}, ensure_ascii=False)
        reasons = []
        if any(rx.search(blob) for rx, _ in sens):
            reasons.append("touches a credential or private file")
        if any(rx.search(blob) for rx, _ in PIPES):
            reasons.append("decodes or downloads code and runs it")
        urls = URL_RX.findall(blob)
        if urls:
            reasons.append("contacts " + ", ".join(sorted({u.split('/')[2] for u in urls if '//' in u})[:4]))
        if str(e.get("tool") or "").lower() in SHELL_TOOLS:
            reasons.append("shell command")
        if component_name and component_name.lower() in blob.lower():
            reasons.append(f"mentions {component_name}")
        if reasons:
            out.append({**e, "why": reasons})
    return out


# ---------------------------------------------------------------- orchestration and report
def run(query: str | None, project: Path, since: datetime | None, apply: bool) -> dict:
    from unpick import sessions

    components = find_component(query, project) if query else []
    incident = INCIDENTS / f"incident-{now_stamp()}"
    result: dict = {"incident": str(incident), "applied": apply, "components": components, "contain": [], "processes": []}
    for c in components:
        result["processes"] += running_from(c)
        if apply:
            incident.mkdir(parents=True, exist_ok=True)
            result["contain"] += contain(c, incident)
        else:
            result["contain"] += [f"would {s['action']}: {s.get('from') or s['entry'] + ' in ' + s['file']}" for s in containment_plan(c)]
    result["reach"] = reach(project)
    name = components[0]["name"] if components else None
    events = sessions.timeline(since)
    result["timeline"] = {"events": len(events), "flagged": flag_events(events, name)[-300:]}
    result["changed"] = changed_on_disk(project, since)
    result["egress"] = EGRESS.get(platform.system(), EGRESS["Linux"])
    result["report_to"] = [ch for c in components for ch in abuse_channel(c)]
    result["summary"] = summary(result)
    incident.mkdir(parents=True, exist_ok=True)
    (incident / f"incident-{incident.name[9:]}.md").write_text(report_md(result), encoding="utf-8")
    result["report"] = str(incident / f"incident-{incident.name[9:]}.md")
    return result


def summary(r: dict) -> str:
    names = ", ".join(c["name"] for c in r["components"]) or "no single component (whole machine)"
    rot = len(r["reach"]["rotate"])
    flagged = len(r["timeline"]["flagged"])
    lf = r["changed"].get("lockfile") or {}
    changed = len(lf.get("changed", [])) + len(lf.get("added", []))
    contained = "contained" if r["applied"] else "NOT yet contained (re-run with --yes)"
    return (f"Suspected component: {names}, {contained}. The agent environment could reach credentials for {rot} provider(s); "
            f"rotate them now if a stealer may have run. {flagged} agent action(s) in the window touched secrets, ran shell "
            f"commands, contacted hosts or mentioned the component. {changed} component(s) differ from the lockfile. "
            "unpick cannot undo anything already sent; recovery means containment, rotation and knowing what happened.")


def report_md(r: dict) -> str:
    out = ["# Incident report", "", f"Generated by unpick on {datetime.now(UTC).isoformat(timespec='seconds')}.", "",
           "## Summary", "", r["summary"], "", "## 1. Contain", ""]
    out += [f"- {x}" for x in r["contain"]] or ["- Nothing to contain (no component named)."]
    out += [f"- Running process {p['pid']}: `{p['command']}`" for p in r["processes"]]
    out += ["", "## 2. Rotate these credentials", "", "Names and locations only; no secret values are in this report.", ""]
    for _rid, v in sorted(r["reach"]["rotate"].items(), key=lambda kv: kv[1]["provider"] or ""):
        out.append(f"- [ ] **{v['provider']}**: {v['what']}. {v['how']} {v['url'] or ''}" + (f" (`{v['cli']}`)" if v.get("cli") else ""))
        out.append(f"  - because: {', '.join(v['because'])}")
    if r["reach"]["unmatched"]:
        out += ["", "Also reachable, no rotation rule matched: " + ", ".join(r["reach"]["unmatched"][:20])]
    out += ["", "## 3. What the agent did", "", f"{r['timeline']['events']} tool call(s) in the window; showing the ones that matter.", ""]
    for e in r["timeline"]["flagged"][-80:]:
        out.append(f"- {e['ts']} {e['agent']} `{e['tool']}`: {'; '.join(e['why'])}  \n  `{json.dumps(e['input'])[:200]}`")
    lf = r["changed"].get("lockfile")
    out += ["", "## 4. What changed on disk", ""]
    if lf:
        out += [f"- changed: {c['name']} ({c['path']})" for c in lf["changed"]] + [f"- added: {a['name']}" for a in lf["added"]]
        out += [f"- removed: {a['name']}" for a in lf["removed"]] or []
        if lf["ok"]:
            out.append("- Everything matches the lockfile.")
    else:
        out.append(f"- {r['changed'].get('lockfile_error', 'no lockfile')}")
    out += [f"- modified {x['modified']}: {x['file']}" for x in r["changed"]["recent"][:100]]
    out += ["", "## 5. Watch outbound connections from now on", "", r["egress"], "", "## 6. Report the component", ""]
    out += [f"- {ch['registry']}: {ch['how']} {ch['url']}" for ch in r["report_to"]] or ["- No registry identified; none published."]
    return "\n".join(out) + "\n"
