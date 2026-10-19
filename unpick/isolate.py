"""Quarantine and restore: move a flagged add-on out of your agent's reach, and put it back if it was a false alarm.

This is the antivirus-style step after a flag. An agent loads skills and plugins from known folders and
MCP servers from its config files, so moving the folder, or taking the entry out of the config, stops the
agent from using it. Nothing is deleted: each quarantined item keeps its files (or the config entry) and a
note of where it came from, so `unpick restore <id>` can undo it exactly. `recover` uses the same code.

Safety rules, from review:
  * a symlink is moved as a link, never followed, so a skill that links to ~/Documents cannot make unpick
    move your documents;
  * a config file is only rewritten when it is plain JSON in valid UTF-8 with no comments; anything else
    (JSONC with comments, TOML) gets the exact manual edit instead, because a rewrite would lose text;
  * every rewrite is backed up, written to a temporary file and swapped in atomically;
  * hooks are matched by their content, not their position in the list;
  * an id given to `restore` must name a folder directly inside the quarantine.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.home() / ".unpick" / "quarantine"
META = "isolated.json"
CONFIG_KEYS = ("mcpServers", "servers", "context_servers", "mcp")


class CannotIsolate(RuntimeError):
    pass


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _new_dir(name: str) -> Path:
    safe = re.sub(r"[^\w.-]+", "-", name)[:60] or "item"
    d = ROOT / f"isolated-{_stamp()}-{safe}"
    d.mkdir(parents=True, exist_ok=False)
    return d


def _has_comments(text: str) -> bool:
    """strip_jsonc removes comments and trailing commas; if it changes more than the commas, there were comments."""
    from unpick.inventory import strip_jsonc
    return strip_jsonc(text) != re.sub(r",(\s*[}\]])", r"\1", text)


def _read_plain_json(cfg: Path) -> dict:
    """Read a config only if unpick can rewrite it without losing anything."""
    if cfg.is_symlink():
        raise CannotIsolate(f"{cfg} is a symlink; edit the file it points to by hand")
    if cfg.suffix == ".toml":
        raise CannotIsolate(f"{cfg} is TOML, which unpick does not rewrite; remove the entry by hand")
    try:
        text = cfg.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise CannotIsolate(f"{cfg} is not valid UTF-8; remove the entry by hand") from e
    if _has_comments(text):
        raise CannotIsolate(f"{cfg} has comments that a rewrite would delete; remove the entry by hand")
    try:
        data = json.loads(text)
    except ValueError as e:
        raise CannotIsolate(f"{cfg} is not plain JSON; remove the entry by hand") from e
    if not isinstance(data, dict):
        raise CannotIsolate(f"{cfg} is not a JSON object")
    return data


def _write_atomic(cfg: Path, data: dict) -> Path:
    backup = cfg.with_name(cfg.name + f".unpick-backup-{_stamp()}")
    shutil.copy2(cfg, backup)
    fd, tmp = tempfile.mkstemp(dir=cfg.parent, prefix=f".{cfg.name}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, cfg)
    return backup


def _containers(data: dict):
    """Every place an MCP server can be listed: top-level blocks and Claude Code's per-project blocks."""
    for key in CONFIG_KEYS:
        if isinstance(data.get(key), dict):
            yield (key,), data[key]
    for proj, cfg in (data.get("projects") or {}).items() if isinstance(data.get("projects"), dict) else []:
        if isinstance(cfg, dict) and isinstance(cfg.get("mcpServers"), dict):
            yield ("projects", proj, "mcpServers"), cfg["mcpServers"]


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True)


def _pop_entry(data: dict, entry: str, kind: str, hook_json: str | None) -> list[dict]:
    """Remove every occurrence of the entry. Returns what was removed, with where it lived."""
    removed = []
    if kind == "hook" and isinstance(data.get("hooks"), dict):
        event = entry.partition(".")[0]
        groups = data["hooks"].get(event)
        if isinstance(groups, dict):
            groups = data["hooks"][event] = [groups]
        if isinstance(groups, list):
            keep = [g for g in groups if hook_json is None or _canon(g) != hook_json]
            if hook_json is None:  # no content to match on: fall back to the position the inventory saw
                idx = entry.partition(".")[2]
                keep = [g for i, g in enumerate(groups) if not (idx.isdigit() and i == int(idx))]
            removed += [{"where": ["hooks", event], "value": g} for g in groups if g not in keep]
            data["hooks"][event] = keep
    if entry.startswith("plugin:") and isinstance(data.get("plugin"), list):
        name = entry.split(":", 1)[1]
        if name in data["plugin"]:
            data["plugin"].remove(name)
            removed.append({"where": ["plugin"], "value": name})
    for where, block in _containers(data):
        if entry in block:
            removed.append({"where": list(where), "name": entry, "value": block.pop(entry)})
    return removed


def _hook_json(cfg: Path, entry: str) -> str | None:
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        event, _, idx = entry.partition(".")
        groups = data["hooks"][event]
        groups = groups if isinstance(groups, list) else [groups]
        return _canon(groups[int(idx)])
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return None


def isolate(component: dict, reason: str = "", hook_json: str | None = None) -> dict:
    """Move one inventoried component (or a plain path) out of the agent's reach. Returns the record."""
    path_s, _, entry = component["path"].partition("#")
    src = Path(os.path.abspath(os.path.expanduser(path_s)))  # absolute, but never through a symlink
    record = {"name": component.get("name") or src.name, "kind": component.get("kind", "path"), "host": component.get("host"),
              "original": str(src), "entry": entry or None, "reason": reason,
              "isolated_at": datetime.now(UTC).isoformat(timespec="seconds")}
    if entry:
        data = _read_plain_json(src)
        if component.get("kind") == "hook" and hook_json is None:
            hook_json = _hook_json(src, entry)
        removed = _pop_entry(data, entry, component.get("kind", ""), hook_json)
        if not removed:
            raise CannotIsolate(f"{entry} is not in {src} any more")
        d = _new_dir(entry.split(":")[-1])
        record["backup"] = str(_write_atomic(src, data))
        record["removed"] = removed
    else:
        if not os.path.lexists(src):
            raise CannotIsolate(f"{src} does not exist")
        d = _new_dir(src.name)
        (d / "files").mkdir()
        record["was_symlink"] = src.is_symlink()
        shutil.move(str(src), d / "files" / src.name)  # moves a symlink itself, never what it points to
        if os.path.lexists(src):
            record["came_back"] = True  # something recreated it straight away: likely a running process
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


def _item_dir(item_id: str) -> Path:
    if not re.fullmatch(r"isolated-[\w.-]+", item_id or ""):
        raise CannotIsolate(f"{item_id!r} is not a quarantine id")
    d = (ROOT / item_id).resolve()
    if d.parent != ROOT.resolve() or not (d / META).is_file():
        raise CannotIsolate(f"nothing in quarantine with id {item_id}")
    return d


def _put_back(data: dict, item: dict) -> None:
    where = item["where"]
    if where == ["plugin"]:
        data.setdefault("plugin", []).append(item["value"])
        return
    if where[0] == "hooks":
        data.setdefault("hooks", {}).setdefault(where[1], []).append(item["value"])
        return
    node = data
    for part in where:
        node = node.setdefault(part, {})
    if item["name"] in node:
        raise CannotIsolate(f"an entry named {item['name']} exists again; remove it first")
    node[item["name"]] = item["value"]


def restore(item_id: str) -> str:
    d = _item_dir(item_id)
    r = json.loads((d / META).read_text(encoding="utf-8"))
    dest = Path(r["original"])
    if any(p.is_symlink() for p in [dest.parent, *dest.parent.parents]):
        raise CannotIsolate(f"a folder on the way to {dest} is now a symlink; restore by hand")
    if r.get("entry"):
        data = _read_plain_json(dest) if dest.exists() else {}
        for item in r["removed"]:
            _put_back(data, item)
        if dest.exists():
            _write_atomic(dest, data)
        else:
            dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        msg = f"put {r['entry']} back into {dest}"
    else:
        if os.path.lexists(dest):
            raise CannotIsolate(f"{dest} exists again; move it away before restoring")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(d / "files" / dest.name), dest)
        msg = f"moved {r['name']} back to {dest}"
    shutil.rmtree(d)
    return msg
