"""Terminal view of one scan: header, TL;DR, collapsed groups, coverage and next steps (unpick.digest).

The default view fits a long scan on about one screen. `--details` lists every finding under its group;
`--rule` and `--severity` filter and say "Showing X of N". Severity words are always printed, so the view
reads without colour, on Windows consoles and in a pipe.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import textwrap
from pathlib import Path

from rich.cells import cell_len
from rich.markup import escape as esc

from unpick import digest
from unpick.render import escape as raw_escape

SEV_STYLE = {"high": "bold red", "medium": "yellow", "low": "cyan", "info": "dim"}
INDENT = "    "


def _clip(text: str, width: int) -> str:
    """One display line: invisible characters shown as \\u{...}, cut by display cells with "..." when cut."""
    s = " ".join(raw_escape(text).split())
    if cell_len(s) <= width:
        return s
    out = ""
    for ch in s:
        if cell_len(out + ch) > width - 3:
            break
        out += ch
    return out + "..."


def _target(d: dict) -> str:
    t = d.get("target", "")
    home = str(Path.home())
    return "~" + t[len(home):] if t.startswith(home) else t


def _para(console, text: str, prefix: str = "") -> None:
    """A sentence block that wraps under its own indent instead of falling back to column 0. A command in
    backticks moves to its own line and is never wrapped, so it can be copied as printed."""
    width = max(40, min(console.width, 100))
    cmds = re.findall(r"`([^`]+)`", text)
    text = re.sub(r"`[^`]+`", "the command below", text) if cmds else text
    console.print(esc(textwrap.fill(prefix + text, width, initial_indent=INDENT, subsequent_indent=INDENT)))
    for cmd in cmds:
        console.print(f"{INDENT}  {esc(cmd)}", soft_wrap=True)


def shell_quote(arg: str) -> str:
    """Quote one argument for the shell a reader pastes into: POSIX quoting, or Windows double quotes
    (cmd.exe does not treat single quotes as quoting)."""
    if os.name == "nt":
        return subprocess.list2cmdline([arg])
    return shlex.quote(arg)


def _runnable(text: str, d: dict, path: str) -> str:
    """Catalog advice names `<file>`; give the reader the real file so the command runs as printed."""
    target = Path(d.get("target", ""))
    full = target if target.is_file() else target / path  # a single-file scan, or a folder that may since be gone
    try:
        shown = full.resolve().relative_to(Path.cwd().resolve())  # shorter when you are inside the scanned folder
    except ValueError:
        shown = full
    return text.replace("<file>", shell_quote(str(shown)))


def _lines(lines: list[int]) -> str:
    return ",".join(str(n) for n in lines if n) or "-"


def render(console, d: dict, *, details: bool = False, rule: str | None = None, severity: str | None = None,
           summary: list[str] | None = None, summary_label: str = "", saved: bool = False,
           headline: str | None = None, lead: bool = True, where: str | None = None) -> None:
    full = digest.build(d)
    if headline:
        full["headline"] = headline
    shown = [f for f in d.get("findings", []) if (not rule or f["rule_id"] == rule)
             and (not severity or f["severity"] == severity) and (not where or digest.place(f["path"]) == where)]
    filtered = bool(rule or severity or where)
    if filtered:
        full["headline"] = full["headline"].split("; run ")[0] + "."  # the next step names the whole scan's top rule
    view = digest.build({**d, "findings": shown}) if filtered else full
    _header(console, d, full, saved, lead)
    if filtered:
        console.print(f"Showing {len(shown)} of {full['open']} findings ({esc(', '.join(x for x in (rule, severity, where) if x))}).")
    for title, lines in ((summary_label, summary or []), ("TL;DR", view["tldr"])):
        if lines:
            console.print(f"\n[bold]{esc(title)}[/]")
            width = max(40, min(console.width, 100))
            for line in lines:
                console.print(esc(textwrap.fill(line, width, initial_indent="  - ", subsequent_indent="    ")))
    gs = view["groups"]
    if gs:
        console.print(f"\n[bold]Findings: {len(gs)} group{'s' * (len(gs) != 1)}[/]")
    width = max(40, min(console.width, 100) - len(INDENT) - 2)
    for i, g in enumerate(gs, 1):
        _group(console, i, g, details, width, d)
    _coverage(console, full["coverage"])
    if gs and not details:
        console.print("\n[bold]Next[/]")
        console.print(f"{INDENT}unpick results --details")
        console.print(f"{INDENT}unpick show {gs[0].example['id']}")


def _header(console, d: dict, full: dict, saved: bool, lead: bool) -> None:
    cov, p = full["coverage"], console.print
    if lead:  # first line: what to do
        width = max(40, min(console.width, 100))
        p(esc(textwrap.fill(full["headline"], width, subsequent_indent="  ", break_on_hyphens=False)), style="bold")
    p(f"Scan: {esc(_target(d))}" + (f"  [dim](saved {esc(d.get('started_at', '')[:16])})[/]" if saved else ""))
    p(f"Open: {full['open']} ({esc(full['counts'])}). Accepted: {full['accepted']}. "
      f"{cov['files_read']} file{'s' * (cov['files_read'] != 1)} read, {cov['not_read']} not read.")
    p(f"Checks: {esc(', '.join(cov['sources']))}. Network: {esc('; '.join(cov['network']) or 'none')}.")
    if d.get("files"):
        p("This is not a safety verdict.", style="dim")


def _group(console, i: int, g, details: bool, width: int, d: dict) -> None:
    p = console.print
    p(f"\n[{SEV_STYLE[g.worst]}][{i}] {esc(g.mix)}.[/] [bold]{esc(g.title.rstrip('.'))}[/]")
    p(f"{INDENT}{g.rule_id}, {g.place}")
    _para(console, g.what_it_means)
    if details:
        for f in g.findings:
            p(f"{INDENT}[{SEV_STYLE[f['severity']]}]{f['severity']:<6}[/] {esc(raw_escape(f['path']))}:{f.get('line') or '-'}"
              f"  [dim]id {f['id']}[/]")
            p(f"{INDENT}  {esc(_clip(f['message'], width - 2))}")
            if f.get("matched"):
                p(f"{INDENT}  [dim]> {esc(_clip(f['matched'], width - 4))}[/]")
        p(f"{INDENT}[dim]May be legitimate when: {esc(g.findings[0].get('false_positive', ''))}[/]")
    else:
        files = list(g.files.items())
        for path, lines in files[:digest.MAX_FILES]:
            p(f"{INDENT}{esc(raw_escape(path))}:{_lines(lines)}", overflow="fold")
        if len(files) > digest.MAX_FILES:
            rest = files[digest.MAX_FILES:]
            p(f"{INDENT}and {sum(len(v) for _, v in rest)} more in {len(rest)} file{'s' * (len(rest) != 1)}.")
        ex = g.example
        p(f"{INDENT}Example, {esc(raw_escape(ex['path']))}:{ex.get('line') or '-'}:")
        p(f"{INDENT}[dim]> {esc(_clip(ex.get('matched') or ex['message'], width - 2))}[/]")
    if g.hint:
        _para(console, g.hint, "Hint: ")
    _para(console, _runnable(g.what_to_do, d, g.example["path"]), "Next: ")
    if not details:
        p(f"{INDENT}[dim]Expand: unpick results --details --rule {g.rule_id} --place {g.place}[/]")


def _coverage(console, cov: dict) -> None:
    p = console.print
    p("\n[bold]Coverage[/]")
    for err in cov["errors"]:
        _para(console, err, "Check incomplete: ")
    for src in cov["unavailable"]:
        _para(console, src, "Not available: ")
    for reason, paths in cov["not_read_by_reason"].items():
        more = f" and {len(paths) - 3} more" if len(paths) > 3 else ""
        p(f"{INDENT}Not read ({esc(reason)}): {esc(', '.join(raw_escape(x) for x in paths[:3]))}{more}.")
    if cov["not_read"]:
        p(f"{INDENT}Unread is not checked. To list every one: unpick results --json  (the \"skipped\" list)")
    elif not cov["errors"] and not cov["unavailable"]:
        p(f"{INDENT}Every file found was read.")
