"""Quarantine, restore and clean: what happens after a flag."""

from __future__ import annotations

import json
from pathlib import Path

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


def test_jsonc_with_comments_is_never_rewritten(home, tmp_path):
    cfg = home / ".cursor" / "mcp.json"
    before = cfg.read_bytes()
    [c] = [x for x in recover.find_component("fs", tmp_path) if x["kind"] == "mcp-server"]
    with pytest.raises(isolate.CannotIsolate, match="comments"):
        isolate.isolate(c)
    assert cfg.read_bytes() == before


def test_mcp_entry_round_trip_keeps_a_backup(home, tmp_path):
    cfg = home / ".cursor" / "mcp.json"
    cfg.write_text(json.dumps({"mcpServers": {"fs": {"command": "npx", "args": ["-y", "x"]}, "keep": {"command": "y"}}}), encoding="utf-8")
    [c] = [x for x in recover.find_component("fs", tmp_path) if x["kind"] == "mcp-server"]
    r = isolate.isolate(c)
    assert list(json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]) == ["keep"]
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


def test_clean_copy_of_sample_a(kit, tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "CLEANED", tmp_path / "cleaned")
    r = clean.clean(kit / "sample-a")
    assert r["clean"].startswith(str(tmp_path / "cleaned"))  # outside every agent folder
    cleaned = (Path(r["clean"]) / "SKILL.md").read_text(encoding="utf-8")
    assert clean.MARKER in cleaned and "base64 -d | bash" not in cleaned
    assert not any(0xE0000 <= ord(c) <= 0xE007F for c in cleaned)
    assert (kit / "sample-a" / "SKILL.md").read_text(encoding="utf-8") != cleaned  # original untouched
    left = {f["rule_id"] for f in r["still_flagged"]}
    assert "RT-UNICODE" not in left and "RT-ENCODED-EXEC" not in left
    assert "RT-PREREQ" in left  # a persuasive setup step is prose: reported, never silently rewritten
    assert (Path(r["clean"]) / "CLEANUP.md").is_file()


def test_clean_drops_symlinks(kit, tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "CLEANED", tmp_path / "cleaned")
    (kit / "sample-b" / "secrets").symlink_to(Path.home())
    r = clean.clean(kit / "sample-b")
    assert not (Path(r["clean"]) / "secrets").exists() and r["links_removed"]


def test_clean_keeps_comments_inside_code_fences():
    text = "intro <!-- hidden --> text\n```html\n<!-- shown in a code block -->\n```\n"
    out, changes = clean.clean_text(text, markdown=True, script=False)
    assert "hidden" not in out and "<!-- shown in a code block -->" in out and changes


def test_clean_refuses_to_overwrite(kit, tmp_path):
    clean.clean(kit / "sample-b", tmp_path / "out")
    with pytest.raises(FileExistsError):
        clean.clean(kit / "sample-b", tmp_path / "out")


def test_watch_quarantines_only_installed_add_ons(home, kit, monkeypatch, tmp_path):
    import shutil
    monkeypatch.setattr(watch, "LOG", tmp_path / "watch.log")
    monkeypatch.setattr(watch, "notify", lambda t, b: None)
    e = watch.scan_and_report(kit / "sample-a", quarantine_at="high")  # not an installed add-on folder
    assert "quarantine_skipped" in e and (kit / "sample-a").exists()
    installed = home / ".claude" / "skills" / "pdf-tidy"
    shutil.copytree(kit / "sample-a", installed)
    e = watch.scan_and_report(installed / "SKILL.md", quarantine_at="high")
    assert e["quarantined"].startswith("isolated-") and not installed.exists()
    assert (home / ".claude" / "skills" / "tidy").exists()  # the neighbour skill is untouched


def test_symlinked_skill_moves_the_link_not_the_target(home, tmp_path):
    target = tmp_path / "Documents"
    target.mkdir()
    (target / "taxes.pdf").write_text("x", encoding="utf-8")
    link = home / ".claude" / "skills" / "linky"
    link.symlink_to(target)
    r = isolate.isolate({"path": str(link), "name": "linky"})
    assert (target / "taxes.pdf").is_file() and r["was_symlink"] and not link.exists()


def test_restore_rejects_path_tricks(home):
    for bad in ("../../etc", "isolated-x/../../y", ""):
        with pytest.raises(isolate.CannotIsolate):
            isolate.restore(bad)


def test_cli_quarantine_list_and_restore(home, kit, capsys):
    assert main(["quarantine", str(kit / "sample-a"), "--json"]) == 0
    rid = json.loads(capsys.readouterr().out)["id"]
    assert main(["quarantine", "--list", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["id"] == rid
    assert main(["restore", rid, "--json"]) == 0 and (kit / "sample-a" / "SKILL.md").is_file()
    assert scan.scan(kit / "sample-a", decision_files=[]).findings


def test_hook_is_matched_by_content_not_position(home, tmp_path):
    cfg = home / ".claude" / "settings.json"
    good = {"matcher": "Edit", "hooks": [{"type": "command", "command": "prettier --write"}]}
    bad = {"hooks": [{"type": "command", "command": "node .claude/setup.mjs"}]}
    cfg.write_text(json.dumps({"hooks": {"SessionStart": [good, bad]}}), encoding="utf-8")
    r = isolate.isolate({"path": f"{cfg}#SessionStart.1", "kind": "hook", "name": "SessionStart"},
                        hook_json=json.dumps(bad, sort_keys=True))
    assert json.loads(cfg.read_text(encoding="utf-8"))["hooks"]["SessionStart"] == [good]
    isolate.restore(r["id"])
    assert bad in json.loads(cfg.read_text(encoding="utf-8"))["hooks"]["SessionStart"]


def test_per_project_mcp_server_in_claude_json_is_removed(home):
    cfg = home / ".claude.json"
    cfg.write_text(json.dumps({"projects": {"/w": {"mcpServers": {"evil": {"command": "x"}}}}, "mcpServers": {"evil": {"command": "x"}}}),
                   encoding="utf-8")
    isolate.isolate({"path": f"{cfg}#evil", "kind": "mcp-server", "name": "evil"})
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["mcpServers"] == {} and data["projects"]["/w"]["mcpServers"] == {}
