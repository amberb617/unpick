"""The on-device summary at the top of a scan: the model picks, unpick writes.

unpick builds every statement from the scan's records, so each is true by construction. Apple Intelligence
(Foundation Models, on this Mac) only chooses the three that matter most for an install decision and orders
them; guided generation limits its answer to those statement ids, so it cannot add a fact, a number or a
line. It never sees file text or finding messages: only these statements, which hold counts, rule ids and
file paths. On by default in an interactive terminal (owner decision, 2026-10-25); `--no-summary` turns it off, and
pipes and --json never call it. Design reviewed with Codex and Grok (DECISIONS.md, "Scan output").
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from unpick import digest

LABEL = "Summary (Apple Intelligence, on this Mac; picked from unpick's own statements)"
TIMEOUT = 20
PINNED = ("high_where", "no_high")


def statements(d: dict) -> dict[str, str]:
    """Every statement the model may pick, keyed by id. Each one is computed from the records."""
    b = digest.build(d)
    findings, cov = d.get("findings", []), b["coverage"]
    out: dict[str, str] = {}  # cross-cutting statements only: the TL;DR below already has one line per group
    if b["groups"]:
        top = b["groups"][0]
        out["top_group"] = f"Listed first: {top.mix}, {top.title.rstrip('.')} in {top.place}."
    high = [f for f in findings if f["severity"] == "high"]
    if high:
        files = sorted({f["path"] for f in high})
        shown = ", ".join(os.path.basename(x) for x in files[:3]) + (f" and {len(files) - 3} more" if len(files) > 3 else "")
        out["high_where"] = f"The {len(high)} high finding{'s' * (len(high) != 1)} sit in {len(files)} file{'s' * (len(files) != 1)}: {shown}."
    elif findings:
        out["no_high"] = "No finding is high. That is not the same as safe."
    low = sum(f["severity"] == "low" for f in findings)
    if findings and low * 2 > len(findings):
        out["mostly_low"] = f"{low} of the {len(findings)} findings are low."
    places = {digest.place(f["path"]) for f in findings}
    if {"code", "docs/config"} <= places:
        code = sum(digest.place(f["path"]) == "code" for f in findings)
        out["code_and_docs"] = f"{code} findings are in code files and {len(findings) - code} in docs, config or other files."
    if cov["not_read"]:
        n = cov["not_read"]
        out["unread"] = f"{n} file{'s were' if n != 1 else ' was'} not read, so {'they were' if n != 1 else 'it was'} not checked."
    if cov["sources"] == ["built-in"]:
        out["builtin_only"] = "Only unpick's built-in checks ran; no other scanner looked at this."
    if d.get("accepted"):
        out["accepted"] = f"{len(d['accepted'])} findings you accepted earlier are not shown as open."
    return out


def wanted(args) -> bool:
    return (not getattr(args, "json", False) and not getattr(args, "no_summary", False)
            and sys.stdout.isatty() and not os.environ.get("UNPICK_NONINTERACTIVE"))


def pick(d: dict, complete=None) -> tuple[list[str], str]:
    """(lines, note). Empty lines and a note when the model is unavailable or answered outside the rules."""
    st = statements(d)
    if len(st) < 2:
        return [], ""
    if complete is None:
        from unpick.judges import apple_fm
        found = apple_fm.detect()
        if not found or found[0].get("usable") is False:
            return [], ""  # no on-device model: the TL;DR below stands on its own

        def complete(prompt, schema):
            return apple_fm.complete("system", prompt, schema, timeout=TIMEOUT)
    ids = list(st)
    prompt = ("Someone is deciding whether to install an AI add-on. These statements describe a scan of it. "
              "Pick the three that matter most for that decision, most important first.\n\n"
              + "\n".join(f"[{k}] {v}" for k, v in st.items()))
    schema = {"type": "object", "properties": {"picks": {"type": "array", "items": {"type": "string", "enum": ids},
                                                          "minItems": 1, "maxItems": 3}}, "required": ["picks"]}
    try:
        picks = json.loads(complete(prompt, schema)).get("picks", [])
    except (subprocess.TimeoutExpired, RuntimeError, OSError, ValueError, AttributeError) as e:
        return [], f"On-device summary skipped: {type(e).__name__}."
    if not isinstance(picks, list) or not picks or any(p not in st for p in picks):
        return [], "On-device summary dropped: the model answered outside unpick's statements."
    pinned = [k for k in PINNED if k in st]  # the severity fact is never left to the model's choice
    chosen = pinned + [p for p in dict.fromkeys(picks) if p not in pinned]
    return [st[p] for p in chosen][:3], ""
