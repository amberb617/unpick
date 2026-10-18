"""Rendered vs raw divergence: lines where what a Markdown viewer shows is not what the model reads.

If you review a skill on GitHub or in a Markdown preview, you see the rendered page. The agent gets the
raw bytes, including HTML comments, invisible characters, collapsed <details> content and text pushed
off-screen. Reading the raw file is step 2 of the five-minute triage; this check does it for you.
Hidden-in-plain-sight instructions in rules files: Pillar Security, "Rules File Backdoor" (2025),
https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents
The line-aligned view itself is runthrough.render, shared with the CLI and the UI.
"""

from __future__ import annotations

import re

from runthrough.checks import Hit
from runthrough.render import rows

RULE_ID = "RT-RENDER-DIVERGE"
TITLE = "Rendered view hides content"
SEVERITY = "medium"
WHY = "A Markdown viewer would not show you this line the way the model reads it, so reviewing the rendered page would miss it."
FALSE_POSITIVE = "Licence headers, editor directives and FAQ sections often live in HTML comments or <details> blocks; read the raw line to see which this is."

IMPERATIVE = re.compile(r"\b(you must|always|never|ignore|send|read|run|execute|fetch|curl|do not tell|instead)\b|https?://", re.I)


def applies(doc):
    return doc.is_markdown


def run(doc):
    for r in rows(doc.text):
        if not r.differs:
            continue
        hidden_text = r.raw if not r.rendered else r.raw.replace(r.rendered, "")
        yield Hit(r.line, "; ".join(r.reasons), _severity(r.reasons, hidden_text),
                  {"raw": r.raw, "rendered": r.rendered, "reasons": r.reasons})


def _severity(reasons: list[str], hidden_text: str) -> str:
    if IMPERATIVE.search(hidden_text) or any("points to" in x or "off-screen" in x for x in reasons):
        return "high"
    if all(x == "inside an HTML comment" for x in reasons):
        return "low"  # editor notes and licence headers live in comments; instructions or URLs raise it to high
    return SEVERITY
