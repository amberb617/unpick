"""Cisco AI Defense mcp-scanner, static mode on a saved tools file. It never starts or contacts the server.

The analyzer list is passed explicitly (--analyzers yara) because the default includes the api and llm
analyzers. LITELLM_LOCAL_MODEL_COST_MAP=True stops litellm fetching its cost map from GitHub on import.
In static mode the output's server_url is just the --server-url default; no connection is made.
https://github.com/cisco-ai-defense/mcp-scanner (verified 4.8.6, see docs/VERIFIED.md)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from unpick.backends import which
from unpick.backends._common import finding

NAME = "cisco-mcp-scanner"
MAINTAINER = "Cisco AI Defense"
LICENSE = "Apache-2.0"
HOMEPAGE = "https://github.com/cisco-ai-defense/mcp-scanner"
TESTED_VERSION = "4.8.6"
INSTALL = "cisco-ai-mcp-scanner==4.8.6"
NETWORK = "none (yara analyzer on a tools file; LITELLM_LOCAL_MODEL_COST_MAP=True)"
NEEDS_ONLINE = False
ENV = {"LITELLM_LOCAL_MODEL_COST_MAP": "True"}
WHY = "Cisco mcp-scanner's YARA rules matched this tool's description."
FP = "Tools that legitimately handle files or credentials match these rules; compare the description to the tool's job."

os.environ.update(ENV)  # inherited by the subprocess, boxed or not


def _tools_files(target: Path) -> list[Path]:
    cands = [target] if target.is_file() else sorted(target.rglob("*.json"))
    out = []
    for p in cands:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            continue
        if isinstance(data, dict) and isinstance(data.get("tools"), list):
            out.append(p)
    return out


def applies(target: Path) -> bool:
    return bool(_tools_files(target))


def version():
    """mcp-scanner has no --version flag; ask the interpreter its script runs under for the package version."""
    import subprocess
    exe = which("mcp-scanner")
    if not exe:
        return None
    try:
        first = Path(exe).read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        first = ""
    python = first[2:].strip() if first.startswith("#!") else None
    if python and Path(python.split()[0]).exists():
        p = subprocess.run([*python.split(), "-c", "import importlib.metadata as m; print(m.version('cisco-ai-mcp-scanner'))"],
                           capture_output=True, text=True, timeout=20)
        if p.returncode == 0 and p.stdout.strip():
            return f"mcp-scanner {p.stdout.strip()}"
    return "mcp-scanner (version unknown)"


def command(target: Path) -> list[str]:
    return ["mcp-scanner", "--analyzers", "yara", "--format", "raw", "static", "--tools", str(_tools_files(target)[0])]


def parse(stdout: str, target: Path):
    data = json.loads(stdout)
    tools_file = _tools_files(target)[0]
    lines = tools_file.read_text(encoding="utf-8").splitlines()
    out = []
    for r in data.get("scan_results", []):
        name = r.get("tool_name", "")
        line = next((n for n, l in enumerate(lines, 1) if f'"{name}"' in l), 1)
        for analyzer, f in (r.get("findings") or {}).items():
            if not f or not f.get("total_findings"):
                continue
            for threat in f.get("threat_names") or ["finding"]:
                out.append(finding(NAME, threat.lower().replace(" ", "-"), f.get("severity"), str(tools_file), line,
                                   f"tool {name!r}: {threat.lower()} ({f.get('threat_summary', '')})", WHY, FP,
                                   original_rule_id=f"{analyzer}:{threat}", original_message=f.get("threat_summary"),
                                   extra={"tool": name, "taxonomies": f.get("mcp_taxonomies")}))
    return out
