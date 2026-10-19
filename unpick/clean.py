"""`unpick clean <path>`: write a cleaned copy of an add-on, removing what is never legitimate.

The original is never changed. The copy, next to it as `<name>.unpick-clean` (or `--out`), has:
  * every invisible character removed (zero-width, bidirectional controls, Unicode tag characters), the
    trick behind the Rules File Backdoor;
  * HTML comments removed from Markdown outside code blocks, since a viewer never shows them;
  * every line that decodes or downloads code and runs it in one step (the ClawHavoc and Zenity lures)
    disabled in place, with a visible marker saying what was removed.

Anything subtler (a poisoned tool description, a persuasive instruction, a look-alike name) cannot be
cleaned reliably by rewriting text, so it is left alone and reported by the rescan of the copy. A cleaned
copy is a starting point for review, not a certificate.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from unpick import scan
from unpick.checks._md import FENCE
from unpick.checks.encoded_execution import PIPES
from unpick.checks.hidden_unicode import hidden_positions

MARKER = "[unpick removed a command that decodes or downloads code and runs it]"
COMMENT = re.compile(r"<!--.*?-->", re.S)
SCRIPT_SUFFIX = {".sh", ".bash", ".zsh", ".ps1", ".psm1", ".bat", ".cmd", ".py", ".js", ".mjs"}


def _strip_invisible(line: str) -> tuple[str, int]:
    drop = set(hidden_positions(line))
    return "".join(c for i, c in enumerate(line) if i not in drop), len(drop)


def _runs_code(line: str) -> bool:
    return any(rx.search(line) for rx, _ in PIPES)


def clean_text(text: str, markdown: bool, script: bool) -> tuple[str, list[str]]:
    """Return (cleaned text, list of changes). Pure function, used by the tests."""
    changes: list[str] = []
    if markdown:
        # Remove HTML comments only outside code fences.
        out_lines, buf, fence = [], [], None
        for line in text.split("\n"):
            m = FENCE.match(line)
            if m and fence is None:
                if buf:
                    out_lines.append(_drop_comments("\n".join(buf), changes))
                    buf = []
                fence = m.group(1)
                out_lines.append(line)
            elif fence is not None:
                out_lines.append(line)
                if m and m.group(1) == fence:
                    fence = None
            else:
                buf.append(line)
        if buf:
            out_lines.append(_drop_comments("\n".join(buf), changes))
        text = "\n".join(out_lines)
    lines = text.split("\n")
    for n, line in enumerate(lines):
        fixed, removed = _strip_invisible(line)
        if removed:
            changes.append(f"line {n + 1}: removed {removed} invisible character(s)")
        if _runs_code(fixed):
            prefix = "# " if script or not markdown else ""
            fixed = f"{prefix}{MARKER}"
            changes.append(f"line {n + 1}: disabled a decode-or-download-and-run command")
        lines[n] = fixed
    return "\n".join(lines), changes


def _drop_comments(block: str, changes: list[str]) -> str:
    found = COMMENT.findall(block)
    if found:
        changes.append(f"removed {len(found)} hidden HTML comment(s)")
    return COMMENT.sub("", block)


def clean(target: Path, out: Path | None = None) -> dict:
    target = target.resolve()
    dest = out or target.with_name(target.name + ".unpick-clean")
    if dest.exists():
        raise FileExistsError(f"{dest} already exists; remove it or pass --out")
    if target.is_dir():
        shutil.copytree(target, dest, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
    _, files, _ = scan.walk(dest)
    report: dict[str, list[str]] = {}
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        is_md = f.suffix.lower() in (".md", ".mdc", ".markdown") or f.name.lower() in (".cursorrules", ".clinerules")
        new, changes = clean_text(text, is_md, f.suffix.lower() in SCRIPT_SUFFIX)
        if changes:
            f.write_text(new, encoding="utf-8")
            report[f.relative_to(dest).as_posix() if dest.is_dir() else f.name] = changes
    res = scan.scan(dest, decision_files=[])
    left = [f.to_dict() for f in res.findings]
    note = dest / "CLEANUP.md" if dest.is_dir() else dest.with_name(dest.name + ".CLEANUP.md")
    body = ["# What unpick cleaned", "", f"Original: {target}", "", "The original was not changed.", ""]
    for rel, changes in report.items():
        body += [f"## {rel}", ""] + [f"- {c}" for c in changes] + [""]
    body += ["## Still flagged after cleaning", ""]
    body += [f"- {f['severity']} {f['rule_id']} {f['path']}:{f['line']}: {f['message']}" for f in left] or ["- Nothing."]
    body += ["", "A cleaned copy is a starting point for review, not a certificate."]
    note.write_text("\n".join(body) + "\n", encoding="utf-8")
    return {"original": str(target), "clean": str(dest), "changes": report, "still_flagged": left, "report": str(note)}
