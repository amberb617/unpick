"""Cisco AI Defense skill-scanner, static mode only.

Offline by default: static, YARA-X, bytecode, pipeline and correlation analyzers. runthrough never passes
the opt-in --use-* flags (LLM, VirusTotal, AI Defense, OSV). Its own README reports that rules alone catch
about 8% (7.7%) of held-out malicious skills on its benchmark, which is why this is one witness among several.
https://github.com/cisco-ai-defense/skill-scanner (verified @8554b11, see docs/VERIFIED.md)
"""

from __future__ import annotations

import json
from pathlib import Path

from runthrough.backends import version_of, which
from runthrough.backends._common import finding

NAME = "cisco-skill-scanner"
MAINTAINER = "Cisco AI Defense"
LICENSE = "Apache-2.0"
HOMEPAGE = "https://github.com/cisco-ai-defense/skill-scanner"
TESTED_VERSION = "2.3.0"
INSTALL = "cisco-ai-skill-scanner==2.3.0"
NETWORK = "none (static mode; no --use-* flags)"
NEEDS_ONLINE = False
WHY = "Cisco skill-scanner's static analyzers matched this location."
FP = "Static rules fire on documentation and examples too; read the line in context."


def applies(target: Path) -> bool:
    return target.is_dir() or target.name.lower().endswith(".md")


def version():
    v = version_of(["skill-scanner", "--version"]) if which("skill-scanner") else None
    return v


def command(target: Path) -> list[str]:
    d = target if target.is_dir() else target.parent
    return ["skill-scanner", "scan", str(d), "--format", "json"]


def parse(stdout: str, target: Path):
    data = json.loads(stdout)
    base = Path(data.get("skill_path") or (target if target.is_dir() else target.parent))
    out = []
    for f in data.get("findings", []):
        path = (base / f["file_path"]).as_posix() if f.get("file_path") else str(base)
        out.append(finding(NAME, f.get("rule_id", "finding"), f.get("severity"), path, f.get("line_number") or 0,
                           f.get("title") or f.get("description", ""), WHY, FP,
                           original_rule_id=f.get("rule_id"), original_message=f.get("description"),
                           extra={"analyzer": f.get("analyzer"), "category": f.get("category")}))
    return out
