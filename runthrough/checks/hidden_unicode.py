"""Hidden Unicode: characters a human never sees but a model reads.

Zero-width characters, bidirectional controls and Unicode tag characters can carry instructions that
are invisible in an editor, a rendered README and a pull-request diff. Pillar Security showed this in
Cursor and Copilot rules files ("Rules File Backdoor", 2025):
https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents
Tag characters (U+E0000..U+E007F) map one-to-one onto ASCII, so a whole sentence can ride along
invisibly; this check decodes them so you can read what was hidden.
"""

from __future__ import annotations

import re
import unicodedata

from runthrough.checks import Hit

RULE_ID = "RT-UNICODE"
TITLE = "Hidden Unicode"
SEVERITY = "medium"
WHY = "The file contains characters that do not show on screen but are passed to the model, which is how instructions get hidden in plain sight."
FALSE_POSITIVE = "Emoji sequences, right-to-left language text and a byte-order mark legitimately use some of these characters."

ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF, 0x180E}
BIDI = {0x061C, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069}


def classify(cp: int) -> str | None:
    if 0xE0000 <= cp <= 0xE007F:
        return "tag"
    if cp in BIDI:
        return "bidi"
    if cp in ZERO_WIDTH:
        return "zero-width"
    if 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
        return "variation-selector"
    if cp in (0x09, 0x0A, 0x0D):
        return None
    if unicodedata.category(chr(cp)) in ("Cc", "Cf", "Co", "Cn") and cp != 0xFFFD:
        return "non-printing"
    return None


def _is_pictograph(ch: str) -> bool:
    return bool(ch) and (unicodedata.category(ch) == "So" or 0x1F000 <= ord(ch) <= 0x1FAFF)


def _benign(text: str, i: int, kind: str, line_text: str) -> bool:
    prev = text[i - 1] if i else ""
    nxt = text[i + 1] if i + 1 < len(text) else ""
    cp = ord(text[i])
    if cp == 0xFEFF and i == 0:
        return True  # byte-order mark
    if kind == "variation-selector" and cp in (0xFE0E, 0xFE0F) and _is_pictograph(prev):
        return True  # emoji presentation selector
    if cp == 0x200D and _is_pictograph(prev) and _is_pictograph(nxt):
        return True  # emoji zero-width joiner sequence
    if kind == "bidi" and cp in (0x200E, 0x200F) and re.search(r"[\u0590-\u08FF]", line_text):
        return True  # direction marks inside Hebrew / Arabic text
    return False


def hidden_positions(line: str) -> list[int]:
    """Indexes of characters in `line` that are hidden and not part of a benign sequence. Shared with render.py."""
    return [i for i, ch in enumerate(line)
            if (kind := classify(ord(ch))) and ch != "\t" and not _benign(line, i, kind, line)]


LATIN = re.compile(r"[A-Za-z]")
CONFUSABLE = re.compile(r"[\u0370-\u03FF\u0400-\u04FF]")  # Greek and Cyrillic look-alikes
WORD = re.compile(r"[^\W\d_][\w-]{2,}", re.UNICODE)


def run(doc):
    text = doc.text
    byte_offset = 0
    line_no, line_start = 1, 0
    lines = doc.lines
    by_line: dict[int, list[dict]] = {}
    for i, ch in enumerate(text):
        if ch == "\n":
            line_no += 1
            line_start = i + 1
        cp = ord(ch)
        kind = classify(cp) if cp > 0x7F or cp < 0x20 else None
        if kind and not _benign(text, i, kind, lines[line_no - 1] if line_no <= len(lines) else ""):
            by_line.setdefault(line_no, []).append({
                "codepoint": f"U+{cp:04X}", "kind": kind, "byte_offset": byte_offset,
                "column": i - line_start + 1, "name": unicodedata.name(ch, "UNASSIGNED"),
            })
        byte_offset += len(ch.encode("utf-8", errors="surrogatepass"))

    for ln, chars in by_line.items():
        kinds = sorted({c["kind"] for c in chars})
        tags = "".join(chr(int(c["codepoint"][2:], 16) - 0xE0000) for c in chars if c["kind"] == "tag")
        extra = {"characters": chars}
        msg = f"{len(chars)} hidden character(s) on this line: {', '.join(kinds)}"
        if tags:
            decoded = "".join(t for t in tags if t.isprintable())
            extra["decoded_tags"] = decoded
            msg += f"; tag characters spell: {decoded!r}"
        sev = "high" if {"tag", "bidi"} & set(kinds) else SEVERITY
        yield Hit(ln, msg, sev, extra)

    for n, line in enumerate(lines, 1):
        for m in WORD.finditer(line):
            w = m.group()
            if LATIN.search(w) and CONFUSABLE.search(w):
                yield Hit(n, f"identifier {w!r} mixes Latin with Greek/Cyrillic look-alike letters", "medium",
                          {"identifier": w, "column": m.start() + 1})
