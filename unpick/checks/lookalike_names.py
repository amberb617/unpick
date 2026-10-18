"""Look-alike names: components named one typo away from a well-known vendor or package.

Typo-squats and look-alikes trade on a name you already trust. The unofficial `postmark-mcp` package
on npm was not published by Postmark, and version 1.0.16 quietly BCC'd every email to an attacker
(https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html). This check reads the name a
component declares (SKILL.md frontmatter, package.json, pyproject.toml, MCP server keys, tool lists) and
compares it with data/known_names.txt. It cannot tell who published it; the `check` command does that.
"""

from __future__ import annotations

import json
import re
from functools import cache

from unpick.checks import Hit
from unpick.resources import load_list

RULE_ID = "RT-LOOKALIKE"
TITLE = "Look-alike name"
SEVERITY = "medium"
WHY = "The component's name is a near-miss or a borrowed version of a well-known vendor's name, which is how look-alike packages get installed by mistake."
FALSE_POSITIVE = "Many honest community projects put a vendor's name in theirs (an unofficial client is not a scam); check the publisher matches."

HOMO = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "7": "t", "@": "a", "$": "s"})
FRONT_NAME = re.compile(r"^\s*name\s*:\s*['\"]?([^'\"\n#]+)", re.I)
TOML_NAME = re.compile(r"^\s*name\s*=\s*['\"]([^'\"]+)", re.I)


@cache
def _known():
    return [n.lower() for n, _ in load_list("known_names.txt")]


def _dist(a: str, b: str) -> int:
    """Damerau-Levenshtein (optimal string alignment) distance."""
    d = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = a[i - 1] != b[j - 1]
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def judge_name(name: str) -> tuple[str, str] | None:
    """Return (vendor, kind) if `name` imitates a known name. kind is 'typo' or 'borrowed'."""
    norm = name.lower().strip()
    parts = [p for p in re.split(r"[^a-z0-9@$]+", norm) if p]
    for part in parts:
        fixed = part.translate(HOMO).replace("rn", "m").replace("vv", "w")
        for known in _known():
            if part == known:
                continue
            if fixed == known or (len(known) >= 5 and _dist(part, known) == 1) or (len(known) >= 8 and _dist(part, known) == 2):
                return known, "typo"
    for known in _known():
        if known in parts and norm != known:
            return known, "borrowed"
    return None


def _frontmatter_names(doc):
    if not doc.lines or doc.lines[0].strip() != "---":
        return
    for n, line in enumerate(doc.lines[1:], 2):
        if line.strip() == "---":
            return
        m = FRONT_NAME.match(line)
        if m:
            yield n, m.group(1).strip()


def _toml_names(doc):
    for n, line in enumerate(doc.lines, 1):
        m = TOML_NAME.match(line)
        if m:
            yield n, m.group(1)
            return


def _json_names(doc):
    try:
        data = json.loads(doc.text)
    except json.JSONDecodeError:
        return
    if not isinstance(data, dict):
        return
    names = [data["name"]] if doc.name == "package.json" and isinstance(data.get("name"), str) else []
    for key in ("mcpServers", "servers", "context_servers"):
        if isinstance(data.get(key), dict):
            names.extend(data[key].keys())
    for name in names:
        yield next((n for n, line in enumerate(doc.lines, 1) if f'"{name}"' in line), 1), name


def _declared_names(doc):
    if doc.is_markdown:
        return _frontmatter_names(doc)
    if doc.name in ("pyproject.toml", "cargo.toml"):
        return _toml_names(doc)
    if doc.is_json:
        return _json_names(doc)
    return iter(())


def run(doc):
    for line, name in _declared_names(doc):
        hit = judge_name(name)
        if not hit:
            continue
        known, kind = hit
        if kind == "typo":
            yield Hit(line, f"name {name!r} is one or two characters away from {known!r}", "high", {"name": name, "imitates": known})
        else:
            yield Hit(line, f"name {name!r} borrows {known!r}; confirm the publisher is {known}", "low", {"name": name, "imitates": known})
