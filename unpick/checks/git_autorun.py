"""Git settings that run programs: a repository folder that arrives with its own .git/config or .gitattributes.

Agents run git in the background. Codex CVE-2026-19590 to 19593 (2026-09) showed that a repo-local
`.git/config` with `core.fsmonitor`, `core.hooksPath` or a filter driver, plus a matching `.gitattributes`,
launches programs outside the agent's sandbox without a prompt
(https://www.zerodayinitiative.com/advisories/ZDI-26-651/). Folders downloaded as archives, or skills shipped with
their .git directory, are the way in. Sources in docs/research/2026-10-landscape.md.
"""

from __future__ import annotations

import re

from unpick.checks import Hit

RULE_ID = "RT-GIT-AUTORUN"
TITLE = "Git config that runs programs"
SEVERITY = "high"
WHY = "Git will run this program by itself whenever an editor or agent touches the repository, without asking you."
FALSE_POSITIVE = "Your own clone may use a hooks path or LFS filter you set up; it is suspicious in a folder you downloaded or a skill you are about to install."

CONFIG = re.compile(r"^\s*(fsmonitor|hookspath|sshcommand|askpass|pager|editor|gitproxy)\s*=\s*(.+)$", re.I)
FILTER = re.compile(r"^\s*(clean|smudge|process)\s*=\s*(.+)$", re.I)
SECTION = re.compile(r"^\s*\[\s*([\w.-]+)(?:\s+\"([^\"]*)\")?\s*\]")
SAFE_FILTERS = {"lfs"}


def applies(doc):
    p = doc.path.as_posix()
    return p.endswith("/.git/config") or doc.name in (".gitattributes", ".gitmodules") or p.endswith(".git/commondir")


def run(doc):
    if doc.name == ".gitattributes":
        for n, line in enumerate(doc.lines, 1):
            m = re.search(r"\bfilter=([\w-]+)", line)
            if m and m.group(1) not in SAFE_FILTERS:
                yield Hit(n, f".gitattributes applies filter '{m.group(1)}'; its program lives in git config", "medium")
        return
    if doc.name == "commondir":
        yield Hit(1, f".git/commondir redirects git to {doc.text.strip()[:80]}", "medium")
        return
    section, sub = "", ""
    for n, line in enumerate(doc.lines, 1):
        if m := SECTION.match(line):
            section, sub = m.group(1).lower(), (m.group(2) or "")
            continue
        if section == "filter" and sub not in SAFE_FILTERS and (m := FILTER.match(line)):
            yield Hit(n, f"filter '{sub}' runs: {m.group(2).strip()[:100]}")
        elif section in ("core", "credential", "") and (m := CONFIG.match(line)):
            key = m.group(1).lower()
            if key in ("pager", "editor") and not m.group(2).strip().startswith("!"):
                continue
            yield Hit(n, f"{section}.{key} runs: {m.group(2).strip()[:100]}")
        elif section == "alias" and "=" in line and line.split("=", 1)[1].strip().startswith("!"):
            yield Hit(n, f"git alias runs a shell command: {line.strip()[:100]}", "low")
