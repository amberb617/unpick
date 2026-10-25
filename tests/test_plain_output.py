import json
from dataclasses import asdict

import pytest

from unpick import backends, check, cli, judges, report, scan
from unpick.explain import get_explanation
from unpick.finding import Finding
from unpick.render import scan_verdict


def result(**kwargs):
    return scan.ScanResult(target="sample", started_at="fixed", sources=["builtin"], files=["SKILL.md"], **kwargs)


def finding(rule="RT-UNICODE", severity="high"):
    return Finding(rule, "builtin", severity, "SKILL.md", 2, "detail", "reason", "exception")


@pytest.mark.parametrize("args", [
    {"errors": ["scanner timed out"]},
    {"unavailable": ["backend:missing"]},
    {"runs": [{"source": "backend:extra", "status": "parse error"}]},
    {"runs": [{"source": "backend:extra", "status": "not applicable"}]},
    {"findings": [finding("RT-JUDGE-FAILED", "info")]},
    {"accepted": [finding("RT-JUDGE-FAILED", "info")]},
])
def test_incomplete_checks_never_look_clean(args, capsys):
    d = result(**args).to_dict()
    cli._print_scan(d)
    output = capsys.readouterr().out
    assert "checks are incomplete" in output.splitlines()[0]
    assert "No problems found" not in output
    assert "No findings" not in report.scan_html(d)
    assert "checks are incomplete" in report.scan_html(d)


def test_empty_and_unread_scans(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["scan", "."]) == 2
    out = capsys.readouterr().out
    assert out.startswith("Cannot assess this: no files were scanned;")
    assert "No problems found" not in out
    (tmp_path / "program.wasm").write_bytes(b"\0wasm")
    assert cli.main(["scan", "."]) == 1
    out = capsys.readouterr().out
    assert out.startswith("Cannot assess this: no files were scanned;")
    assert "This file could not be checked" in out


def test_verdict_and_grouping(kit, monkeypatch, capsys):
    monkeypatch.chdir(kit)
    assert cli.main(["scan", "sample-a", "--no-decisions"]) == 1
    out = capsys.readouterr().out
    assert out.splitlines()[0] == (
        "Don't install this yet: 4 serious findings; run `unpick explain RT-PREREQ` for the next step.")
    assert out.count("Setup asks you to run extra code") == 1
    assert out.index("SKILL.md:14") < out.index("SKILL.md:17") < out.index("Runs code you cannot read first")
    assert "  high RT-UNICODE  SKILL.md:24" in out


def test_low_finding_and_accepted_are_not_passes(kit, monkeypatch, capsys):
    monkeypatch.chdir(kit)
    assert cli.main(["scan", "sample-b", "--no-decisions"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("Don't install this yet: 1 finding to review;")
    assert "Private files or keys are mentioned" in out
    assert cli.main(["scan", "sample-b", "--decisions", "accepted.decisions.json"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Review your decisions: 1 finding was previously accepted, not cleared;")
    assert "No problems found" not in out


def test_clean_and_partial_coverage(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# A plain description\n")
    assert cli.main(["scan", "."]) == 0
    assert capsys.readouterr().out.startswith("No problems found in 1 scanned file, but safety is not guaranteed;")
    (tmp_path / "image.png").write_bytes(b"image")
    assert cli.main(["scan", "."]) == 0
    assert capsys.readouterr().out.startswith("Cannot assess the whole component: some files were not read;")


@pytest.mark.parametrize("command", ["scan", "check"])
def test_auto_judge_warning_follows_incomplete_verdict(command, monkeypatch, capsys):
    res = result()
    monkeypatch.setattr(judges, "default_judge", lambda: None)
    monkeypatch.setattr(scan, "scan", lambda *a, **kw: res)
    monkeypatch.setattr(scan, "save_last", lambda r: None)
    monkeypatch.setattr(check, "run", lambda *a, **kw: metadata(res))
    assert cli.main([command, ".", "--judge", "auto"]) == 0
    output = capsys.readouterr().out
    assert "checks are incomplete" in output.splitlines()[0]
    assert "on-device AI reviewer" in output
    assert "No problems found" not in output


def metadata(res):
    return {"scan": res.to_dict(), "ref": "sample", "id": "sample-id", "root": "sample",
            "provenance": {}, "network": [], "questions": [], "provenance_error": None}


@pytest.mark.parametrize("changes", [
    {"questions": ["Who made this?"]}, {"provenance_error": "Lookup failed"},
])
def test_check_source_questions_prevent_clean_verdict(changes, capsys):
    data = {**metadata(result()), **changes}
    cli._print_check(data)
    out = capsys.readouterr().out
    assert out.startswith("Don't install this yet:")
    assert "No problems found" not in out
    assert "Approve:" not in out


def test_check_leads_with_scan_verdict(monkeypatch, capsys):
    data = metadata(result(findings=[finding()]))
    monkeypatch.setattr(check, "run", lambda *a, **kw: data)
    assert cli.main(["check", "sample"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("Don't install this yet: 1 serious finding;")
    assert out.count("Don't install this yet") == 1
    assert "checked sample" in out


@pytest.mark.parametrize("command", ["scan", "check"])
def test_json_serialization_remains_byte_compatible(command, monkeypatch, capsys):
    res = result(findings=[finding()])
    data = res.to_dict() if command == "scan" else metadata(res)
    monkeypatch.setattr(scan, "scan", lambda *a, **kw: res)
    monkeypatch.setattr(scan, "save_last", lambda r: None)
    monkeypatch.setattr(check, "run", lambda *a, **kw: data)
    assert cli.main([command, ".", "--json"]) == 1
    assert capsys.readouterr().out == json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n"


def test_unavailable_backend_preserves_exit_code(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# Description\n")
    monkeypatch.setattr(backends, "run", lambda *a, **kw: backends.BackendRun(
        meta={"source": "backend:extra", "status": "not installed"}, unavailable=True))
    assert cli.main(["scan", ".", "--backends", "extra"]) == 3
    out = capsys.readouterr().out
    assert "checks are incomplete" in out.splitlines()[0]
    assert "No problems found" not in out


def test_explain_command(capsys):
    assert cli.main(["explain", "RT-UNICODE"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Hidden characters can conceal instructions\n")
    assert "unpick raw <file>" in out
    assert cli.main(["explain", "RT-UNICODE", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == asdict(get_explanation("RT-UNICODE"))
    assert cli.main(["explain", "RT-MISSING"]) == 2
    assert "unknown rule" in capsys.readouterr().err


def test_help_starts_with_three_workflows():
    help_text = cli.build_parser().format_help()
    start, more = help_text.split("More commands:")
    for example in ("unpick check ./downloaded-skill", "unpick scan ./my-project", "unpick hook install claude-code"):
        assert example in start
    assert "inventory" not in start and "inventory" in more
    assert "explain" in more and "==SUPPRESS==" not in more


def test_html_uses_shared_explanations_and_escapes_content():
    f = finding()
    f.message = "<script>alert(1)</script>"
    d = result(findings=[f]).to_dict()
    output = report.scan_html(d)
    entry = get_explanation(f.rule_id)
    assert f"<h3>{entry.title}</h3>" in output
    assert entry.what_it_means in output
    assert "RT-UNICODE" in output and "SKILL.md:2" in output
    assert "<script>" not in output and "&lt;script&gt;" in output
    assert "Don&#x27;t install this yet" in output


def test_empty_html_and_unknown_saved_rules():
    d = result().to_dict()
    d["files"] = []
    output = report.scan_html(d)
    assert "no files were scanned" in output
    assert "No findings" not in output
    d["findings"] = [finding("OLD-RULE").to_dict()]
    assert "This finding needs review" in report.scan_html(d)


def test_external_rule_command_is_shell_quoted():
    d = result(findings=[finding("jiffy:rule; echo unexpected")]).to_dict()
    assert "`unpick explain 'jiffy:rule; echo unexpected'`" in scan_verdict(d)


@pytest.mark.parametrize("source,code", [("backend:extra", 2), ("backend:extra", 1), ("backend:jiffy", 1)])
def test_failed_exit_without_findings_is_incomplete(source, code):
    data = result(runs=[{"source": source, "status": "ran", "exit_code": code}]).to_dict()
    assert "checks are incomplete" in scan_verdict(data)


def test_finding_exit_is_not_a_failed_scan():
    f = finding()
    f.source = "backend:extra"
    data = result(findings=[f], runs=[{"source": f.source, "status": "ran", "exit_code": 1}]).to_dict()
    assert "1 serious finding" in scan_verdict(data)


def test_missing_auto_review_is_visible_in_html(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(judges, "default_judge", lambda: None)
    monkeypatch.setattr(scan, "scan", lambda *a, **kw: result())
    monkeypatch.setattr(scan, "save_last", lambda r: None)
    output = tmp_path / "report.html"
    assert cli.main(["scan", ".", "--judge", "auto", "--html", str(output)]) == 0
    assert "checks are incomplete" in output.read_text()
    assert "No problems found" not in output.read_text()


@pytest.mark.parametrize("command", ["scan", "check"])
def test_missing_path_is_not_a_pass(command, tmp_path, capsys):
    assert cli.main([command, str(tmp_path / "missing")]) == 2
    output = capsys.readouterr().err
    assert output.startswith("Cannot assess this:")
    assert f"unpick {command} --help" in output


def test_files_not_read_are_grouped_by_reason(capsys):
    from unpick import cli

    skipped = [{"path": f"docs/{i}.md", "reason": "ignored by .unpickignore"} for i in range(40)]
    skipped.append({"path": "logo.png", "reason": "not a text format"})
    cli._print_skipped(skipped)
    out = capsys.readouterr().out
    assert out.count("Not read") == 2
    assert "Not read (ignored by .unpickignore): docs/0.md, docs/1.md, docs/2.md and 37 more" in out
    assert "Not read (not a text format): logo.png\n" in out and '"skipped"' in out
