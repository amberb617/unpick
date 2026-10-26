"""Jiffy (commercial, network): OPT-IN ONLY, never a default.

Disclosure: Jiffy Labs is the company of unpick's author. This backend wraps the `jiffy` CLI
(@jiffylabs/jiffy-cli, MIT), which needs a Jiffy account. `jiffy scanner scan <path> --json` first sends
a hash of the files to Jiffy's API, and uploads the component's files when Jiffy has not seen those bytes.
It is listed in README "When data leaves your machine" and only runs with --online.
Exit codes: 0 pass or review, 2 block, 1 unverified (verified against Jiffy-Labs-AI/jiffy-cli@b724e01 README.md,
https://github.com/Jiffy-Labs-AI/jiffy-cli).
"""

from __future__ import annotations

import json
from pathlib import Path

from unpick.backends import version_of, which
from unpick.backends._common import finding

NAME = "jiffy"
MAINTAINER = "Jiffy Labs (commercial)"
LICENSE = "MIT (CLI); service is commercial"
HOMEPAGE = "https://github.com/Jiffy-Labs-AI/jiffy-cli"
TESTED_VERSION = "1.2.0"
INSTALL = None  # npm package; install with your Node package manager if you choose this backend
NETWORK = "Jiffy API: file hashes, then the component's files if not already known; needs a Jiffy account"
NEEDS_ONLINE = True
WHY = "The Jiffy service flagged this location."
WHY_LOCAL = "The Jiffy CLI's local checks flagged this location."
FP = "Verdicts follow your organization's Jiffy policies; a finding here is one source among several."


def applies(target: Path) -> bool:
    return True


def version():
    return version_of(["jiffy", "--version"]) if which("jiffy") else None


def command(target: Path) -> list[str]:
    return ["jiffy", "scanner", "scan", str(target), "--json"]


def parse(stdout: str, target: Path):
    """Server findings (`findings[]`) and the CLI's own local checks (`local.findings[]`, jiffy-cli 1.2.0:
    ruleId, severity, title, file, line). Reading only the first list dropped every local finding."""
    data = json.loads(stdout)
    base = target if target.is_dir() else target.parent
    out = []
    for f in data.get("findings", []):
        path = (base / f["file"]).as_posix() if f.get("file") else str(base)
        out.append(finding(NAME, f.get("ruleId") or "finding", f.get("severity"), path, f.get("line") or 0,
                           f.get("message") or f.get("ruleName") or "", WHY, FP,
                           original_rule_id=f.get("ruleId"), original_message=f.get("message")))
    for f in (data.get("local") or {}).get("findings", []):
        path = (base / f["file"]).as_posix() if f.get("file") else str(base)
        out.append(finding(NAME, f.get("ruleId") or "local", f.get("severity"), path, f.get("line") or 0,
                           f.get("title") or "", WHY_LOCAL, FP, original_rule_id=f.get("ruleId"),
                           original_message=f.get("title"), extra={"via": "jiffy-cli local check"}))
    return out


def notes(stdout: str) -> list[str]:
    """What Jiffy could not do. `via: none` means no server verdict: only the CLI's local checks ran, so the
    scan must not read as a full Jiffy check."""
    try:
        data = json.loads(stdout)
    except ValueError:
        return []
    if data.get("via") != "none":
        return []
    reasons = [r for r in data.get("reasons", []) if not r.startswith("a local check found")]
    return [f"jiffy: the Jiffy server did not check this ({'; '.join(reasons) or 'no server verdict'}); "
            "only the Jiffy CLI's local checks ran"]
