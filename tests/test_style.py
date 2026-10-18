"""Code gate that ruff does not cover: no nested conditional expressions (Sonar S3358)."""

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "unpick"


def test_no_nested_ternaries():
    offenders = []
    for p in PKG.rglob("*.py"):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.IfExp) and any(isinstance(n, ast.IfExp) for n in ast.walk(node.body)) or (
                isinstance(node, ast.IfExp) and isinstance(node.orelse, ast.IfExp)
            ):
                offenders.append(f"{p.relative_to(PKG.parent)}:{node.lineno}")
    assert not offenders, offenders
