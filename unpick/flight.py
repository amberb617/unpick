"""Flight recorder: an append-only log of every tool call an agent makes.

Without it, "what did the agent do?" has no answer after the fact. `unpick record` is meant to run as a
hook (it reads the hook's JSON on stdin) and appends one line per call to ~/.unpick/flight/<date>.jsonl:
timestamp, tool, arguments with secret-looking values redacted, working directory, exit status. It never
blocks and never prints anything the agent could read. rehearse and recover read the same files.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.home() / ".unpick" / "flight"
SECRET_KEY = re.compile(r"(token|secret|password|passwd|api[_-]?key|authorization|cookie|credential|private[_-]?key)", re.I)
SECRET_VALUE = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[abpr]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|npm_[A-Za-z0-9]{20,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})")


def redact(obj, key: str = ""):
    if isinstance(obj, dict):
        return {k: redact(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, key) for v in obj]
    if isinstance(obj, str):
        if SECRET_KEY.search(key) and obj:
            return "[redacted]"
        return SECRET_VALUE.sub("[redacted]", obj)
    return obj


def append(event: dict, root: Path | None = None) -> Path:
    root = root or ROOT
    root.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    line = {
        "ts": now.isoformat(timespec="milliseconds"),
        "agent": event.get("agent", "claude-code"),
        "event": event.get("hook_event_name") or event.get("event"),
        "session": event.get("session_id"),
        "tool": event.get("tool_name") or event.get("tool"),
        "input": redact(event.get("tool_input") or event.get("input") or {}),
        "cwd": event.get("cwd"),
        "status": _status(event),
    }
    p = root / f"{now.date().isoformat()}.jsonl"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=True) + "\n")
    return p


def _status(event: dict):
    resp = event.get("tool_response")
    if isinstance(resp, dict):
        for k in ("exit_code", "exitCode", "returncode"):
            if k in resp:
                return resp[k]
        if "is_error" in resp:
            return "error" if resp["is_error"] else "ok"
    return event.get("status")


def read(root: Path | None = None, since: datetime | None = None) -> list[dict]:
    root = root or ROOT
    out = []
    for p in sorted(root.glob("*.jsonl")) if root.is_dir() else []:
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                e = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if since and datetime.fromisoformat(e["ts"]) < since:
                continue
            out.append(e)
    return out
