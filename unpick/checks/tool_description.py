"""MCP tool descriptions: the text the model reads to decide which tool to call, and you usually never see.

Tool poisoning hides instructions in a tool's description. Invariant Labs' proof of concept is an `add`
tool whose description tells the model to read ~/.ssh/id_rsa and pass it in a parameter
(https://github.com/invariantlabs-ai/mcp-injection-experiments). This check reads saved tool lists
(a tools.json export, or a saved `tools/list` response). It never starts the server.
"""

from __future__ import annotations

import json
import re

from unpick.checks import Hit

RULE_ID = "RT-TOOL-DESC"
TITLE = "Suspicious MCP tool description"
SEVERITY = "medium"
WHY = "A tool's description is instructions the model follows, and this one is far longer than its job, or talks about files, the network, other tools or the user."
FALSE_POSITIVE = "File-system, browser and HTTP tools legitimately describe files and URLs; compare the description to what the tool's name says it does."

MENTIONS = {
    "files": re.compile(r"~/|\b(read|open|cat|load)\b.{0,20}\b(file|contents?)\b|\.ssh|\.env\b|id_rsa|mcp\.json|/etc/", re.I),
    "network": re.compile(r"https?://|\b(send|post|upload|forward|exfil)\w*\b.{0,30}\b(to|url|server|endpoint)\b", re.I),
    "other tools": re.compile(r"\b(other|another|all) tools?\b|\bwhen (calling|using) (the )?\w+ tool\b|\binstead of\b.{0,20}\btool\b", re.I),
    "the user": re.compile(r"\bthe user\b", re.I),
    "hidden markup": re.compile(r"<\s*(important|system|secret|instructions?)\s*>", re.I),
}
SECRET_PARAM = re.compile(r"(content|contents|file|key|secret|token|password|credential|ssh|note|context|sidenote|extra|metadata)", re.I)
ASKS_CONTENT = re.compile(r"\b(contents? of|full text of|read|paste|pass)\b", re.I)


def _tools(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("tools"), list):
            return data["tools"]
        result = data.get("result")
        if isinstance(result, dict) and isinstance(result.get("tools"), list):
            return result["tools"]
    return []


def _line_of(lines: list[str], needle: str, default: int = 1) -> int:
    needle = needle[:60]
    for n, line in enumerate(lines, 1):
        if needle and needle in line:
            return n
    return default


def applies(doc):
    return doc.is_json


def run(doc):
    try:
        data = json.loads(doc.text)
    except json.JSONDecodeError:
        return
    for tool in _tools(data):
        if not isinstance(tool, dict) or "name" not in tool:
            continue
        name = str(tool.get("name", ""))
        desc = str(tool.get("description") or "")
        schema = tool.get("inputSchema") or tool.get("input_schema") or tool.get("parameters") or {}
        name_line = _line_of(doc.lines, json.dumps(name)[1:-1])
        desc_line = _line_of(doc.lines, json.dumps(desc)[1:-1], name_line) if desc else name_line

        reasons = []
        budget = 120 + 40 * len((schema or {}).get("properties", {}) or {})
        if len(desc) > max(300, 3 * budget):
            reasons.append(f"description is {len(desc)} characters for a tool named {name!r}")
        mentions = [label for label, rx in MENTIONS.items() if rx.search(desc)]
        if mentions:
            reasons.append("description mentions " + ", ".join(mentions))
        if reasons:
            sev = "high" if ({"files", "hidden markup"} & set(mentions) or len(mentions) >= 3) else SEVERITY
            yield Hit(desc_line, f"tool {name!r}: " + "; ".join(reasons), sev,
                      {"tool": name, "description_length": len(desc), "mentions": mentions})

        for pname, pspec in ((schema or {}).get("properties") or {}).items():
            pdesc = str((pspec or {}).get("description", "")) if isinstance(pspec, dict) else ""
            if SECRET_PARAM.search(pname) and (ASKS_CONTENT.search(pdesc) or MENTIONS["files"].search(pdesc + desc)):
                yield Hit(_line_of(doc.lines, f'"{pname}"', desc_line),
                          f"tool {name!r} parameter {pname!r} looks like a channel for file contents or secrets",
                          "high", {"tool": name, "parameter": pname})
