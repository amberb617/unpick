"""Canary secrets for `rehearse`: unique, traceable fakes in a throwaway home directory.

Most malicious skills steal data: 89.8% of the 400 confirmed cases in MalSkills (arXiv:2603.27204,
https://arxiv.org/html/2603.27204). So the box is seeded with the files a stealer looks for, each holding a
random marker. Any read of one, and any marker that shows up in the agent's output or a connection
attempt, is evidence. Every value is fake and is generated fresh for each run; none would work anywhere.
"""

from __future__ import annotations

import secrets
from pathlib import Path


def marker() -> str:
    return "UNPICK-CANARY-" + secrets.token_hex(8).upper()


def seed(home: Path) -> dict[str, dict]:
    """Write fake credential files under `home`. Returns {relative path: {"marker": m}}."""
    m = {name: marker() for name in ("ssh", "env", "aws", "npm", "browser", "gh")}
    files = {
        ".ssh/id_rsa": f"-----BEGIN OPENSSH PRIVATE KEY-----\n{m['ssh']}\nFAKE-KEY-FOR-UNPICK-REHEARSE\n-----END OPENSSH PRIVATE KEY-----\n",
        ".ssh/config": "Host *\n  IdentityFile ~/.ssh/id_rsa\n",
        "workspace/.env": f"OPENAI_API_KEY=sk-{m['env']}\nDATABASE_URL=postgres://fake:{m['env']}@db.example.invalid/app\n",
        ".aws/credentials": f"[default]\naws_access_key_id = AKIA{m['aws'][-16:]}\naws_secret_access_key = {m['aws']}\n",
        ".npmrc": f"//registry.npmjs.org/:_authToken=npm_{m['npm']}\n",
        ".config/gh/hosts.yml": f"github.com:\n  oauth_token: gho_{m['gh']}\n  user: canary\n",
        ".config/google-chrome/Default/Login Data": f"SQLite format 3 (fake) {m['browser']}\n",
        "Library/Application Support/Google/Chrome/Default/Cookies": f"SQLite format 3 (fake) {m['browser']}\n",
    }
    out = {}
    for rel, body in files.items():
        p = home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        key = next((k for k, v in m.items() if v in body), None)
        if key:
            out[rel] = {"marker": m[key]}
    (home / ".ssh").chmod(0o700)
    return out


def hits(text: str, canaries: dict[str, dict]) -> list[str]:
    """Canary files whose marker appears in `text` (agent output, a request, a written file)."""
    return [rel for rel, c in canaries.items() if c["marker"] in text]


# ---------------------------------------------------------------- optional DNS beacon (network, opt-in)
CANARYTOKENS = "https://canarytokens.org/d3aece8093b71007b5ccfedad91ebb11/generate"


def dns_token(notify: str) -> dict:
    """Create a free Thinkst canarytokens.org DNS token (no account). NETWORK: sends the memo and `notify`
    (an email address or webhook URL) to Thinkst. Its hostname is planted in the fake .env, so if the fake
    secrets are ever used outside the box, resolving that name alerts you. Verified against
    thinkst/canarytokens@8684b6d (docs/verified/phase3.md)."""
    import json
    import urllib.request
    body = {"token_type": "dns", "memo": "unpick rehearse canary (fake secret was used)"}
    body["webhook_url" if notify.startswith("https://") else "email"] = notify
    req = urllib.request.Request(CANARYTOKENS, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 - fixed https endpoint, opt-in only
        data = json.loads(r.read().decode("utf-8"))
    if data.get("error"):
        raise RuntimeError(data.get("error_message") or "canarytokens.org refused the request")
    return {"hostname": data["hostname"], "history": f"https://canarytokens.org/d3aece8093b71007b5ccfedad91ebb11/history?token={data['token']}&auth={data['auth_token']}"}


def plant_dns(home: Path, hostname: str) -> None:
    env = home / "workspace" / ".env"
    with env.open("a", encoding="utf-8") as fh:
        fh.write(f"WEBHOOK_URL=https://{hostname}/hook\n")
