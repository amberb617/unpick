"""Rendered vs raw divergence: lines where what a Markdown viewer shows is not what the model reads.

If you review a skill on GitHub or in a Markdown preview, you see the rendered page. The agent gets the
raw bytes, including HTML comments, invisible characters, collapsed <details> content and text pushed
off-screen. Reading the raw file is step 2 of the five-minute triage; this check does it for you.
Hidden-in-plain-sight instructions in rules files: Pillar Security, "Rules File Backdoor" (2025),
https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents
The line-aligned view itself is unpick.render, shared with the CLI and the UI.
"""

from __future__ import annotations

import re

from unpick.checks import Hit
from unpick.render import rows

RULE_ID = "RT-RENDER-DIVERGE"
TITLE = "Rendered view hides content"
SEVERITY = "medium"
WHY = "A Markdown viewer would not show you this line the way the model reads it, so reviewing the rendered page would miss it."
FALSE_POSITIVE = "Licence headers, editor directives and FAQ sections often live in HTML comments or <details> blocks; read the raw line to see which this is."

# Words aimed at the agent, not at a reader. "always", "run" or a bare URL are ordinary documentation and no
# longer raise a line on their own: measured 2026-10-25, they made 1,407 distinct high findings across 297
# installed add-ons, nearly all README prose (DECISIONS.md, "Rule precision").
AGENT = re.compile(
    r"\b(you must|you should|ignore (all |any |the )?(previous|prior|above|earlier)|disregard (all|any|the|previous)"
    r"|do not (tell|mention|inform|reveal)|don'?t (tell|mention|inform|reveal)|without (telling|asking|informing)"
    r"|as an ai|exfiltrat\w*)\b"
    r"|curl\b.*\|\s*(ba|z)?sh\b|\b(send|post|upload)\b.{0,60}\b(to|https?://)", re.I)
URL = re.compile(r"https?://", re.I)
TRULY_HIDDEN = ("inside an HTML comment", "text pushed off-screen", "hidden HTML element")


def applies(doc):
    return doc.is_markdown


def run(doc):
    for r in rows(doc.text):
        reasons = [x for x in r.reasons if not x.startswith("invisible characters")]  # RT-UNICODE reports those
        if not reasons:
            continue
        hidden_text = r.raw if not r.rendered else r.raw.replace(r.rendered, "")
        yield Hit(r.line, "; ".join(reasons), _severity(reasons, hidden_text),
                  {"raw": r.raw, "rendered": r.rendered, "reasons": reasons})


def _severity(reasons: list[str], hidden_text: str) -> str:
    hidden = any(x.startswith(TRULY_HIDDEN) for x in reasons)
    if any("points to" in x or "off-screen" in x for x in reasons):
        return "high"  # a link that lies about its target, or text deliberately moved out of view
    if AGENT.search(hidden_text):
        return "high" if hidden else SEVERITY  # a collapsed <details> block opens with one click
    if all(x == "inside an HTML comment" for x in reasons):
        return SEVERITY if URL.search(hidden_text) else "low"  # editor notes and licence headers live in comments
    if all(x == "inside a collapsed <details> block" for x in reasons):
        return "low"  # FAQ and long examples live in <details>; agent-directed text raises it
    return SEVERITY
