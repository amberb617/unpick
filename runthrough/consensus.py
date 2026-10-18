"""Where sources agree and disagree.

Scanners disagree far more than people expect: in a benchmark of five open-source skill scanners on
100 malicious and 100 benign skills, pairwise agreement ranged from 0.01 to 0.21. This module reports
"agreed by N of M" per finding and a pairwise agreement matrix, without editorialising.
"""

from __future__ import annotations

from itertools import combinations

TOLERANCE = 2  # lines


def annotate(findings, sources: list[str]) -> None:
    """Fill `agreed_by` on every finding: the sources that fired on the same file within TOLERANCE lines."""
    by_path: dict[str, list] = {}
    for f in findings:
        by_path.setdefault(f.path, []).append(f)
    for group in by_path.values():
        for f in group:
            f.agreed_by = sorted({g.source for g in group if abs(g.line - f.line) <= TOLERANCE})


def _spots(findings, source):
    return {(f.path, f.line) for f in findings if f.source == source}


def _near(spot, others) -> bool:
    return any(spot[0] == o[0] and abs(spot[1] - o[1]) <= TOLERANCE for o in others)


def matrix(findings, sources: list[str]) -> dict:
    """Pairwise agreement between every two sources that ran: the share of their flagged (file, line)
    spots that the other source also flagged within TOLERANCE lines. None when neither flagged anything."""
    out = {}
    for a, b in combinations(sources, 2):
        sa, sb = _spots(findings, a), _spots(findings, b)
        total = len(sa) + len(sb)
        agreed = sum(_near(s, sb) for s in sa) + sum(_near(s, sa) for s in sb)
        out[f"{a} ~ {b}"] = round(agreed / total, 2) if total else None
    return out


def totals(findings, sources: list[str]) -> dict:
    return {s: sum(f.source == s for f in findings) for s in sources}
