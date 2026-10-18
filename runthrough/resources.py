"""Locate the data/ and schemas/ folders, whether installed as a wheel or run from a checkout."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

_PKG = Path(__file__).resolve().parent
_REPO = _PKG.parent


def _pick(installed: str, repo: str) -> Path:
    p = _PKG / installed
    return p if p.exists() else _REPO / repo


def data_dir() -> Path:
    return _pick("_data", "data")


def schemas_dir() -> Path:
    return _pick("_schemas", "schemas")


@cache
def load_json(name: str):
    return json.loads((data_dir() / name).read_text(encoding="utf-8"))


@cache
def load_list(name: str) -> tuple[tuple[str, str], ...]:
    """Read a one-entry-per-line data file. Returns (entry, source comment) pairs.

    Format: `entry  # source or reason`. Blank lines and lines starting with # are skipped.
    """
    out = []
    for raw in (data_dir() / name).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entry, _, comment = line.partition("#")
        out.append((entry.strip(), comment.strip()))
    return tuple(out)
