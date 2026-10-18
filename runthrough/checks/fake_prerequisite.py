"""Fake prerequisite: setup prose that asks a human to paste something into a terminal.

The ClawHavoc campaign on ClawHub (Jan-Feb 2026) hid no malware in the skill itself. Its SKILL.md
files had a "Prerequisites" section telling the reader to paste a base64 command into Terminal, or to
download a password-protected ZIP, and that step installed Atomic macOS Stealer.
https://www.esecurityplanet.com/threats/hundreds-of-malicious-skills-found-in-openclaws-clawhub/
https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/
"""

from __future__ import annotations

import re

from runthrough.checks import Hit
from runthrough.checks._md import walk

RULE_ID = "RT-PREREQ"
TITLE = "Fake prerequisite / paste-to-terminal"
SEVERITY = "medium"
WHY = "Setup text asks you to paste or run something yourself, which is how the ClawHavoc skills got users to install a stealer without any code in the skill."
FALSE_POSITIVE = "Plenty of honest tools document an install command; it is a problem when the command fetches and runs something you cannot read first."

SETUP_HEADING = re.compile(r"prereq|pre-req|setup|set up|requirement|install|getting started|before you|quick ?start|dependencies", re.I)
ASK = re.compile(
    r"\b(paste|copy)\b.{0,40}\b(terminal|shell|powershell|command prompt|cmd|console)\b"
    r"|\b(open|launch)\b.{0,15}\b(terminal|powershell|command prompt)\b"
    r"|\brun (this|the following|these|the) (command|one-liner|script|line)s?\b"
    r"|\b(download|grab)\b.{0,60}\.(zip|dmg|pkg|exe|msi|7z|rar|tar\.gz|tgz|app)\b"
    r"|\bpassword[- ]protected\b.{0,30}\b(zip|archive)\b"
    r"|\b(zip|archive|\.7z|\.rar)\b.{0,60}\b(password|passcode) (is|:)\s*\S+",
    re.I,
)
ONE_LINER = re.compile(
    r"\b(curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod)\b.+\|"
    r"|\bbase64\b.+\|\s*(sudo\s+)?(ba|z)?sh\b"
    r"|\b(sh|bash|zsh)\s+-c\s+[\"']?\$\("
    r"|\bxattr\s+-[dc]",
    re.I,
)


def applies(doc):
    return doc.is_markdown or doc.name.endswith(".txt")


def run(doc):
    for n, line, heading, in_fence in walk(doc.lines):
        in_setup = bool(SETUP_HEADING.search(heading))
        if ASK.search(line):
            yield Hit(n, f"asks the reader to run or download something (section: {heading or 'none'})",
                      "high" if in_setup else "medium", {"section": heading})
        elif in_fence and in_setup and ONE_LINER.search(line):
            yield Hit(n, f"one-liner that fetches or decodes and runs code, under '{heading}'", "high",
                      {"section": heading})
