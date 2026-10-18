"""Jiffy (commercial, network): OPT-IN ONLY, never a default.

Disclosure: Jiffy Labs is the company of runthrough's author. This backend wraps the `jiffy` CLI
(@jiffylabs/jiffy-cli, MIT), which needs a Jiffy account. `jiffy scanner scan <path> --json` first sends
a hash of the files to Jiffy's API, and uploads the component's files when Jiffy has not seen those bytes.
It is listed in README "When data leaves your machine" and only runs with --online.
Exit codes: 0 pass or review, 2 block, 1 unverified (verified against Jiffy-Labs-AI/jiffy-cli@b724e01 README.md,
https://github.com/Jiffy-Labs-AI/jiffy-cli).
"""

from __future__ import annotations

import json
from pathlib import Path

from runthrough.backends import version_of, which
from runthrough.backends._common import finding

NAME = "jiffy"
MAINTAINER = "Jiffy Labs (commercial)"
LICENSE = "MIT (CLI); service is commercial"
HOMEPAGE = "https://github.com/Jiffy-Labs-AI/jiffy-cli"
TESTED_VERSION = "1.2.0"
INSTALL = None  # npm package; install with your Node package manager if you choose this backend
NETWORK = "Jiffy API: file hashes, then the component's files if not already known; needs a Jiffy account"
NEEDS_ONLINE = True
WHY = "The Jiffy service flagged this location."
FP = "Verdicts follow your organization's Jiffy policies; a finding here is one source among several."


def applies(target: Path) -> bool:
    return True


def version():
    return version_of(["jiffy", "--version"]) if which("jiffy") else None


def command(target: Path) -> list[str]:
    return ["jiffy", "scanner", "scan", str(target), "--json"]


def parse(stdout: str, target: Path):
    data = json.loads(stdout)
    base = target if target.is_dir() else target.parent
    out = []
    for f in data.get("findings", []):
        path = (base / f["file"]).as_posix() if f.get("file") else str(base)
        out.append(finding(NAME, f.get("ruleId") or "finding", f.get("severity"), path, f.get("line") or 0,
                           f.get("message") or f.get("ruleName") or "", WHY, FP,
                           original_rule_id=f.get("ruleId"), original_message=f.get("message")))
    return out
