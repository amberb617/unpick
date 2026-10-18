"""Run YARA-X through its Python package and print the same JSON shape as `yr scan --output-format json`."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yara_x


def main(rules: str, target: str) -> None:
    compiled = yara_x.compile(Path(rules).read_text(encoding="utf-8"))
    files = [Path(target)] if Path(target).is_file() else [p for p in sorted(Path(target).rglob("*")) if p.is_file()]
    matches = []
    for f in files:
        res = yara_x.Scanner(compiled).scan(f.read_bytes())
        for r in res.matching_rules:
            matches.append({
                "rule": r.identifier, "file": str(f.resolve()), "meta": dict(r.metadata),
                "strings": [{"identifier": p.identifier, "offset": m.offset} for p in r.patterns for m in p.matches],
            })
    print(json.dumps({"matches": matches}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
