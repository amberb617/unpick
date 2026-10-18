from __future__ import annotations

from pathlib import Path

import pytest

from unpick import demo
from unpick.checks import Doc, run_checks

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def kit(tmp_path) -> Path:
    return demo.write(tmp_path / "demo")


def findings_for(tmp_path: Path, name: str, text: str, only=None):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return run_checks(Doc.load(p, tmp_path), only)


@pytest.fixture
def check(tmp_path):
    def _run(name, text, rule=None):
        return findings_for(tmp_path, name, text, {rule} if rule else None)
    return _run
