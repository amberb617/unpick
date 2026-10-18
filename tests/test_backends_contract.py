"""Adapter contract tests against recorded scanner output, so CI needs none of the scanners installed.

Each fixture under tests/fixtures/backends/<name>/ holds the input, the raw output and meta.json with
the exact argv, version and date it was recorded (offline, network denied).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runthrough import backends
from runthrough.finding import SEVERITIES

FIX = Path(__file__).resolve().parent / "fixtures" / "backends"
CASES = {
    "cisco-skill-scanner": ("skill-scanner", "input/defanged-test-skill"),
    "cisco-mcp-scanner": ("mcp-scanner", "input/tools.json"),
    "skillspector": ("skillspector", "input/defanged-test-skill"),
    "yara-x": ("yara-x", "input/targets"),
}


def recorded(folder: str) -> str:
    d = FIX / folder
    return (d / "output.json").read_text(encoding="utf-8").replace("{FIXTURE}", d.as_posix())


@pytest.mark.parametrize("name", CASES)
def test_parse_recorded_output(name):
    folder, target = CASES[name]
    mod = backends.adapters()[name]
    found = mod.parse(recorded(folder), FIX / folder / target)
    assert found, f"{name}: recorded output parsed to zero findings"
    for f in found:
        assert f.source == f"backend:{name}" and f.severity in SEVERITIES
        assert f.original_rule_id, "keep the backend's own rule id"
        assert f.why.endswith(".") and f.false_positive.endswith(".")


@pytest.mark.parametrize("name", CASES)
def test_recorded_argv_matches_adapter(name, monkeypatch):
    folder, target = CASES[name]
    monkeypatch.setattr(backends.adapters()["yara-x"], "which", lambda cmd: f"/usr/bin/{cmd}")
    meta = json.loads((FIX / folder / "meta.json").read_text(encoding="utf-8"))
    mod = backends.adapters()[name]
    argv = mod.command(FIX / folder / target)
    assert argv[0] == meta["argv"][0]
    for flag in meta["argv"][1:]:
        if flag.startswith("-"):
            assert flag in argv, f"{name}: adapter dropped recorded flag {flag}"


def test_offline_flags_are_kept():
    assert "--no-llm" in backends.adapters()["skillspector"].command(Path("x"))
    mcp = backends.adapters()["cisco-mcp-scanner"]
    assert mcp.ENV == {"LITELLM_LOCAL_MODEL_COST_MAP": "True"}
    assert not any(a.startswith("--use-") for a in backends.adapters()["cisco-skill-scanner"].command(Path("x")))


def test_network_backends_need_online():
    rows = {r["name"]: r for r in backends.describe()}
    assert rows["skillspector"]["needs_online"] and rows["jiffy"]["needs_online"]
    assert not rows["yara-x"]["needs_online"] and not rows["cisco-skill-scanner"]["needs_online"]


def test_network_backend_refused_without_online(tmp_path, monkeypatch):
    mod = backends.adapters()["skillspector"]
    monkeypatch.setattr(mod, "version", lambda: "2.12.0")
    (tmp_path / "SKILL.md").write_text("# x\n", encoding="utf-8")
    out = backends.run("skillspector", tmp_path)
    assert out.unavailable and "needs --online" in out.meta["status"] and not out.meta["network"]


def test_every_adapter_declares_its_contract():
    for name, mod in backends.adapters().items():
        for attr in ("MAINTAINER", "LICENSE", "HOMEPAGE", "TESTED_VERSION", "NETWORK"):
            assert getattr(mod, attr), f"{name}.{attr}"
        assert isinstance(mod.NEEDS_ONLINE, bool)
        assert mod.__doc__ and "http" in mod.__doc__


def test_yara_x_falls_back_to_python_package(monkeypatch):
    mod = backends.adapters()["yara-x"]
    monkeypatch.setattr(mod, "which", lambda cmd: None)
    assert mod.command(Path("x"))[1:3] == ["-m", "runthrough.backends._yarax_runner"]
