"""YARA-X with unpick's bundled rule set (data/yara/unpick.yar), fully local.

Uses the `yr` command if installed, otherwise the `yara-x` Python package through a small runner that
prints the same JSON. YARA-X reports byte offsets; unpick turns them into line numbers.
https://github.com/VirusTotal/yara-x (verified 1.21.0, see docs/VERIFIED.md)
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from unpick.backends import version_of, which
from unpick.backends._common import finding, offset_to_line
from unpick.resources import data_dir

NAME = "yara-x"
MAINTAINER = "VirusTotal"
LICENSE = "BSD-3-Clause"
HOMEPAGE = "https://github.com/VirusTotal/yara-x"
TESTED_VERSION = "1.21.0"
INSTALL = "yara-x==1.21.0"
NETWORK = "none"
NEEDS_ONLINE = False
WHY = "A YARA rule from unpick's bundled rule set matched these bytes."
FP = "Pattern rules match quoted examples and documentation as readily as live instructions."
RULES = data_dir() / "yara" / "unpick.yar"


def applies(target: Path) -> bool:
    return True


def version():
    if which("yr"):
        return version_of(["yr", "--version"])
    if importlib.util.find_spec("yara_x"):
        import yara_x
        return f"yara-x (python) {getattr(yara_x, '__version__', 'unknown')}"
    return None


def command(target: Path) -> list[str]:
    if which("yr"):
        recursive = ["--recursive"] if target.is_dir() else []  # yr refuses --recursive on a file
        return ["yr", "scan", "--output-format", "json", "--print-meta", "--print-strings", *recursive, str(RULES), str(target)]
    return [sys.executable, "-m", "unpick.backends._yarax_runner", str(RULES), str(target)]


def parse(stdout: str, target: Path):
    data = json.loads(stdout)
    out = []
    for m in data.get("matches", []):
        f = Path(m["file"])
        meta = m.get("meta") or {}
        offsets = [s.get("offset", 0) for s in m.get("strings", [])] or [0]
        for line in sorted({offset_to_line(f, o) for o in offsets}):
            out.append(finding(NAME, m["rule"], meta.get("severity"), str(f), line,
                               meta.get("description", m["rule"]), WHY, FP, original_rule_id=m["rule"],
                               original_message=meta.get("description")))
    return out
