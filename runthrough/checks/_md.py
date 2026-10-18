"""Small Markdown helpers shared by checks: which section a line sits in, and whether it is in a code fence."""

from __future__ import annotations

import re

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s{0,3}(```|~~~)")


def walk(lines: list[str]):
    """Yield (line_no, line, current_heading, in_fence) for every line."""
    heading, fence = "", None
    for n, line in enumerate(lines, 1):
        m = FENCE.match(line)
        if m:
            if fence is None:
                fence = m.group(1)
                yield n, line, heading, True
                continue
            if m.group(1) == fence:
                fence = None
                yield n, line, heading, True
                continue
        if fence is None:
            h = HEADING.match(line)
            if h:
                heading = h.group(2)
        yield n, line, heading, fence is not None
