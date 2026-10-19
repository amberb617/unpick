"""Install redirects: text that steers you or your agent away from the official source.

In the skills.sh campaign (Zenity Labs, 2026-07) the malicious skills told the agent not to install from
the registry and to clone a look-alike repository instead, and package-registry rewrites point npm or pip
at a mirror the attacker controls. Trail of Bits (2026-06) showed such rewrites can be phrased to sound
like corporate policy so that LLM-based scanners accept them. Sources and URLs in
docs/research/2026-10-landscape.md; npm `registry` config: https://docs.npmjs.com/cli/v10/using-npm/config#registry
"""

from __future__ import annotations

import re

from unpick.checks import Hit

RULE_ID = "RT-INSTALL-REDIRECT"
TITLE = "Install redirected away from the official source"
SEVERITY = "medium"
WHY = "The text steers the install away from the official registry or repository, which is how look-alike sources and attacker-run mirrors get used."
FALSE_POSITIVE = "Plenty of honest projects say to install from source or use a company mirror; check that the source named is the project's own."

AVOID_REGISTRY = re.compile(
    r"\b(do not|don't|never|avoid)\s+(use|install\s+(it\s+)?(via|with|from|using))\s+(the\s+)?(npx|npm|pnpm|pip|pipx|uvx|pypi|"
    r"the\s+registry|the\s+marketplace|clawhub|skills\.sh)\b", re.I)
ONLY_CLONE = re.compile(r"\b(only|official)\s+(supported\s+)?(way|method|source)\b.{0,60}\bgit\s+clone\b", re.I)
NO_CONVERT = re.compile(r"\b(do not|don't)\s+(convert|change|rewrite|replace)\b.{0,40}\b(github\s+)?url\b", re.I)
REGISTRY_SET = [re.compile(rx, re.I) for rx in (
    r"npm\s+config\s+set\s+(?:@[\w-]+:)?registry\s+(?P<url>\S+)",
    r"^\s*(?:@[\w-]+:)?registry\s*=\s*(?P<url>\S+)",
    r"--(?:extra-)?index-url[\s=]+(?P<url>\S+)",
    r"\b(?:PIP|UV)_(?:EXTRA_)?INDEX_URL\s*=\s*(?P<url>\S+)",
)]
OFFICIAL = ("registry.npmjs.org", "pypi.org", "files.pythonhosted.org", "registry.yarnpkg.com")
READ_FIRST = re.compile(r"\b(read|run|open|follow)\b.{0,30}\b[\w./-]*(setup|install|bootstrap|init)[\w.-]*\.(md|sh|ps1|txt|mjs|js|py)\b.{0,20}\b(first|before)\b", re.I)


def applies(doc):
    return doc.is_markdown or doc.name in (".npmrc", "pip.conf", "pip.ini", ".pypirc") or doc.name.endswith((".txt", ".sh", ".ps1", ".toml", ".cfg"))


def run(doc):
    for n, line in enumerate(doc.lines, 1):
        if m := AVOID_REGISTRY.search(line):
            yield Hit(n, f"tells you not to use the registry: {m.group(0)!r}", "high")
        elif ONLY_CLONE.search(line):
            yield Hit(n, "says cloning a repository is the only way to install", None)
        elif NO_CONVERT.search(line):
            yield Hit(n, "tells you not to change the URL it gives", None)
        for m in (m for rx in REGISTRY_SET for m in rx.finditer(line)):
            url = m.group("url").strip("`'\"")
            if url.startswith(("http", "git+")) and not any(o in url for o in OFFICIAL):
                yield Hit(n, f"points the package manager at {url}", "high", {"registry": url})
        if READ_FIRST.search(line):
            yield Hit(n, "sends you to a setup file before anything else", "low")
