"""llama.cpp `llama-server`: an OpenAI-compatible server, by default on 127.0.0.1:9931 (not 8080).

Structured output: response_format {"type": "json_schema", "schema": ...}. Set UNPICK_LLAMACPP_URL
to use another loopback address. Verified against ggml-org/llama.cpp tools/server/README.md.
"""

from __future__ import annotations

import os

from unpick.judges import _local

NAME = "llamacpp"
KIND = "on-device"


def _base() -> str:
    return os.environ.get("UNPICK_LLAMACPP_URL", "http://127.0.0.1:9931")


def detect() -> list[dict]:
    return [{"id": f"llamacpp:{m}", "model": m, "found_by": f"{_base()}/v1/models"} for m in _local.openai_models(_base())]


def complete(model: str, prompt: str, schema: dict) -> str:
    return _local.openai_chat(_base(), model, prompt, schema, style="llamacpp")
