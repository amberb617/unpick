import json

from unpick.cli import main


def test_exit_codes(kit, tmp_path, capsys):
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "SKILL.md").write_text("---\nname: tidy\n---\n# Tidy\nSummarise the file.\n", encoding="utf-8")
    assert main(["scan", str(clean), "--no-decisions", "--json"]) == 0
    assert main(["scan", str(kit / "sample-a"), "--no-decisions", "--json"]) == 1
    assert main(["scan", str(tmp_path / "missing"), "--json"]) == 2
    assert main(["scan", str(clean), "--no-decisions", "--json", "--backends", "no-such-scanner"]) == 3


def test_scan_json_shape(kit, capsys):
    main(["scan", str(kit / "tools.json"), "--no-decisions", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["summary"]["network_calls"] == [] and d["sources"] == ["builtin"]
    assert all(f["agreed_by"] == ["builtin"] for f in d["findings"])


def test_raw_json(kit, capsys):
    assert main(["raw", str(kit / "sample-a" / "SKILL.md"), "--json"]) == 1
    rows = json.loads(capsys.readouterr().out)
    assert rows[23]["differs"] and "\\u{E0041}" in rows[23]["raw"]


def test_every_command_has_json_and_no_color():
    from unpick.cli import build_parser
    sub = next(a for a in build_parser()._actions if a.dest == "cmd")
    for name, parser in sub.choices.items():
        opts = {o for a in parser._actions for o in a.option_strings}
        assert {"--json", "--no-color"} <= opts, name
