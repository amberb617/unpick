"""Rendered vs raw: what a Markdown viewer shows you, line by line, next to what the model actually reads.

This is deterministic and deliberately simple. It does not try to be a full CommonMark renderer; it
models the specific ways a renderer hides text: HTML comments, invisible characters, collapsed
<details> blocks, hidden HTML, link text that names a different place than the link goes, reference
definitions, and text pushed off-screen by a long run of spaces (a trick used in Invariant Labs'
WhatsApp proof of concept, https://github.com/invariantlabs-ai/mcp-injection-experiments).

The same rows drive the terminal view, the --json output and the UI's split view.
"""

from __future__ import annotations

import re
import shlex
import unicodedata
from dataclasses import asdict, dataclass, field

from unpick.checks._md import FENCE
from unpick.checks.hidden_unicode import classify, hidden_positions

COMMENT_OPEN, COMMENT_CLOSE = "<!--", "-->"
LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REFDEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s+\S+")
HIDDEN_HTML = re.compile(r"<(\w+)[^>]*(style\s*=\s*\"[^\"]*(display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0)[^\"]*\"|hidden\b)[^>]*>.*?</\1>", re.I)
TAG = re.compile(r"</?[A-Za-z][^>]*>")
OFFSCREEN = re.compile(r"\S {40,}[^\s|]")  # a padded table cell ends in "|", hidden text does not
TABLE_ROW = re.compile(r"^\s*([|:+]).*\1\s*$")  # pipe and grid table rows pad their cells with spaces
DOMAINISH = re.compile(r"(?:[a-z0-9-]+\.)+[a-z]{2,}", re.I)
# "classify.md" or "Next.js" in a link label is a file or framework name, not a website, even though .md is a
# country domain. Measured 2026-10-25: every link-mismatch high on installed add-ons had a label like these.
FILE_NAME = re.compile(r"\.(md|mdc|markdown|mjs|cjs|js|jsx|ts|tsx|py|ipynb|json|ya?ml|toml|txt|sh|html?|css|rs|go|rb|java|kt|swift|cpp|c|h|sql|csv|lock)$", re.I)


@dataclass
class Row:
    line: int
    raw: str  # escaped: every invisible or non-ASCII control shown as \u{XXXX}
    rendered: str  # what a reader would see; "" when the whole line is hidden
    differs: bool
    reasons: list[str] = field(default_factory=list)


def escape(s: str) -> str:
    """Show every invisible character explicitly. This is the Python equivalent of `cat -v`, cross-platform."""
    out = []
    for ch in s:
        cp = ord(ch)
        if ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif classify(cp) or (cp < 0x20) or cp == 0x7F:
            out.append(f"\\u{{{cp:04X}}}")
        else:
            out.append(ch)
    return "".join(out)


def _visible(s: str) -> str:
    drop = set(hidden_positions(s))
    return "".join(ch for i, ch in enumerate(s) if i not in drop)


def _strip_md(s: str) -> str:
    s = re.sub(r"^\s{0,3}#{1,6}\s+", "", s)
    s = re.sub(r"^\s{0,3}>\s?", "", s)
    s = re.sub(r"(\*\*|__)(.+?)\1", r"\2", s)
    s = re.sub(r"(?<![*\w])([*_])(?!\s)(.+?)(?<!\s)\1(?![*\w])", r"\2", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"[image: \1]", s)
    return s


class _State:
    """What carries over from one line to the next: an open HTML comment, an open <details> block."""

    def __init__(self) -> None:
        self.fence: str | None = None
        self.in_comment = False
        self.details_depth = 0
        self.summary_seen = False


def _strip_comments(line: str, st: _State, reasons: list[str]) -> str:
    shown, i = "", 0
    while i < len(line):
        if st.in_comment:
            j = line.find(COMMENT_CLOSE, i)
            end = len(line) if j < 0 else j
            if line[i:end].strip():
                reasons.append("inside an HTML comment")
            if j < 0:
                break
            st.in_comment, i = False, j + len(COMMENT_CLOSE)
        else:
            j = line.find(COMMENT_OPEN, i)
            if j < 0:
                shown += line[i:]
                break
            shown += line[i:j]
            st.in_comment, i = True, j + len(COMMENT_OPEN)
    if COMMENT_OPEN in line and "inside an HTML comment" not in reasons:
        reasons.append("inside an HTML comment")
    return shown


def _details(shown: str, st: _State, reasons: list[str]) -> tuple[str, bool]:
    """Returns (text still shown, whether the whole line is collapsed)."""
    low = shown.lower()
    collapsed = False
    if "<details" in low:
        st.details_depth += 1
        st.summary_seen = False
    if st.details_depth and "<summary" in low:
        st.summary_seen = True
        m = re.search(r"<summary[^>]*>(.*?)</summary>", shown, re.I)
        shown = m.group(1) if m else ""
    elif st.details_depth and st.summary_seen and shown.strip() and "</details" not in low:
        reasons.append("inside a collapsed <details> block")
        collapsed = True
    if "</details" in low:
        st.details_depth = max(0, st.details_depth - 1)
    return shown, collapsed


def _same_site(label: str, host: str) -> bool:
    """The link goes where its label says: the same host or a subdomain of it. A substring test let
    "github.com" pass for github.com.evil.test."""
    label, host = label.lower().removeprefix("www."), host.lower().removeprefix("www.")
    return host == label or host.endswith("." + label)


def _links(shown: str, reasons: list[str]) -> str:
    def swap(m):
        label, href = m.group(1), m.group(2)
        ld, hd = DOMAINISH.search(label), DOMAINISH.search(href)
        if ld and hd and not FILE_NAME.search(ld.group(0)) and not _same_site(ld.group(0), hd.group(0)):
            reasons.append(f"link text says {ld.group(0)} but points to {hd.group(0)}")
        return label

    return LINK.sub(swap, shown)


def _fenced_row(n: int, raw_line: str, st: _State) -> Row | None:
    """Inside a code fence a renderer shows text verbatim, so only invisible characters can hide anything."""
    m = FENCE.match(raw_line)
    if st.fence is None and not st.in_comment and m:
        st.fence = m.group(1)
    elif st.fence is not None and m and m.group(1) == st.fence:
        st.fence = None
    elif st.fence is None:
        return None
    visible = _visible(raw_line)
    reasons = [_invisible_reason(raw_line)] if visible != raw_line else []
    rendered = "" if m else visible.rstrip()  # a renderer draws the fence, not its backticks
    return Row(n, escape(raw_line), rendered, bool(reasons), reasons)


def _invisible_reason(line: str) -> str:
    tags = "".join(chr(ord(c) - 0xE0000) for c in line if 0xE0020 <= ord(c) <= 0xE007E)
    return f"invisible characters; tag characters spell: {tags!r}" if tags else "invisible characters"


def _row(n: int, raw_line: str, st: _State) -> Row:
    fenced = _fenced_row(n, raw_line, st)
    if fenced:
        return fenced
    reasons: list[str] = []
    shown = _strip_comments(raw_line, st, reasons)
    visible = _visible(shown)
    if visible != shown:
        reasons.append(_invisible_reason(shown))
    shown, collapsed = _details(visible, st, reasons)
    if HIDDEN_HTML.search(shown):
        reasons.append("hidden HTML element")
        shown = HIDDEN_HTML.sub("", shown)
    if REFDEF.match(shown):
        reasons.append("link reference definition (not rendered)")
        shown = ""
    shown = _links(shown, reasons)
    if OFFSCREEN.search(shown) and not shown.lstrip().startswith("|") and not TABLE_ROW.match(shown):
        reasons.append("text pushed off-screen by a long run of spaces")
        shown = re.sub(r" {40,}", "  ", shown)
    if st.in_comment and not reasons:
        reasons.append("inside an HTML comment")
    rendered = "" if collapsed else _strip_md(TAG.sub("", shown)).rstrip()
    reasons = list(dict.fromkeys(reasons))
    return Row(n, escape(raw_line), rendered, bool(reasons), reasons)


def rows(text: str) -> list[Row]:
    st = _State()
    return [_row(n, line, st) for n, line in enumerate(text.splitlines(), 1)]


def to_json(text: str) -> list[dict]:
    return [asdict(r) for r in rows(text)]


def non_ascii_names(s: str) -> list[str]:
    return [f"U+{ord(c):04X} {unicodedata.name(c, '?')}" for c in s if ord(c) > 0x7F]


def finding_groups(findings: list[dict]) -> list[tuple]:
    """Group findings by plain title, with the most serious group first."""
    from unpick.explain import UNKNOWN_EXPLANATION, get_explanation

    order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    groups = {}
    for finding in sorted(findings, key=lambda f: order[f["severity"]]):
        try:
            entry = get_explanation(finding["rule_id"])
        except KeyError:
            entry = UNKNOWN_EXPLANATION
        groups.setdefault(entry.title, []).append((entry, finding))
    return list(groups.items())



def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" + ("" if number == 1 else "s")


def _run_incomplete(run: dict, findings: list[dict]) -> bool:
    if run.get("status") != "ran":
        return True
    code = run.get("exit_code")
    # Jiffy documents 2 as block and 1 as unverified. Other adapters commonly
    # use 1 for findings; without any evidence from that source it is inconclusive.
    if run.get("source") == "backend:jiffy":
        return code not in (None, 0, 2)
    if code not in (None, 0, 1):
        return True
    return code == 1 and not any(f["source"] == run.get("source") for f in findings)

def scan_verdict(d: dict, *, questions: bool = False, provenance_error: bool = False) -> str:
    """Describe evidence, never equate missing work or accepted findings with safety.

    Counts are findings, not independent attacks: two rules can flag the same line.
    Commands are read-only and contain no untrusted file paths to paste into a shell.
    """
    findings = d.get("findings", [])
    all_findings = findings + d.get("accepted", [])
    if not d.get("files"):
        return "Cannot assess this: no files were scanned; run `unpick scan --help` to choose a readable file or folder."
    failed = (d.get("errors") or d.get("unavailable") or provenance_error
              or any(f["rule_id"] == "RT-JUDGE-FAILED" for f in all_findings)
              or any(_run_incomplete(r, all_findings) for r in d.get("runs", [])))
    if failed:
        return ("Don't install this yet: checks are incomplete; run `unpick scan --help` "
                "and resolve the missing checks listed below before retrying.")
    if findings:
        first = finding_groups(findings)[0][1][0][1]
        serious = sum(f["severity"] == "high" for f in findings)
        count = _count(serious, "serious finding") if serious else _count(len(findings), "finding") + " to review"
        return f"Don't install this yet: {count}; run `unpick explain {shlex.quote(escape(first['rule_id']))}` for the next step."
    if questions:
        return ("Don't install this yet: questions about the source need review; "
                "run `unpick check --help` and resolve the questions below before approving.")
    if d.get("accepted"):
        accepted = len(d["accepted"])
        verb = "was" if accepted == 1 else "were"
        return (f"Review your decisions: {_count(accepted, 'finding')} {verb} previously accepted, not cleared; "
                "run `unpick scan --no-decisions <path>` to see them again.")
    if d.get("skipped"):
        return ("Cannot assess the whole component: some files were not read; "
                "run `unpick scan --json <path>` to see which files need review.")
    return (f"No problems found in {_count(len(d['files']), 'scanned file')}, but safety is not guaranteed; "
            "run `unpick hook install claude-code --dry-run` to preview checks before future installs.")
