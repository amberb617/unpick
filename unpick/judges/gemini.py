"""Gemini CLI as a judge: HOSTED. The full content of each file is sent to Google.

Opt-in only, with a per-session consent prompt. Built-in tools are switched off with a system settings
file (tools.core = [] registers zero built-in tools), and MCP servers, extensions and skills are disabled:
    GEMINI_CLI_SYSTEM_SETTINGS_PATH=<file> gemini -p <prompt> -o json -e none --skip-trust [-m M]
Gemini CLI has no schema flag, so the schema is described in the prompt and the output is validated
afterwards. Verified against the installed @google/gemini-cli 0.59.0 and https://geminicli.com/docs/cli/headless.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

NAME = "gemini"
KIND = "hosted"
PROVIDER = "Google (via the Gemini CLI)"
SETTINGS = {
    "tools": {"core": []},
    "mcp": {"allowed": []},
    "admin": {"mcp": {"enabled": False}, "extensions": {"enabled": False}, "skills": {"enabled": False}},
}


def detect() -> list[dict]:
    if not shutil.which("gemini"):
        return []
    return [{"id": "gemini:default", "model": "default", "found_by": shutil.which("gemini")}]


def complete(model: str, prompt: str, schema: dict) -> str:
    prompt += "\n\nThe JSON must match this JSON Schema:\n" + json.dumps(schema)
    with tempfile.TemporaryDirectory() as d:
        settings = os.path.join(d, "settings.json")
        with open(settings, "w", encoding="utf-8") as fh:
            json.dump(SETTINGS, fh)
        cmd = ["gemini", "-p", prompt, "-o", "json", "-e", "none", "--skip-trust"]
        if model and model != "default":
            cmd += ["-m", model]
        env = {**os.environ, "GEMINI_CLI_SYSTEM_SETTINGS_PATH": settings}
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env, cwd=d, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[-300:])
    out = json.loads(p.stdout)
    if out.get("error"):
        raise RuntimeError(str(out["error"])[:300])
    return out.get("response", "")
