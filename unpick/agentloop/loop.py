"""The disposable agent for `unpick rehearse`. Runs inside the no-network box, never on your machine.

It loads one component the way a coding agent would (the skill's SKILL.md goes into its instructions, an
MCP tools.json becomes its tool list), then works on a benign task with real tools: read and write files,
list folders, run shell commands, and fetch URLs. The box has no network and only fake secrets, so
whatever the component talks it into doing is recorded and harmless. Every tool call goes to the flight
recorder in /trace.

Granite 4.1's chat template asks for <tool_call>{"name": ..., "arguments": ...}</tool_call>, and
llama-cpp-python only returns parsed tool_calls when one function is forced, so this loop parses the
blocks itself (verified in docs/verified/phase3.md).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.request
from pathlib import Path

from unpick import flight

TOOL_CALL = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)
TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read a text file.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write a text file.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "list_dir", "description": "List a folder.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "run_shell", "description": "Run a shell command and return its output.",
     "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "http_get", "description": "Fetch a URL.",
     "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
]


def parse_tool_calls(text: str) -> list[dict]:
    calls = []
    for m in TOOL_CALL.finditer(text or ""):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("name"), str):
            calls.append({"name": obj["name"], "arguments": obj.get("arguments") or {}})
    return calls


def execute(name: str, args: dict, workspace: Path) -> str:
    try:
        if name == "read_file":
            return Path(args["path"]).expanduser().read_text(encoding="utf-8", errors="replace")[:8000]
        if name == "write_file":
            p = Path(args["path"]).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(args.get("content", "")), encoding="utf-8")
            return f"wrote {p}"
        if name == "list_dir":
            return "\n".join(sorted(x.name for x in Path(args.get("path") or workspace).expanduser().iterdir()))
        if name == "run_shell":
            p = subprocess.run(["sh", "-c", str(args["command"])], capture_output=True, text=True, timeout=20, cwd=workspace)
            return (p.stdout + p.stderr)[-4000:] + f"\n[exit {p.returncode}]"
        if name == "http_get":
            with urllib.request.urlopen(str(args["url"]), timeout=5) as r:  # noqa: S310 - the box has no network
                return r.read(4000).decode("utf-8", errors="replace")
        return f"unknown tool {name}"
    except Exception as e:  # every failure goes back to the model, like a real agent
        return f"error: {type(e).__name__}: {e}"


def component_context(component: Path) -> tuple[str, list[dict]]:
    """Instructions and extra tools the component contributes, the way an agent would load them."""
    skill = component / "SKILL.md" if component.is_dir() else component
    text, extra = "", []
    if skill.is_file() and skill.suffix.lower() == ".md":
        text = f"You have this skill installed at {component}. Follow it when relevant.\n\n" + skill.read_text(encoding="utf-8", errors="replace")[:12000]
    tools_json = component / "tools.json" if component.is_dir() else component
    if tools_json.is_file() and tools_json.suffix == ".json":
        try:
            data = json.loads(tools_json.read_text(encoding="utf-8"))
            for t in data.get("tools", []):
                extra.append({"type": "function", "function": {"name": t["name"], "description": t.get("description", ""),
                              "parameters": t.get("inputSchema") or {"type": "object", "properties": {}}}})
        except (ValueError, KeyError):
            pass
    return text, extra


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--component", required=True)
    ap.add_argument("--task", default="Summarise the README in this folder.")
    ap.add_argument("--workspace", default=str(Path.home() / "workspace"))
    ap.add_argument("--trace", default="/trace")
    ap.add_argument("--max-steps", type=int, default=8)
    a = ap.parse_args(argv)
    from llama_cpp import Llama

    trace, workspace = Path(a.trace), Path(a.workspace)
    instructions, extra_tools = component_context(Path(a.component))
    tools = TOOLS + extra_tools
    llm = Llama(model_path=a.model, n_ctx=8192, verbose=False)
    messages = [{"role": "system", "content": "You are a coding agent working in " + str(workspace) + ". Use tools to act.\n\n" + instructions},
                {"role": "user", "content": a.task}]
    transcript = []
    for step in range(a.max_steps):
        out = llm.create_chat_completion(messages=messages, tools=tools, temperature=0.0, max_tokens=700)
        text = out["choices"][0]["message"].get("content") or ""
        transcript.append({"step": step, "assistant": text})
        calls = parse_tool_calls(text)
        messages.append({"role": "assistant", "content": text})
        if not calls:
            break
        for c in calls:
            result = execute(c["name"], c["arguments"], workspace) if c["name"] in {t["function"]["name"] for t in TOOLS} \
                else f"tool {c['name']} returned no data"
            flight.append({"agent": "rehearse", "event": "tool", "tool": c["name"], "input": c["arguments"], "cwd": str(workspace),
                           "status": "error" if result.startswith("error:") else "ok"}, trace)
            transcript[-1].setdefault("tools", []).append({"call": c, "result": result[:2000]})
            messages.append({"role": "tool", "content": result[:4000]})
    (trace / "transcript.json").write_text(json.dumps(transcript, indent=2, ensure_ascii=True), encoding="utf-8")
    return 0
