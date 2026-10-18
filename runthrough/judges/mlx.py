"""MLX (`mlx_lm.server`): an OpenAI-compatible server on localhost:8080, Apple silicon.

mlx_lm.server has no JSON-schema mode, so the schema is described in the prompt and the output is
validated afterwards (and retried once). Temperature defaults to 0. Set RUNTHROUGH_MLX_URL to override.
"""

from __future__ import annotations

import json
import os

from runthrough.judges import _local

NAME = "mlx"
KIND = "on-device"


def _base() -> str:
    return os.environ.get("RUNTHROUGH_MLX_URL", "http://127.0.0.1:8080")


def detect() -> list[dict]:
    return [{"id": f"mlx:{m}", "model": m, "found_by": f"{_base()}/v1/models"}
            for m in _local.rank(_local.openai_models(_base()))]


def complete(model: str, prompt: str, schema: dict) -> str:
    prompt += "\n\nThe JSON must match this JSON Schema:\n" + json.dumps(schema)
    return _local.openai_chat(_base(), model, prompt, None)
