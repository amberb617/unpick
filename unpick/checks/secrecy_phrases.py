"""Secrecy and override phrases: text that tells the model to hide something from you, or to stop following its rules.

"Do not mention this to the user" has no honest use in a tool description. Invariant Labs' tool-poisoning
proof of concept combines a secrecy phrase with an instruction to read private files
(https://github.com/invariantlabs-ai/mcp-injection-experiments). The scored list is data/phrases.json;
phrases scored 3 are almost never benign.
"""

from __future__ import annotations

import re
from functools import cache

from unpick.checks import Hit
from unpick.resources import load_json

RULE_ID = "RT-SECRECY"
TITLE = "Secrecy or override phrase"
SEVERITY = "medium"
WHY = "The text uses wording about secrecy or about setting an AI's rules aside, which is worth reading in context to see whether it is an instruction or a description."
FALSE_POSITIVE = "Security write-ups, test fixtures and prompt-injection training material quote these phrases as examples."

SCORE_TO_SEV = {1: "low", 2: "medium", 3: "high"}


@cache
def _phrases():
    return [(re.compile(p["pattern"], re.I), p) for p in load_json("phrases.json")["phrases"]]


def run(doc):
    for n, line in enumerate(doc.lines, 1):
        found = [(m, p) for rx, p in _phrases() if (m := rx.search(line))]
        if not found:
            continue
        top = max(p["score"] for _, p in found)
        yield Hit(n, "phrase: " + "; ".join(f"{m.group(0)!r} ({p['category']})" for m, p in found),
                  SCORE_TO_SEV[top], {"phrases": [p["pattern"] for _, p in found], "score": top,
                                      "categories": sorted({p["category"] for _, p in found})})
