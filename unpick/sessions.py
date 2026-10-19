"""Read the agents' own session logs into one timeline of tool calls, for `recover`.

Formats were read from local files (keys only) and docs on 2026-10-18; none of the vendors documents its
schema, so a parser that finds nothing it recognises says so instead of guessing (docs/verified/phase4.md):
  * Claude Code: ~/.claude/projects/<project>/<session>.jsonl (and <session>/subagents/). Tool calls are
    type "assistant" lines whose message.content[] holds {type: "tool_use", name, input}; timestamp is ISO.
  * Codex CLI: ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl, lines {timestamp, type, payload}; a payload of
    type function_call has name and arguments (a JSON string); newer rollouts log custom_tool_call with input.
  * Gemini CLI: ~/.gemini/tmp/<hash>/chats/session-*.jsonl; type "gemini" lines carry toolCalls[] with
    {name, args, timestamp}.
  * Cursor writes no per-session tool log; the flight recorder (a hook) is the only record. OpenCode's
    storage format is UNVERIFIED and not parsed.
Values are passed through flight.redact before they are kept.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from unpick import flight


def _ts(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _lines(path: Path) -> Iterator[dict]:
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    yield obj
    except OSError:
        return


def _event(agent, ts, tool, args, source, session=None) -> dict:
    return {"ts": ts.isoformat(timespec="seconds") if ts else None, "agent": agent, "tool": tool,
            "input": flight.redact(args if isinstance(args, dict) else {"value": args}), "source": str(source), "session": session}


def claude_code(home: Path, since: datetime | None) -> Iterator[dict]:
    for f in sorted((home / ".claude" / "projects").glob("**/*.jsonl")):
        if since and datetime.fromtimestamp(f.stat().st_mtime, UTC) < since:
            continue
        for obj in _lines(f):
            if obj.get("type") != "assistant":
                continue
            ts = _ts(obj.get("timestamp"))
            if since and ts and ts < since:
                continue
            for part in (obj.get("message") or {}).get("content") or []:
                if isinstance(part, dict) and part.get("type") == "tool_use":
                    yield _event("claude-code", ts, part.get("name"), part.get("input"), f, obj.get("sessionId"))


def codex(home: Path, since: datetime | None) -> Iterator[dict]:
    for f in sorted((home / ".codex" / "sessions").glob("**/rollout-*.jsonl")):
        if since and datetime.fromtimestamp(f.stat().st_mtime, UTC) < since:
            continue
        for obj in _lines(f):
            p = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
            kind = p.get("type")
            if kind not in ("function_call", "custom_tool_call"):
                continue
            ts = _ts(obj.get("timestamp"))
            if since and ts and ts < since:
                continue
            args = p.get("arguments") if kind == "function_call" else p.get("input")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"command": args}
            yield _event("codex", ts, p.get("name"), args, f)


def gemini(home: Path, since: datetime | None) -> Iterator[dict]:
    for f in sorted((home / ".gemini" / "tmp").glob("*/chats/session-*.jsonl")):
        if since and datetime.fromtimestamp(f.stat().st_mtime, UTC) < since:
            continue
        for obj in _lines(f):
            if obj.get("type") != "gemini":
                continue
            for call in obj.get("toolCalls") or []:
                ts = _ts(call.get("timestamp") or obj.get("timestamp"))
                if since and ts and ts < since:
                    continue
                yield _event("gemini-cli", ts, call.get("name"), call.get("args"), f)


def recorder(since: datetime | None) -> Iterator[dict]:
    for e in flight.read(since=since):
        yield {"ts": e["ts"], "agent": e.get("agent"), "tool": e.get("tool"), "input": e.get("input") or {},
               "source": "flight recorder", "session": e.get("session")}


def timeline(since: datetime | None, home: Path | None = None) -> list[dict]:
    home = home or Path.home()
    events = [*claude_code(home, since), *codex(home, since), *gemini(home, since), *recorder(since)]
    return sorted(events, key=lambda e: e["ts"] or "")
