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


def test_no_literal_invisible_characters_in_source():
    """A tool that hunts hidden Unicode must not carry any. Write \\u escapes, never the characters."""
    from unpick.checks.hidden_unicode import classify

    root = PKG.parent
    skip = ("tests/fixtures/", "tests/adversarial/", "unpick/demo_kit/", "demo/", ".venv/", ".git/", ".unpick/")
    offenders = []
    for p in root.rglob("*"):
        rel = p.relative_to(root).as_posix()
        if not p.is_file() or rel.startswith(skip) or p.suffix not in (".py", ".ps1", ".sh", ".md", ".json", ".js", ".css", ".html", ".yml", ".yar"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        offenders += [f"{rel}: U+{ord(c):04X}" for c in set(text) if classify(ord(c)) and c not in "\t\n\r"]
    assert not offenders, offenders
