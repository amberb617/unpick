"""Model provider APIs, using a key already in your environment: HOSTED, and never automatic.

A key in the environment is listed as available but never used unless you pass --judge api:<provider>,
and you are asked for consent before anything is sent. Plain HTTPS chat-completion calls; the model gets
no tools. UNVERIFIED: the endpoints and request shapes below have not yet been checked against each
provider's current API reference for this release, so this tier prints a warning when used.
"""

from __future__ import annotations

import json
import os
import urllib.request

NAME = "api"
KIND = "hosted"
PROVIDER = "a model provider API"
UNVERIFIED = "provider API endpoints and request shapes not yet verified for this release"

PROVIDERS = {
    "anthropic": {"env": "ANTHROPIC_API_KEY", "label": "Anthropic API", "model": "claude-haiku-5-5"},
    "openai": {"env": "OPENAI_API_KEY", "label": "OpenAI API", "model": "gpt-5-mini",
               "url": "https://api.openai.com/v1/chat/completions"},
    "xai": {"env": "XAI_API_KEY", "label": "xAI API", "model": "grok-4-fast",
            "url": "https://api.x.ai/v1/chat/completions"},
}


def provider_for(model_id: str) -> str:
    name = model_id.split("/", 1)[0]
    return PROVIDERS.get(name, {}).get("label", name)


def detect() -> list[dict]:
    rows = []
    for name, p in PROVIDERS.items():
        if os.environ.get(p["env"]):
            rows.append({"id": f"api:{name}", "model": name, "found_by": f"${p['env']} is set",
                         "provider": p["label"], "unverified": UNVERIFIED, "explicit_only": True})
    return rows


def _post(url: str, headers: dict, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=600) as r:  # noqa: S310 - fixed provider URLs, consent required
        return json.loads(r.read().decode("utf-8"))


def complete(model: str, prompt: str, schema: dict) -> str:
    name, _, override = model.partition("/")
    p = PROVIDERS[name]
    key = os.environ[p["env"]]
    prompt += "\n\nThe JSON must match this JSON Schema:\n" + json.dumps(schema)
    if name == "anthropic":
        data = _post("https://api.anthropic.com/v1/messages",
                     {"x-api-key": key, "anthropic-version": "2023-06-01"},
                     {"model": override or p["model"], "max_tokens": 4096, "temperature": 0,
                      "messages": [{"role": "user", "content": prompt}]})
        return "".join(b.get("text", "") for b in data.get("content", []))
    data = _post(p["url"], {"Authorization": f"Bearer {key}"},
                 {"model": override or p["model"], "temperature": 0, "messages": [{"role": "user", "content": prompt}],
                  "response_format": {"type": "json_object"}})
    return data["choices"][0]["message"]["content"]
