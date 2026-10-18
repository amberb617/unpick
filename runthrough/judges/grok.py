"""xAI Grok Build CLI: detected, but NOT used as a judge.

`grok -p` supports `--json-schema`, but its docs say MCP meta-tools stay available whatever `--tools`
says, and it loads MCP servers, plugins and allow rules from other agents' config with no flag to skip
them, so zero tools cannot be confirmed (verified against `grok --help` 1.0.46 and xai-org/grok-build
docs/user-guide/14-headless-mode.md). Use an on-device judge, or `--judge api:xai` with an API key.
"""

from __future__ import annotations

import shutil

NAME = "grok"
KIND = "hosted"
PROVIDER = "xAI (via the Grok CLI)"
REASON = "Grok CLI keeps MCP tools available and cannot be confirmed to run with zero tools, so it is not used as a judge"


def detect() -> list[dict]:
    if not shutil.which("grok"):
        return []
    return [{"id": "grok:default", "model": "default", "found_by": shutil.which("grok"), "usable": False, "reason": REASON}]


def complete(model: str, prompt: str, schema: dict) -> str:
    raise RuntimeError(REASON)
