"""Quarantine and restore: move a flagged add-on out of your agent's reach, and put it back if it was a false alarm.

This is the antivirus-style step after a flag. An agent loads skills and plugins from known folders and
MCP servers from its config files, so moving the folder, or taking the entry out of the config, stops the
agent from using it. Nothing is deleted: each quarantined item keeps its files (or the config entry) and a
note of where it came from, so `unpick restore <id>` can undo it exactly. `recover` uses the same code.

Every edited config file is backed up first. TOML configs (Codex) are not rewritten, because Python's
standard library cannot write TOML; for those the exact manual edit is printed instead.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from unpick import inventory

ROOT = Path.home() / ".unpick" / "quarantine"
META = "isolated.json"
CONFIG_KEYS = ("mcpServers", "servers", "context_servers", "mcp")


class CannotIsolate(RuntimeError):
    pass


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _new_dir(name: str) -> Path:
    safe = re.sub(r"[^\w.-]+", "-", name)[:60] or "item"
    d = ROOT / f"isolated-{_stamp()}-{safe}"
    d.mkdir(parents=True, exist_ok=False)
    return d


def _backup(cfg: Path) -> Path:
    b = cfg.with_name(cfg.name + f".unpick-backup-{_stamp()}")
    shutil.copy2(cfg, b)
    return b


def _pop_entry(cfg: Path, entry: str, kind: str) -> tuple[dict | None, str | None]:
    """Remove an MCP server or hook group from a JSON config. Returns (removed entry, the key it lived under)."""
    data = inventory.load_config(cfg, "")
    if kind == "hook" and isinstance(data.get("hooks"), dict):
        event, _, idx = entry.partition(".")
        groups = data["hooks"].get(event)
        if isinstance(groups, list) and idx.isdigit() and int(idx) < len(groups):
            removed = groups.pop(int(idx))
            _write(cfg, data)
            return removed, f"hooks.{event}"
    for key in CONFIG_KEYS:
        block = data.get(key) if isinstance(data, dict) else None
        if isinstance(block, dict) and entry in block:
            removed = block.pop(entry)
            _write(cfg, data)
            return removed, key
    return None, None


def _write(cfg: Path, data) -> None:
    _backup(cfg)
    cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def isolate(component: dict, reason: str = "") -> dict:
    """Move one inventoried component (or a plain path) out of the agent's reach. Returns the record."""
    path_s, _, entry = component["path"].partition("#")
    src = Path(path_s)
    record = {"name": component.get("name") or src.name, "kind": component.get("kind", "path"), "host": component.get("host"),
              "original": str(src), "entry": entry or None, "reason": reason,
              "isolated_at": datetime.now(UTC).isoformat(timespec="seconds")}
    if entry:
        if src.suffix == ".toml":
            raise CannotIsolate(f"edit {src} by hand and remove the [mcp_servers.{entry}] table; unpick does not rewrite TOML")
        removed, key = _pop_entry(src, entry, component.get("kind", ""))
        if removed is None:
            raise CannotIsolate(f"{entry} is not in {src} any more")
        d = _new_dir(entry)
        record.update(key=key, config_entry=removed)
    else:
        if not src.exists():
            raise CannotIsolate(f"{src} does not exist")
        d = _new_dir(src.name)
        (d / "files").mkdir()
        shutil.move(str(src), d / "files" / src.name)
    record["id"] = d.name
    (d / META).write_text(json.dumps(record, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return record


def isolated() -> list[dict]:
    out = []
    for m in sorted(ROOT.glob(f"isolated-*/{META}")) if ROOT.is_dir() else []:
        try:
            out.append(json.loads(m.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out


def restore(item_id: str) -> str:
    d = ROOT / item_id
    meta = d / META
    if not meta.is_file():
        raise CannotIsolate(f"nothing in quarantine with id {item_id}")
    r = json.loads(meta.read_text(encoding="utf-8"))
    dest = Path(r["original"])
    if r.get("entry"):
        data = inventory.load_config(dest, "") if dest.is_file() else {}
        key = r["key"]
        if key.startswith("hooks."):
            data.setdefault("hooks", {}).setdefault(key.split(".", 1)[1], []).append(r["config_entry"])
        else:
            block = data.setdefault(key, {})
            if r["entry"] in block:
                raise CannotIsolate(f"{dest} already has an entry named {r['entry']}; remove it first")
            block[r["entry"]] = r["config_entry"]
        if dest.is_file():
            _write(dest, data)
        else:
            dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        msg = f"put {r['entry']} back into {dest}"
    else:
        if dest.exists():
            raise CannotIsolate(f"{dest} exists again; move it away before restoring")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(d / "files" / dest.name), dest)
        msg = f"moved {r['name']} back to {dest}"
    shutil.rmtree(d)
    return msg
