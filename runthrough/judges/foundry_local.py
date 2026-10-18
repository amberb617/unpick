"""Windows (and macOS) Foundry Local: Microsoft's on-device model runtime, preview.

Its port is dynamic; runthrough asks `foundry server status` for the local URL and lists models with
`foundry model list`. Structured-output support is UNVERIFIED, so the schema is described in the prompt
and the output validated afterwards.

Phi Silica on Copilot+ PCs is NOT offered: Microsoft's Windows AI APIs require an app with package
identity and the systemAIModels capability, which a command-line Python process does not have.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess

from runthrough.judges import _local

NAME = "foundry-local"
KIND = "on-device"
UNVERIFIED = "Foundry Local structured-output support is not documented; output is validated after the fact"


def _base() -> str | None:
    if not shutil.which("foundry"):
        return None
    try:
        out = subprocess.run(["foundry", "server", "status"], capture_output=True, text=True, timeout=15).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r"https?://(?:127\.0\.0\.1|localhost):\d+", out)
    return m.group(0) if m else None


def detect() -> list[dict]:
    if not shutil.which("foundry"):
        return []
    base = _base()
    if not base:
        return [{"id": "foundry-local:", "model": "", "usable": False, "found_by": "foundry CLI",
                 "reason": "Foundry Local is installed but its server is not running (run: foundry server start)"}]
    return [{"id": f"foundry-local:{m}", "model": m, "found_by": f"{base}/v1/models", "unverified": UNVERIFIED}
            for m in _local.rank(_local.openai_models(base))]


def complete(model: str, prompt: str, schema: dict) -> str:
    prompt += "\n\nThe JSON must match this JSON Schema:\n" + json.dumps(schema)
    return _local.openai_chat(_base(), model, prompt, None)
