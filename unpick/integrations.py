"""Scanning integrations: what is set up, and how to set up the rest. unpick stores no secret for any of them.

* Jiffy (commercial, network; see backends/jiffy.py). The `jiffy` CLI keeps its own login: a token in a
  per-user config file (0600 on POSIX) or $JIFFY_TOKEN. `connect_jiffy` hands a pasted key to `jiffy login`
  through the environment, so it never shows in a process listing or shell history, and the CLI validates it
  before saving. The status reads that file and makes no network call, so it can only say a key is saved,
  not that it still works; `check_jiffy` asks Jiffy, and only when you run it.
* Scanner backends: installed or not (backends.describe), installed with `unpick backends install`.
* AI review over a provider API (judges/api.py): reads a key from your environment. unpick only reports whether
  it is set; storing it is your shell's job.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path

from unpick import backends
from unpick.judges.api import PROVIDERS

JIFFY_PACKAGE = "@jiffylabs/jiffy-cli"
JIFFY_KEYS_URL = "https://app.jiffylabs.ai/settings/api-keys"
JIFFY_DEFAULT_SERVER = "https://app.jiffylabs.ai"  # jiffy-cli DEFAULT_API_URL


def jiffy_config() -> Path:
    """Where the jiffy CLI saves its login (jiffy-cli README, Configuration)."""
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "jiffy" / "config.json"
    if system == "Darwin":
        return Path.home() / "Library" / "Preferences" / "jiffy" / "config.json"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "jiffy" / "config.json"


def jiffy_status() -> dict:
    try:
        cfg = json.loads(jiffy_config().read_text(encoding="utf-8"))
        cfg = cfg if isinstance(cfg, dict) else {}
    except (OSError, json.JSONDecodeError):
        cfg = {}
    if os.environ.get("JIFFY_TOKEN"):
        how = "$JIFFY_TOKEN"
    else:
        how = "saved login" if cfg.get("token") else None
    server = (os.environ.get("JIFFY_API_URL") or cfg.get("apiUrl") or JIFFY_DEFAULT_SERVER).rstrip("/")
    return {"cli": backends.which("jiffy") is not None, "connected": how is not None, "how": how, "server": server}


def check_jiffy(runner=subprocess.run) -> tuple[int, str]:
    """Ask Jiffy whether the saved key works (network: `jiffy whoami`)."""
    if backends.which("jiffy") is None:
        return 2, f"The Jiffy CLI is not installed. Install it with: npm install -g {JIFFY_PACKAGE}"
    p = runner(["jiffy", "whoami"], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def connect_jiffy(key: str | None, runner=subprocess.run) -> tuple[int, str]:
    """Sign the jiffy CLI in: with a pasted key, or (key=None) the browser device flow, which needs the terminal."""
    if backends.which("jiffy") is None:
        return 2, f"The Jiffy CLI is not installed. Install it with: npm install -g {JIFFY_PACKAGE}"
    if key is None:
        return runner(["jiffy", "login"]).returncode, ""
    p = runner(["jiffy", "login"], env={**os.environ, "JIFFY_TOKEN": key.strip()}, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def disconnect_jiffy(runner=subprocess.run) -> tuple[int, str]:
    if backends.which("jiffy") is None:
        return 2, "The Jiffy CLI is not installed, so there is no saved login to remove."
    p = runner(["jiffy", "logout"], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def rows() -> list[dict]:
    """One row per integration: what it is, whether it is ready, and the unpick command that sets it up."""
    out = []
    j = jiffy_status()
    if not j["cli"]:
        status = "Jiffy CLI not installed"
    elif j["connected"]:
        status = ("key from $JIFFY_TOKEN" if j["how"] == "$JIFFY_TOKEN" else "key saved in the Jiffy CLI") + ", not checked"
    else:
        status = "no key saved"
    if j["server"] != JIFFY_DEFAULT_SERVER:
        status += f"; server {j['server']}"
    out.append({"id": "jiffy", "name": "Jiffy", "kind": "scanner, account", "ready": j["connected"] and j["cli"],
                "status": status, "network": backends.adapters()["jiffy"].NETWORK,
                "action": ["integrations", "connect", "jiffy"]})  # also how you replace a key
    for b in backends.describe(cached=True):
        if b["name"] == "jiffy":
            continue
        installed = f"installed {b['version'] or ''}".strip()
        can_install = backends.adapters()[b["name"]].INSTALL is not None
        out.append({"id": b["name"], "name": b["name"], "kind": "scanner", "ready": b["installed"],
                    "status": installed if b["installed"] else "not installed", "network": b["network"],
                    "action": None if b["installed"] or not can_install else ["backends", "install", b["name"], "--online"]})
    for name, p in PROVIDERS.items():
        is_set = bool(os.environ.get(p["env"]))
        out.append({"id": f"api:{name}", "name": p["label"], "kind": "AI review, hosted", "ready": is_set,
                    "status": f"${p['env']} is set" if is_set else f"set ${p['env']} in your shell to use it",
                    "network": f"{p['label']}: the full text of each scanned file, only with --judge api:{name}",
                    "action": None})
    return out


def online_backends(found: list[dict] | None = None) -> list[str]:
    """Every ready scanner, for a scan you have allowed onto the network (--online)."""
    return [r["id"] for r in (rows() if found is None else found) if r["kind"].startswith("scanner") and r["ready"]]
