"""NVIDIA SkillSpector with LLM mode off (--no-llm).

Even with --no-llm it sends dependency names to OSV.dev (POST https://api.osv.dev/v1/querybatch) whenever
the skill has a dependency manifest, and there is no flag to stop that (verified at NVIDIA/skillspector@cf5cac7:
static_patterns_supply_chain.py -> osv_client.py). So runthrough runs it only with --online, or --boxed,
where the box blocks the call and SkillSpector falls back to its bundled advisory list.
SkillSpector is not on PyPI; install from its GitHub repository at the pinned commit.
"""

from __future__ import annotations

import json
from pathlib import Path

from runthrough.backends import version_of, which
from runthrough.backends._common import finding

NAME = "skillspector"
MAINTAINER = "NVIDIA"
LICENSE = "Apache-2.0"
HOMEPAGE = "https://github.com/nvidia/skillspector"
TESTED_VERSION = "2.12.0 (git cf5cac7)"
INSTALL = "skillspector @ git+https://github.com/nvidia/skillspector@cf5cac7ba5c756a6e0ebf52dc9763f49422f889f"
NETWORK = "OSV.dev: dependency names, when the skill has a manifest (even with --no-llm)"
NEEDS_ONLINE = True
WHY = "SkillSpector's static rules matched this location."
FP = "SkillSpector's YARA rules are broad (including offensive-tool indicators) and match documentation; read the line in context."


def applies(target: Path) -> bool:
    return target.is_dir() or target.name.lower().endswith(".md")


def version():
    return version_of(["skillspector", "--version"]) if which("skillspector") else None


def command(target: Path) -> list[str]:
    d = target if target.is_dir() else target.parent
    return ["skillspector", "scan", str(d), "--no-llm", "--format", "json"]


def parse(stdout: str, target: Path):
    data = json.loads(stdout)
    base = Path((data.get("skill") or {}).get("source") or (target if target.is_dir() else target.parent))
    out = []
    for i in data.get("issues", []):
        loc = i.get("location") or {}
        path = (base / loc["file"]).as_posix() if loc.get("file") else str(base)
        out.append(finding(NAME, i.get("id", "issue"), i.get("severity"), path, loc.get("start_line") or 0,
                           i.get("pattern") or i.get("category", ""), WHY, FP,
                           original_rule_id=i.get("id"), original_message=i.get("explanation"),
                           extra={"category": i.get("category"), "confidence": i.get("confidence")}))
    return out
