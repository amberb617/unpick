"""LM Studio: an OpenAI-compatible server, usually on localhost:1234.

Structured output: response_format {"type": "json_schema", "json_schema": {"schema": ...}}. LM Studio's
docs warn models under 7B may not comply, so output is still validated. Port 1234 is the documented
example rather than a stated default (UNVERIFIED as a default); set UNPICK_LMSTUDIO_URL to override.
"""

from __future__ import annotations

import os

from unpick.judges import _local

NAME = "lmstudio"
KIND = "on-device"
UNVERIFIED = "port 1234 is LM Studio's documented example, not a documented default"


def _base() -> str:
    return os.environ.get("UNPICK_LMSTUDIO_URL", "http://127.0.0.1:1234")


def detect() -> list[dict]:
    return [{"id": f"lmstudio:{m}", "model": m, "found_by": f"{_base()}/v1/models"}
            for m in _local.rank(_local.openai_models(_base()))]


def complete(model: str, prompt: str, schema: dict) -> str:
    return _local.openai_chat(_base(), model, prompt, schema)
