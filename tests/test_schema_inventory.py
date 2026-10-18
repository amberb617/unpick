import json
from pathlib import Path

import jsonschema

from runthrough import inventory, scan
from runthrough.resources import load_json, schemas_dir


def test_findings_match_schema(kit):
    schema = json.loads((schemas_dir() / "finding.schema.json").read_text(encoding="utf-8"))
    res = scan.scan(kit, decision_files=[])
    assert res.findings
    for f in res.findings:
        jsonschema.validate(f.to_dict(), schema)


def test_judge_schema_is_valid_json_schema():
    jsonschema.Draft202012Validator.check_schema(json.loads((schemas_dir() / "judge.schema.json").read_text(encoding="utf-8")))


def test_every_location_cites_a_source():
    for loc in load_json("locations.json"):
        assert loc["source"] and loc["scope"] in ("user", "project") and set(loc["os"]) <= {"mac", "linux", "windows"}
        assert isinstance(loc["verified"], bool)


def _fake_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".claude" / "skills" / "tidy").mkdir(parents=True)
    (home / ".claude" / "skills" / "tidy" / "SKILL.md").write_text("---\nname: tidy-pdf\n---\nBODY SECRET\n", encoding="utf-8")
    (home / ".cursor").mkdir()
    (home / ".cursor" / "mcp.json").write_text(
        '{\n // comment\n "mcpServers": {"fs": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"], '
        '"env": {"TOKEN": "s3cret"}},}\n}', encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return home


def test_inventory_finds_skills_and_mcp_without_leaking_env(tmp_path, monkeypatch):
    _fake_home(tmp_path, monkeypatch)
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
    items = inventory.discover(project=proj)
    kinds = {(c["kind"], c["name"]) for c in items}
    assert ("skill", "tidy-pdf") in kinds and ("mcp-server", "fs") in kinds
    assert any(c["kind"] in ("instructions-file", "rules-file") and c["name"] == "AGENTS.md" for c in items)
    blob = json.dumps(items)
    assert "s3cret" not in blob and "BODY SECRET" not in blob
    fs = next(c for c in items if c["name"] == "fs")
    assert fs["provenance"].startswith("npx -y @modelcontextprotocol/server-filesystem") and len(fs["sha256"]) == 64


def test_directory_hash_changes_with_content(tmp_path):
    d = tmp_path / "s"
    d.mkdir()
    (d / "a").write_text("1", encoding="utf-8")
    h1 = inventory.sha256_dir(d)
    (d / "a").write_text("2", encoding="utf-8")
    assert inventory.sha256_dir(d) != h1


def test_jsonc_comments_and_trailing_commas():
    assert json.loads(inventory.strip_jsonc('{"a": "x//y", /* c */ "b": [1,2,],}')) == {"a": "x//y", "b": [1, 2]}


def test_empty_target_is_an_error_not_clean(tmp_path):
    res = scan.scan(tmp_path, decision_files=[])
    assert res.exit_code == 2 and res.errors
