"""The collapsed scan view (DECISIONS.md, "Scan output"): grouping, the on-device summary's limits, and the
commands it prints."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from rich.console import Console

from unpick import cli, digest, scan_output, summary


def f(rule, sev, path, line, fid=None, matched="x"):
    return {"rule_id": rule, "severity": sev, "path": path, "line": line, "id": fid or f"{rule}{path}{line}",
            "message": "m", "matched": matched, "why": "w.", "false_positive": "fp.", "source": "builtin",
            "agreed_by": ["builtin"], "context": [{"line": line, "text": matched}]}


def scan_dict(findings, **kw):
    return {"target": "/tmp/addon", "started_at": "2026-10-25T10:00", "files": ["a"] * 10, "findings": findings,
            "accepted": [], "skipped": [], "errors": [], "unavailable": [], "runs": [], "sources": ["builtin"],
            "summary": {"open": len(findings), "accepted": 0, "network_calls": []}, **kw}


def render(d, **kw):
    c = Console(width=100, record=True, no_color=True)
    scan_output.render(c, d, **kw)
    return c.export_text()


def test_groups_split_by_file_type_and_order_most_serious_first():
    gs = digest.groups([f("RT-SENSITIVE-PATH", "medium", "README.md", 1), f("RT-SENSITIVE-PATH", "medium", "a.py", 2),
                        f("RT-UNICODE", "high", "SKILL.md", 3), f("RT-SECRECY", "low", "x.toml", 4)])
    assert [(g.rule_id, g.place) for g in gs] == [("RT-UNICODE", "docs/config"), ("RT-SENSITIVE-PATH", "code"),
                                                  ("RT-SENSITIVE-PATH", "docs/config"), ("RT-SECRECY", "docs/config")]


def test_example_prefers_the_plain_readme():
    [g] = digest.groups([f("RT-RENDER-DIVERGE", "low", p, 78) for p in ("README.es.md", "README.ko.md", "README.md")])
    assert g.example["path"] == "README.md"


def test_tldr_says_how_much_it_left_out():
    gs = digest.groups([f(f"RT-X{i}", "low", f"{i}.md", 1) for i in range(7)])
    lines = digest.tldr(gs)
    assert len(lines) == 6 and lines[-1] == "2 more groups, 2 findings."


def test_default_view_collapses_and_never_says_safe():
    d = scan_dict([f("RT-SENSITIVE-PATH", "medium", f"f{i}.md", i) for i in range(30)])
    out = render(d)
    assert out.count("f1.md") == 1 and "and 26 more in 26 files." in out
    assert "This is not a safety verdict." in out and "Expand: unpick results --details --rule RT-SENSITIVE-PATH" in out
    for word in ("safe.", "benign", "harmless"):
        assert word not in out.replace("not a safety verdict", "")


def test_details_and_filters_say_what_they_show():
    d = scan_dict([f("RT-SECRECY", "low", "a.md", 1, "id1"), f("RT-UNICODE", "high", "b.md", 2, "id2")])
    out = render(d, details=True, rule="RT-SECRECY")
    assert "Showing 1 of 2 findings (RT-SECRECY)." in out and "id id1" in out and "id2" not in out


def test_a_command_in_advice_gets_its_own_unwrapped_line():
    d = scan_dict([f("RT-RENDER-DIVERGE", "low", "deep/" * 12 + "README.md", 5)])
    from pathlib import Path
    line = next(x for x in render(d).splitlines() if "unpick raw" in x)
    expected = scan_output.shell_quote(str(Path("/tmp/addon") / ("deep/" * 12 + "README.md")))
    assert line.strip() == f"unpick raw {expected}"  # one line, quoted for this platform's shell


def test_summary_statements_come_from_records_only():
    d = scan_dict([f("RT-SECRECY", "low", "a.md", 1), f("RT-SECRECY", "low", "b.py", 2), f("RT-UNICODE", "medium", "c.md", 3)],
                  skipped=[{"path": "x.png", "reason": "not a text format"}])
    st = summary.statements(d)
    assert st["no_high"].startswith("No finding is high") and st["mostly_low"] == "2 of the 3 findings are low."
    assert st["unread"] == "1 file was not read, so it was not checked."
    assert "builtin_only" in st and "code_and_docs" in st
    assert all("safe." not in v.replace("not the same as safe.", "") for v in st.values())


def test_summary_keeps_only_known_picks_and_drops_the_rest():
    d = scan_dict([f("RT-SECRECY", "low", "a.md", 1), f("RT-UNICODE", "high", "b.md", 2)])
    seen = {}

    def model(prompt, schema):
        seen["schema"], seen["prompt"] = schema, prompt
        return json.dumps({"picks": ["high_where", "builtin_only"]})
    lines, note = summary.pick(d, model)
    assert lines[0].startswith("The 1 high finding sit") and note == ""
    assert set(seen["schema"]["properties"]["picks"]["items"]["enum"]) == set(summary.statements(d))
    assert "m" not in seen["prompt"].split("\n")  # finding messages never reach the model
    lines, note = summary.pick(d, lambda p, s: json.dumps({"picks": ["made_up"]}))
    assert lines == [] and "outside unpick's statements" in note


def test_summary_failure_leaves_the_view_intact():
    import subprocess
    d = scan_dict([f("RT-SECRECY", "low", "a.md", 1), f("RT-UNICODE", "high", "b.md", 2)])
    def slow(p, s):
        raise subprocess.TimeoutExpired("apple-fm", 20)
    assert summary.pick(d, slow) == ([], "On-device summary skipped: TimeoutExpired.")


@pytest.mark.parametrize("args,tty,expected", [
    (SimpleNamespace(json=False, no_summary=False), True, True),
    (SimpleNamespace(json=True, no_summary=False), True, False),
    (SimpleNamespace(json=False, no_summary=True), True, False),
    (SimpleNamespace(json=False, no_summary=False), False, False),  # pipes never call the model
])
def test_summary_is_on_by_default_only_in_a_terminal(args, tty, expected, monkeypatch):
    monkeypatch.delenv("UNPICK_NONINTERACTIVE", raising=False)
    monkeypatch.setattr("sys.stdout.isatty", lambda: tty)
    assert summary.wanted(args) is expected


def test_results_and_show_read_the_saved_scan(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["results"]) == 2 and "no saved scan here" in capsys.readouterr().err
    (tmp_path / ".unpick").mkdir()
    (tmp_path / ".unpick" / "last-scan.json").write_text(json.dumps(scan_dict([f("RT-SECRECY", "low", "a.md", 7, "abc")])))
    assert cli.main(["results", "--no-summary"]) == 0 and "(saved 2026-10-25T10:00)" in capsys.readouterr().out
    assert cli.main(["show", "abc"]) == 0
    out = capsys.readouterr().out
    assert ">     7 | x" in out and "unpick decide abc accept" in out
    assert cli.main(["show", "nope"]) == 2


def test_check_saves_its_scan_for_results_and_decide(tmp_path, monkeypatch, capsys):
    from unpick import check
    monkeypatch.chdir(tmp_path)
    d = scan_dict([f("RT-SECRECY", "low", "a.md", 1, "abc")])
    monkeypatch.setattr(check, "run", lambda *a, **k: {"scan": d, "ref": "r", "id": "q", "root": "/tmp/q",
                                                      "provenance": {}, "network": [], "questions": [], "provenance_error": None})
    cli.main(["check", "r"])
    assert json.loads((tmp_path / ".unpick" / "last-scan.json").read_text())["findings"][0]["id"] == "abc"


def test_example_prefers_a_line_that_acts_over_one_that_describes():
    gs = digest.groups([f("RT-SENSITIVE-PATH", "medium", "judge.py", 13, matched="Judge: key from ../../ dotenv file."),
                        f("RT-SENSITIVE-PATH", "medium", "judge.py", 20, matched="# load the key file"),
                        f("RT-SENSITIVE-PATH", "medium", "judge.py", 43, matched="for line in (ROOT / KEYS).read_text():")])
    assert gs[0].example["line"] == 43


def test_no_high_caveat_is_always_in_the_summary():
    d = scan_dict([f("RT-SECRECY", "low", "a.md", 1), f("RT-SENSITIVE-PATH", "medium", "b.py", 2)])
    lines, _ = summary.pick(d, lambda p, s: json.dumps({"picks": ["builtin_only", "code_and_docs"]}))
    assert lines[0] == "No finding is high. That is not the same as safe." and len(lines) == 3


def test_headline_says_no_high_not_none_serious():
    out = render(scan_dict([f("RT-SECRECY", "low", "a.md", 1)]))
    flat = " ".join(out.split())
    assert "no high ones (not the same as safe)" in flat and "none serious" not in flat


def test_place_filter_and_expand_commands_keep_code_and_docs_apart():
    d = scan_dict([f("RT-SENSITIVE-PATH", "medium", "a.py", 1, "c1"), f("RT-SENSITIVE-PATH", "medium", "b.md", 2, "d1")])
    out = render(d)
    assert "--rule RT-SENSITIVE-PATH --place code" in out and "--rule RT-SENSITIVE-PATH --place docs/config" in out
    out = render(d, details=True, where="code")
    assert "Showing 1 of 2 findings (code)." in out and "id c1" in out and "id d1" not in out
    assert "run `unpick explain" not in " ".join(out.split())  # a filtered view does not point at the whole scan's rule


def test_show_prints_each_decision_as_its_own_command(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".unpick").mkdir()
    (tmp_path / ".unpick" / "last-scan.json").write_text(json.dumps(scan_dict([f("RT-SECRECY", "low", "a.md", 7, "abc")])))
    cli.main(["show", "abc"])
    out = capsys.readouterr().out.splitlines()
    for choice in ("accept", "reject", "ask-author"):
        assert f"  unpick decide abc {choice}" in out
    assert "Scan of /tmp/addon" in "\n".join(out)
