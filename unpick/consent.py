"""Consent for hosted judges: nothing is sent to a model provider without the person saying yes.

Every consent is recorded in ~/.unpick/consent.json with a timestamp. It only counts beyond the
current session if it was given with --remember. The prompt says exactly what happens: the full content of each scanned file goes to the provider.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_session: set[str] = set()
REMEMBER = False


def _file() -> Path:
    return Path.home() / ".unpick" / "consent.json"


def _all() -> dict:
    p = _file()
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _saved() -> dict:
    return {k: v for k, v in _all().items() if v.get("remember")}


def status(provider: str | None) -> str:
    if not provider:
        return "not needed"
    if provider in _session:
        return "granted (this session)"
    if provider in _saved():
        return f"granted (remembered {_saved()[provider]['at']})"
    return "not granted"


def prompt_text(provider: str) -> str:
    return (f"This judge is hosted by {provider}. The full content of every file being scanned will be sent to "
            f"{provider}. Nothing is sent unless you type yes. Send it? [yes/N] ")


def ensure(provider: str, ask=None) -> bool:
    """True if consent exists or is given now. `ask` is a callable(prompt)->bool; default reads stdin."""
    if provider in _session or provider in _saved():
        return True
    if ask is None:
        if not sys.stdin.isatty() or os.environ.get("UNPICK_NONINTERACTIVE"):
            return False
        ask = lambda text: input(text).strip().lower() == "yes"  # noqa: E731
    if not ask(prompt_text(provider)):
        return False
    _session.add(provider)
    data = _all()
    data[provider] = {"at": datetime.now(UTC).isoformat(timespec="seconds"), "remember": REMEMBER}
    _file().parent.mkdir(parents=True, exist_ok=True)
    _file().write_text(json.dumps(data, indent=2), encoding="utf-8")
    return True
