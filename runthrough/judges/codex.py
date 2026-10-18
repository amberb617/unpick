"""OpenAI Codex CLI: detected, but NOT used as a judge.

A judge must have no tools. Codex can turn off its shell tool (`--disable shell_tool`) and runs read-only
by default, but there is no single switch that disables every tool, and the model-visible tool list
cannot be printed, so zero tools cannot be confirmed (verified against `codex exec --help` 0.159.3 and
`codex features list`). Use an on-device judge, or `--judge api:openai` with an API key.
"""

from __future__ import annotations

import shutil

NAME = "codex"
KIND = "hosted"
PROVIDER = "OpenAI (via the Codex CLI)"
REASON = "Codex CLI cannot be confirmed to run with zero tools, so it is not used as a judge"


def detect() -> list[dict]:
    if not shutil.which("codex"):
        return []
    return [{"id": "codex:default", "model": "default", "found_by": shutil.which("codex"), "usable": False, "reason": REASON}]


def complete(model: str, prompt: str, schema: dict) -> str:
    raise RuntimeError(REASON)
