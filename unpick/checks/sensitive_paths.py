"""Sensitive paths and secret names: SSH keys, .env files, cloud credentials, browser profiles, keychains.

Data theft is what most malicious skills do: 89.8% of the 400 confirmed malicious skills in the
MalSkills study (arXiv:2603.27204, https://arxiv.org/html/2603.27204). Invariant Labs' tool-poisoning
proof of concept asks the agent to read ~/.ssh/id_rsa and mcp.json
(https://github.com/invariantlabs-ai/mcp-injection-experiments). Patterns live in data/sensitive_paths.txt.
"""

from __future__ import annotations

import re
from functools import cache

from unpick.checks import Hit
from unpick.resources import load_list

RULE_ID = "RT-SENSITIVE-PATH"
TITLE = "Sensitive path or secret mention"
SEVERITY = "medium"
WHY = "The component names a file or variable that holds credentials or private data, which an agent following it may read or send somewhere."
FALSE_POSITIVE = "Documentation that tells you never to commit a .env file, or a tool whose stated job is managing keys, mentions these for good reasons."

# Lines that warn against leaking the file ("never commit your .env") still fire, at low severity.
# In prose, naming a dotenv file is how setup docs work ("add your key to the local env file"). It stays medium
# when the same line reads, sends or prints it. Measured 2026-10-25: 495 of 729 medium findings on installed
# add-ons were dotenv-file mentions in Markdown setup notes. Code keeps medium: a script that opens one is worth a look.
ACCESS = re.compile(r"\b(cat|less|head|tail|open|load|source|send|upload|post|print|echo|copy|cp|attach|include|exfil\w*|curl|wget|base64|read)\b", re.I)
REDIRECT_IN = re.compile(r"<\s*[\"']?[~$\w./{}-]*\.env")  # a shell redirect from a dotenv file reads it as surely as cat does
NEGATED = re.compile(r"\b(never|don't|do not|must not|should not)\s+(commit|share|upload|push|paste|check in)\b|\.?gitignore\b", re.I)


@cache
def _patterns():
    return [(re.compile(rx, re.I), why) for rx, why in load_list("sensitive_paths.txt")]


def run(doc):
    if doc.name.endswith("ignore"):
        return  # .gitignore and friends list secret files to keep them out; no agent follows them
    for n, line in enumerate(doc.lines, 1):
        hits = [(rx.search(line), why) for rx, why in _patterns()]
        hits = [(m, why) for m, why in hits if m]
        if not hits:
            continue
        names = sorted({m.group(0) for m, _ in hits})
        only_env_names = all(why.startswith("env var") for _, why in hits)  # naming a variable is not reading it
        prose_mention = doc.is_markdown and not ACCESS.search(line) and not REDIRECT_IN.search(line)
        sev = "low" if NEGATED.search(line) or only_env_names or prose_mention else None
        yield Hit(n, f"mentions {', '.join(names)} ({hits[0][1]})", sev,
                  {"matches": names, "reasons": sorted({w for _, w in hits})})
