"""Any OpenAI-compatible server you run on this machine, at the loopback URL in UNPICK_OPENAI_LOCAL_URL.

For runtimes unpick does not know by name (vLLM, Jan, LocalAI, a custom server). The URL must be
loopback; anything else is refused so this tier cannot become a hosted one by accident.
"""

from __future__ import annotations

import os

from unpick.judges import _local

NAME = "openai-local"
KIND = "on-device"


def _base() -> str | None:
    return os.environ.get("UNPICK_OPENAI_LOCAL_URL")


def detect() -> list[dict]:
    base = _base()
    if not base:
        return []
    if not _local.is_loopback(base):
        return [{"id": "openai-local:", "model": "", "usable": False, "found_by": "UNPICK_OPENAI_LOCAL_URL",
                 "reason": f"{base} is not a loopback address"}]
    return [{"id": f"openai-local:{m}", "model": m, "found_by": f"{base}/v1/models"} for m in _local.openai_models(base)]


def complete(model: str, prompt: str, schema: dict) -> str:
    return _local.openai_chat(_base(), model, prompt, schema)
