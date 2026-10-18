"""Rules and instruction files: AGENTS.md, CLAUDE.md, .cursorrules, copilot-instructions.md and friends.

These files are loaded into every session without a prompt. A rules file that fetches outside code,
points at external URLs, or turns off the assistant's safety behaviour changes every answer the
assistant gives in that project. Pillar Security's "Rules File Backdoor" (2025) showed rules files used
to steer Copilot and Cursor into writing malicious code:
https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents
"""

from __future__ import annotations

import re

from runthrough.checks import Hit

RULE_ID = "RT-RULES-FILE"
TITLE = "Risky rules-file instruction"
SEVERITY = "medium"
WHY = "This instruction file is loaded into every session automatically, and this line pulls in outside content or weakens the assistant's safety behaviour."
FALSE_POSITIVE = "Project rules often link to the team's own docs or say which commands are safe to run without asking; check that the link and the commands are yours."

# Documentation hosts reserved by RFC 2606 and loopback are not "outside content"; the host must end there.
URL = re.compile(r"https?://(?!(?:[\w-]+\.)*example\.(?:com|org|net|invalid)(?=[/:?#\s)\]'\"]|$)|localhost(?=[/:]|$)|127\.0\.0\.1(?=[/:]|$))[^\s)>\]'\"]+", re.I)
FETCH = re.compile(r"\b(fetch|download|curl|wget|pull|import|load|include)\b.{0,40}\b(code|script|instructions?|rules|from|url|https?://)", re.I)
WEAKEN = re.compile(
    r"\b(disable|skip|bypass|turn off|ignore|suppress|remove)\b.{0,30}\b(security|safety|confirmation|approval|permission|sandbox|warning|review|lint|tests?|checks?)\b"
    r"|\b(auto[- ]?approve|always allow|never ask|without asking|yolo|full[- ]auto)\b"
    r"|--dangerously-skip-permissions|--dangerously-bypass-approvals-and-sandbox|--yolo\b",
    re.I,
)


def applies(doc):
    return doc.is_rules


def run(doc):
    for n, line in enumerate(doc.lines, 1):
        if WEAKEN.search(line):
            yield Hit(n, "weakens the assistant's safety or review behaviour", "high")
        elif FETCH.search(line) and URL.search(line):
            yield Hit(n, f"asks the assistant to fetch outside content: {URL.search(line).group(0)}", "high")
        elif URL.search(line):
            yield Hit(n, f"references an external URL: {URL.search(line).group(0)}", "low")
