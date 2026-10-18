"""Paste sites, throwaway file hosts, request catchers, tunnels and raw IP addresses in URLs.

Code fetched from a paste site can change after you read the skill, and nobody vouches for it.
ClawHavoc fetched its payload from glot.io and reported to a raw-IP command server (Unit 42,
https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/). The domain list lives in
data/paste_domains.txt with a reason for each entry.
"""

from __future__ import annotations

import ipaddress
import re

from unpick.checks import Hit
from unpick.resources import load_list

RULE_ID = "RT-PASTE-HOST"
TITLE = "Paste-site or throwaway hosting"
SEVERITY = "medium"
WHY = "The component points at a paste site, anonymous file host, request catcher, tunnel or bare IP address, where content can change after review and data sent there is readable by a stranger."
FALSE_POSITIVE = "Tutorials and test fixtures mention these services legitimately; it matters when the component fetches from or sends to one."

URL = re.compile(r"\b(?:https?|ftp)://([^\s/'\"<>)\]]+)([^\s'\"<>)\]]*)", re.I)
BARE = re.compile(r"(?<![\w.-])((?:[a-z0-9-]+\.)+[a-z]{2,})(/[^\s'\"<>)\]]*)?", re.I)


def _domains():
    return [(d.lower(), why) for d, why in load_list("paste_domains.txt")]


def _match(host: str, path: str):
    host = host.lower().split("@")[-1].split(":")[0]
    full = host + path.lower()
    for d, why in _domains():
        if "/" in d:
            if full.startswith(d) or ("." + d) in ("." + full):
                return d, why
        elif host == d or host.endswith("." + d):
            return d, why
    return None


def run(doc):
    for n, line in enumerate(doc.lines, 1):
        seen = set()
        for m in URL.finditer(line):
            host, path = m.group(1), m.group(2)
            bare_host = host.split("@")[-1].split(":")[0].strip("[]")
            try:
                ip = ipaddress.ip_address(bare_host)
                if not (ip.is_loopback or ip.is_private or ip.is_unspecified):
                    yield Hit(n, f"URL uses a bare public IP address: {m.group(0)}", "high", {"url": m.group(0)})
                seen.add(bare_host)
                continue
            except ValueError:
                pass
            hit = _match(host, path)
            if hit:
                seen.add(hit[0])
                yield Hit(n, f"URL on {hit[0]}: {hit[1]}", None, {"url": m.group(0), "domain": hit[0]})
        for m in BARE.finditer(line):
            hit = _match(m.group(1), m.group(2) or "")
            if hit and hit[0] not in seen:
                seen.add(hit[0])
                yield Hit(n, f"mentions {hit[0]}: {hit[1]}", "low", {"domain": hit[0]})
