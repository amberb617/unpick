import asyncio
import json
from types import SimpleNamespace

import pytest

from tests.test_schema_inventory import _fake_home
from unpick import cli, hook, tui, watch

pytest.importorskip("textual")


def _result(exit_code=1, severities=()):
    return SimpleNamespace(exit_code=exit_code, findings=[SimpleNamespace(severity=s) for s in severities])


def test_protection_reads_the_installed_hook(tmp_path, monkeypatch):
    _fake_home(tmp_path, monkeypatch)  # has ~/.claude and ~/.cursor, not ~/.codex
    hook.apply("claude-code", install=True, dry_run=False, min_severity="medium", fail_open=True)
    rows = {r["agent"]: r for r in tui.protection()}
    assert rows["claude-code"] | {} == {**rows["claude-code"], "hooked": True, "level": "medium", "fail_open": True}
    assert rows["cursor"]["installed"] and not rows["cursor"]["hooked"]
    assert not rows["codex"]["installed"]
    assert tui.next_steps(list(rows.values()))[0].startswith("Press c")  # one agent hooked: no setup nudge


def test_next_steps_lead_with_setup_when_nothing_is_protected(tmp_path, monkeypatch):
    _fake_home(tmp_path, monkeypatch)
    assert tui.next_steps(tui.protection())[0].startswith("Press s")


@pytest.mark.parametrize("result,expected", [
    (_result(2), "not read"),  # nothing read must never show as clean
    (_result(0), "nothing found"),
    (_result(1, ["low", "high"]), "high"),
    (_result(1, ["low", "medium"]), "medium"),
])
def test_bucket_is_the_worst_open_finding(result, expected):
    assert tui.bucket(result) == expected


def test_alerts_skip_clean_and_broken_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(watch, "LOG", tmp_path / "watch.log")
    lines = [{"ts": "2026-10-24T10:00:00+00:00", "path": "/a", "open": 2, "high": 1}, "not json",
             {"ts": "2026-10-24T11:00:00+00:00", "path": "/b", "open": 0, "high": 0}]
    watch.LOG.write_text("\n".join(x if isinstance(x, str) else json.dumps(x) for x in lines), encoding="utf-8")
    assert [e["path"] for e in tui.alerts()] == ["/a"]


def test_bars_show_every_bucket_with_its_count():
    text = tui.bars({"high": 3, "nothing found": 6}).plain
    assert all(b in text for b in tui.BUCKETS) and " 3\n" in text and " 0\n" in text


def test_home_screen_scans_every_place_once(tmp_path, monkeypatch):
    from unpick import tui_app

    home = _fake_home(tmp_path, monkeypatch)
    skill, cfg = home / ".claude" / "skills" / "tidy", home / ".cursor" / "mcp.json"
    items = [{"path": str(skill), "kind": "skill", "host": "claude-code", "name": "tidy", "display_path": "~/tidy"},
             {"path": str(cfg), "kind": "mcp-server", "host": "cursor", "name": "fs", "display_path": "~/mcp.json"},
             {"path": str(cfg), "kind": "mcp-server", "host": "cursor", "name": "git", "display_path": "~/mcp.json"}]
    monkeypatch.setattr(tui_app.inventory, "discover", lambda project: items)
    handed = []
    monkeypatch.setattr(tui_app, "hand_over", lambda app, argv: handed.append(argv))
    scanned = []
    def scanner(p):
        scanned.append(p)
        return _result(1, ["high"]) if p == skill else _result(2)

    async def go():
        app = tui_app.Home(scanner=scanner)
        async with app.run_test(size=(110, 34)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            body = str(app.query_one("#addons-body").render())
            assert "3 add-ons in 2 places" in body and "Nothing found is not the same as safe." in body
            assert app.results == {str(cfg): "not read", str(skill): "high"}
            await pilot.press("i")
            assert app.screen.query_one("DataTable").row_count == 3
            await pilot.press("enter")  # worst first: the skill with a high finding
            assert handed[-1] == ["scan", str(skill)]
            await pilot.press("escape")
            assert app.screen is app.screen_stack[0]
            await pilot.press("s")
            assert handed[-1] == ["setup"]

    asyncio.run(go())
    assert sorted(scanned) == sorted([skill, cfg])


def test_bare_unpick_without_a_terminal_prints_help(capsys):
    assert cli.main([]) == 0 and "usage: unpick" in capsys.readouterr().out
