"""The 60-second "who made it?" card: step 1 of the triage.

Uses only the public, unauthenticated GitHub, npm and PyPI APIs (a network call, listed in README "When
data leaves your machine"; what is sent is the package or repository name). Each signal is a question to
ask, not a verdict. The look-alike signal compares the name with the publisher: an unofficial
`postmark-mcp` was the postmark-mcp attack, and look-alike GitHub orgs were the skills.sh campaign.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import UTC, datetime

from unpick import net
from unpick.checks.lookalike_names import judge_name

UA = {"User-Agent": "unpick (https://github.com/amberb617/unpick)", "Accept": "application/vnd.github+json"}
INSTALL_ASK = re.compile(r"\b(curl|wget|iwr|irm)\b[^\n]*\|\s*(sudo\s+)?(ba|z)?sh\b|paste .{0,30}terminal|\bnpx\s+-y\b|base64\s+-d", re.I)


def _json(url: str):
    with net.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.loads(r.read().decode("utf-8")), r.geturl()


def _age_days(ts: str | None) -> int | None:
    if not ts:
        return None
    try:
        return (datetime.now(UTC) - datetime.fromisoformat(ts.replace("Z", "+00:00"))).days
    except ValueError:
        return None


def github(owner: str, repo: str) -> dict:
    data, final = _json(f"https://api.github.com/repos/{owner}/{repo}")
    card = {
        "source": "github", "full_name": data.get("full_name"), "owner_type": (data.get("owner") or {}).get("type"),
        "created_at": data.get("created_at"), "age_days": _age_days(data.get("created_at")),
        "pushed_at": data.get("pushed_at"), "stars": data.get("stargazers_count"), "forks": data.get("forks_count"),
        "default_branch": data.get("default_branch"), "archived": data.get("archived"),
        "renamed_or_transferred": data.get("full_name", "").lower() != f"{owner}/{repo}".lower(),
    }
    try:
        contributors, _ = _json(f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=100")
        card["contributors"] = len(contributors)
        releases, _ = _json(f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=5")
        card["latest_release"] = releases[0]["tag_name"] if releases else None
    except (urllib.error.URLError, KeyError, IndexError, TypeError):
        pass
    return card


def npm(meta: dict, version: str) -> dict:
    times = meta.get("time", {})
    info = meta.get("versions", {}).get(version, {})
    publishers = [(v, (meta["versions"][v].get("_npmUser") or {}).get("name")) for v in meta.get("versions", {})]
    prev = [p for v, p in publishers if v != version and p]
    this = (info.get("_npmUser") or {}).get("name")
    repo = meta.get("repository") or {}
    return {
        "source": "npm", "name": meta.get("name"), "version": version, "created_at": times.get("created"),
        "age_days": _age_days(times.get("created")), "published_at": times.get(version),
        "maintainers": [m.get("name") for m in meta.get("maintainers", [])], "publisher": this,
        "publisher_changed": bool(prev) and this not in prev,
        "versions": len(meta.get("versions", {})), "repository": repo.get("url") if isinstance(repo, dict) else repo,
        "install_scripts": sorted(k for k in (info.get("scripts") or {}) if k in ("preinstall", "install", "postinstall", "prepare")),
    }


def pypi(meta: dict) -> dict:
    info = meta.get("info", {})
    uploads = [f.get("upload_time_iso_8601") for rel in (meta.get("releases") or {}).values() for f in rel]
    first = min((u for u in uploads if u), default=None)
    return {
        "source": "pypi", "name": info.get("name"), "version": info.get("version"), "created_at": first,
        "age_days": _age_days(first), "author": info.get("author") or info.get("author_email"),
        "maintainer": info.get("maintainer") or info.get("maintainer_email"),
        "project_urls": info.get("project_urls"), "versions": len(meta.get("releases") or {}),
    }


def questions(card: dict, name: str, readme_text: str = "") -> list[str]:
    """Plain-language questions the card raises. Empty means nothing stood out, not that it is safe."""
    q = []
    if card.get("age_days") is not None and card["age_days"] < 30:
        q.append(f"It is {card['age_days']} days old.")
    if card.get("renamed_or_transferred"):
        q.append(f"The repository moved: it is now {card['full_name']}.")
    if card.get("publisher_changed"):
        q.append(f"This version was published by {card['publisher']}, who did not publish earlier versions.")
    if card.get("install_scripts"):
        q.append(f"It runs install scripts: {', '.join(card['install_scripts'])}.")
    if card.get("stars") is not None and card.get("forks") is not None and card["stars"] > 200 and card["forks"] < 2:
        q.append("Many stars but almost no forks, a pattern seen with bought stars.")
    owner = (card.get("full_name") or "").split("/")[0]
    hit = judge_name(name)
    if hit and hit[0] not in owner.lower():
        q.append(f"The name suggests {hit[0]}, but the publisher is {owner or card.get('publisher') or 'someone else'}.")
    if INSTALL_ASK.search(readme_text):
        q.append("Its install instructions ask you to run a command that fetches or decodes code.")
    return q
