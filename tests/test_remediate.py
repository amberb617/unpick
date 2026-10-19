"""Quarantine, restore and clean: what happens after a flag."""

from __future__ import annotations

import json

import pytest

from tests.test_schema_inventory import _fake_home
from unpick import clean, isolate, recover, scan, watch
from unpick.cli import main


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = _fake_home(tmp_path, monkeypatch)
    monkeypatch.setattr(isolate, "ROOT", h / ".unpick" / "quarantine")
    return h


def test_skill_round_trip(home, tmp_path):
    skill = home / ".claude" / "skills" / "tidy"
    [c] = recover.find_component("tidy-pdf", tmp_path)
    r = isolate.isolate(c, reason="test")
    assert not skill.exists() and (isolate.ROOT / r["id"] / "files" / "tidy" / "SKILL.md").is_file()
    assert [x["id"] for x in isolate.isolated()] == [r["id"]]
    assert "moved" in isolate.restore(r["id"])
    assert (skill / "SKILL.md").is_file() and isolate.isolated() == []


def test_mcp_entry_round_trip_keeps_a_backup(home, tmp_path):
    cfg = home / ".cursor" / "mcp.json"
    [c] = [x for x in recover.find_component("fs", tmp_path) if x["kind"] == "mcp-server"]
    r = isolate.isolate(c)
    assert json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"] == {}
    assert list(cfg.parent.glob("mcp.json.unpick-backup-*"))
    isolate.restore(r["id"])
    assert json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["fs"]["command"] == "npx"


def test_restore_refuses_to_overwrite(home, tmp_path):
    [c] = recover.find_component("tidy-pdf", tmp_path)
    r = isolate.isolate(c)
    (home / ".claude" / "skills" / "tidy").mkdir()
    with pytest.raises(isolate.CannotIsolate, match="exists again"):
        isolate.restore(r["id"])


def test_recover_contain_uses_quarantine(home, tmp_path):
    [c] = recover.find_component("tidy-pdf", tmp_path)
    [msg] = recover.contain(c, tmp_path / "incident-x")
    assert "unpick restore isolated-" in msg and isolate.isolated()[0]["reason"].startswith("recover")


def test_clean_copy_of_sample_a(kit):
    r = clean.clean(kit / "sample-a")
    cleaned = (kit / "sample-a.unpick-clean" / "SKILL.md").read_text(encoding="utf-8")
    assert clean.MARKER in cleaned and "base64 -d | bash" not in cleaned
    assert not any(0xE0000 <= ord(c) <= 0xE007F for c in cleaned)
    assert (kit / "sample-a" / "SKILL.md").read_text(encoding="utf-8") != cleaned  # original untouched
    left = {f["rule_id"] for f in r["still_flagged"]}
    assert "RT-UNICODE" not in left and "RT-ENCODED-EXEC" not in left
    assert "RT-PREREQ" in left  # a persuasive setup step is prose: reported, never silently rewritten
    assert (kit / "sample-a.unpick-clean" / "CLEANUP.md").is_file()


def test_clean_keeps_comments_inside_code_fences():
    text = "intro <!-- hidden --> text\n```html\n<!-- shown in a code block -->\n```\n"
    out, changes = clean.clean_text(text, markdown=True, script=False)
    assert "hidden" not in out and "<!-- shown in a code block -->" in out and changes


def test_clean_refuses_to_overwrite(kit):
    clean.clean(kit / "sample-b")
    with pytest.raises(FileExistsError):
        clean.clean(kit / "sample-b")


def test_watch_quarantines_only_when_asked(home, kit, monkeypatch, tmp_path):
    monkeypatch.setattr(watch, "LOG", tmp_path / "watch.log")
    monkeypatch.setattr(watch, "notify", lambda t, b: None)
    e = watch.scan_and_report(kit / "sample-b", quarantine_at="high")  # only a low note: stays put
    assert "quarantined" not in e and (kit / "sample-b").exists()
    e = watch.scan_and_report(kit / "sample-a", quarantine_at="high")
    assert e["quarantined"].startswith("isolated-") and not (kit / "sample-a").exists()


def test_cli_quarantine_list_and_restore(home, kit, capsys):
    assert main(["quarantine", str(kit / "sample-a"), "--json"]) == 0
    rid = json.loads(capsys.readouterr().out)["id"]
    assert main(["quarantine", "--list", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["id"] == rid
    assert main(["restore", rid, "--json"]) == 0 and (kit / "sample-a" / "SKILL.md").is_file()
    assert scan.scan(kit / "sample-a", decision_files=[]).findings
