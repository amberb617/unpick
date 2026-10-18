"""Ollama: local models on 127.0.0.1:11434 (or $OLLAMA_HOST). Nothing leaves the machine.

Structured output: POST /api/chat with `format` set to the JSON schema, `options.temperature` 0.
Verified against ollama/ollama docs/api.md (see docs/VERIFIED.md).
"""

from __future__ import annotations

import os

from unpick.judges import _local

NAME = "ollama"
KIND = "on-device"


def _base() -> str:
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
    return host if host.startswith("http") else f"http://{host}"


def detect() -> list[dict]:
    base = _base()
    if not _local.is_loopback(base):
        return [{"id": "ollama:", "model": "", "usable": False, "found_by": "OLLAMA_HOST",
                 "reason": f"OLLAMA_HOST points off this machine ({base}); not treated as on-device"}]
    try:
        tags = _local.get_json(base + "/api/tags")
    except Exception:
        return []
    models = _local.rank([m["name"] for m in tags.get("models", [])])
    return [{"id": f"ollama:{m}", "model": m, "found_by": f"{base}/api/tags"} for m in models]


def complete(model: str, prompt: str, schema: dict) -> str:
    data = _local.post_json(_base() + "/api/chat", {
        "model": model, "stream": False, "format": schema, "options": {"temperature": 0},
        "messages": [{"role": "user", "content": prompt}],
    })
    return data["message"]["content"]
