"""AI agents in CI that strangers can steer: a GitHub Actions workflow that runs Claude, Gemini or Codex on
issues, comments or pull requests from anyone.

Clinejection (2026-02): Cline's issue-triage workflow ran Claude on `issues` with
`allowed_non_write_users: "*"` and Bash allowed, and a crafted issue title made it install an imposter
commit. "Comment and Control" (2026-04 to 08, CVE-2026-54316): PR titles, issue bodies and hidden HTML
comments hijacked Claude Code, Gemini CLI and the Copilot agent in Actions and read their tokens.
Gemini CLI GHSA-wpqr-6v78-jr5g (CVSS 10): headless runs trusted the workspace and --yolo ignored the tool
allowlist, https://github.com/google-github-actions/run-gemini-cli/security/advisories/GHSA-wpqr-6v78-jr5g .
Sources in docs/research/2026-10-landscape.md.
"""

from __future__ import annotations

import re

import yaml

from unpick.checks import Hit

RULE_ID = "RT-CI-AGENT"
TITLE = "AI agent in CI that strangers can steer"
SEVERITY = "medium"
WHY = "This workflow runs an AI agent on events anyone can create, such as an issue or a comment, so a stranger's text becomes the agent's instructions inside your CI with your tokens."
FALSE_POSITIVE = "Agent workflows limited to maintainers, with read-only tools and no secrets, are a reasonable design; check who can trigger it and what the agent may do."

AGENT_ACTIONS = ("anthropics/claude-code-action", "google-github-actions/run-gemini-cli", "openai/codex-action",
                 "github/copilot")
AGENT_RUN = re.compile(r"\b(claude\s+(-p|--print)\b|gemini\s+(-p|--prompt|--yolo)\b|codex\s+exec\b)")
STRANGER_EVENTS = {"issues", "issue_comment", "pull_request_target", "discussion", "discussion_comment",
                   "pull_request_review_comment"}
UNTRUSTED_EXPR = re.compile(r"\$\{\{\s*github\.(event\.(issue\.(title|body)|comment\.body|pull_request\.(title|body)|"
                            r"review\.body|discussion\.(title|body))|head_ref)\s*\}\}")
YOLO = re.compile(r"--yolo\b|--dangerously-skip-permissions\b|--dangerously-bypass-approvals-and-sandbox\b")
BARE_BASH = re.compile(r"(?<![\w(])Bash(?!\s*\()")
GEMINI_FIXED = (0, 39, 1)


def applies(doc):
    p = doc.path.as_posix()
    return "/.github/workflows/" in p and doc.name.endswith((".yml", ".yaml"))


def _triggers(data) -> set[str]:
    on = data.get("on", data.get(True))  # YAML 1.1 reads a bare `on:` key as True
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return set(map(str, on))
    if isinstance(on, dict):
        return set(map(str, on))
    return set()


def _line(doc, needle: str, default: int = 1) -> int:
    return next((n for n, line in enumerate(doc.lines, 1) if needle in line), default)


def _version(v: str) -> tuple[int, ...] | None:
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", str(v))
    return tuple(int(x) for x in m.groups()) if m else None


def _agent_steps(data):
    for job in (data.get("jobs") or {}).values() if isinstance(data.get("jobs"), dict) else []:
        for step in job.get("steps") or [] if isinstance(job, dict) else []:
            if not isinstance(step, dict):
                continue
            uses, run = str(step.get("uses", "")), str(step.get("run", ""))
            if uses.startswith(AGENT_ACTIONS) or AGENT_RUN.search(run):
                yield step, uses or run.strip().splitlines()[0][:60]


def _step_hits(doc, step, name):
    w = step.get("with") if isinstance(step.get("with"), dict) else {}
    blob = " ".join(str(v) for v in [*w.values(), step.get("run", "")])
    if w.get("allowed_non_write_users"):
        yield Hit(_line(doc, "allowed_non_write_users"), f"{name}: allowed_non_write_users lets people without write access trigger the agent", "high")
    tools = " ".join(str(w.get(k, "")) for k in ("allowed_tools", "claude_args", "settings"))
    if BARE_BASH.search(tools):
        yield Hit(_line(doc, "Bash"), f"{name}: Bash is allowed with no command pattern, so the agent can run anything", "high")
    if m := YOLO.search(blob):
        yield Hit(_line(doc, m.group(0)), f"{name}: {m.group(0)} turns off the agent's approvals", "high")
    if m := UNTRUSTED_EXPR.search(blob):
        yield Hit(_line(doc, m.group(0)[:20]), f"{name}: puts {m.group(0)} (text anyone can write) straight into the agent's input", "high")
    ver = _version(w.get("gemini_cli_version", ""))
    if ver and ver < GEMINI_FIXED:
        yield Hit(_line(doc, "gemini_cli_version"), f"{name}: gemini_cli_version {'.'.join(map(str, ver))} predates the GHSA-wpqr-6v78-jr5g fix (0.39.1)", "high")


def run(doc):
    try:
        data = yaml.safe_load(doc.text)
    except yaml.YAMLError:
        return
    if not isinstance(data, dict):
        return
    open_to = sorted(_triggers(data) & STRANGER_EVENTS)
    for step, name in _agent_steps(data):
        hits = list(_step_hits(doc, step, name))
        if open_to:
            yield Hit(_line(doc, name[:30]), f"{name} runs on {', '.join(open_to)}, which anyone can trigger",
                      "high" if hits else SEVERITY, {"triggers": open_to})
        yield from hits
