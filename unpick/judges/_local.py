"""Shared plumbing for judges that run on this machine and speak HTTP on localhost.

Every request goes to a loopback address. A URL that is not loopback is refused, so a local tier can
never quietly become a hosted one.
"""

from __future__ import annotations

import ipaddress
import json
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

TIMEOUT = 600


def is_loopback(url: str) -> bool:
    host = urlparse(url).hostname or ""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _check(url: str) -> None:
    if not is_loopback(url):
        raise ValueError(f"refusing non-loopback URL for an on-device judge: {url}")


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False


def get_json(url: str, timeout: float = 3):
    _check(url)
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 - loopback only, checked above
        return json.loads(r.read().decode("utf-8"))


def post_json(url: str, body: dict, timeout: float = TIMEOUT):
    _check(url)
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def openai_models(base: str) -> list[str]:
    try:
        data = get_json(base.rstrip("/") + "/v1/models")
    except (OSError, urllib.error.URLError, ValueError):
        return []
    return [m.get("id") for m in data.get("data", []) if m.get("id")]


def openai_chat(base: str, model: str, prompt: str, schema: dict | None, style: str = "lmstudio") -> str:
    """POST /v1/chat/completions at temperature 0. `style` picks the response_format dialect the server accepts."""
    body = {"model": model, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}
    if schema is not None:
        if style == "llamacpp":
            body["response_format"] = {"type": "json_schema", "schema": schema}
        else:
            body["response_format"] = {"type": "json_schema", "json_schema": {"name": "judge", "strict": True, "schema": schema}}
    data = post_json(base.rstrip("/") + "/v1/chat/completions", body)
    return data["choices"][0]["message"]["content"]


PREFERRED = ("3b", "4b", "7b", "8b", "mini", "small", "instruct")


def rank(models: list[str]) -> list[str]:
    """Prefer small instruct models (3B-8B class); keep the rest in their original order."""
    return sorted(models, key=lambda m: (not any(t in m.lower() for t in PREFERRED), models.index(m)))
