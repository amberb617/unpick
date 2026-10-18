import json

from runthrough import decisions, scan
from runthrough.cli import main


def test_sample_a_has_exactly_three_planted_lines(kit):
    res = scan.scan(kit / "sample-a", decision_files=[])
    assert {f.line for f in res.findings} == {14, 17, 24}
    assert {"RT-PREREQ", "RT-ENCODED-EXEC", "RT-UNICODE"} <= {f.rule_id for f in res.findings}


def test_sample_a_domains_are_all_example_invalid(kit):
    import re
    text = (kit / "sample-a" / "SKILL.md").read_text(encoding="utf-8")
    hidden = "".join(chr(ord(c) - 0xE0000) for c in text if 0xE0000 <= ord(c) <= 0xE007F)
    for domain in re.findall(r"@?((?:[a-z0-9-]+\.)+[a-z]{2,})\b", text + " " + hidden):
        if "." in domain and not domain.endswith((".md", ".pdf")):
            assert domain.endswith("example.invalid"), domain


def test_sample_b_is_one_low_false_positive(kit):
    res = scan.scan(kit / "sample-b", decision_files=[])
    assert [(f.rule_id, f.severity) for f in res.findings] == [("RT-SENSITIVE-PATH", "low")]


def test_demo_kit_passes_once_planted_findings_are_accepted(kit):
    res = scan.scan(kit, decision_files=[kit / "accepted.decisions.json"])
    assert res.findings == [] and res.accepted and res.exit_code == 0


def test_changed_line_fires_again(kit):
    skill = kit / "sample-a" / "SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8").replace("helper installer", "helper installer now"), encoding="utf-8")
    res = scan.scan(kit, decision_files=[kit / "accepted.decisions.json"])
    assert [f.line for f in res.findings] == [14]


def test_decide_by_id_round_trip(kit, monkeypatch):
    monkeypatch.chdir(kit)
    assert main(["scan", "sample-b", "--no-decisions", "--json"]) == 1
    last = json.loads((kit / ".runthrough" / "last-scan.json").read_text(encoding="utf-8"))
    fid = last["findings"][0]["id"]
    assert main(["decide", fid, "accept", "--note", "warns against committing secrets"]) == 0
    assert main(["scan", "sample-b", "--json"]) == 0
    stored = json.loads(decisions.project_file(kit).read_text(encoding="utf-8"))["decisions"][0]
    assert stored["decision"] == "accept" and stored["note"].startswith("warns")


def test_reject_and_ask_author_keep_finding_open(kit, monkeypatch):
    monkeypatch.chdir(kit)
    main(["scan", "sample-b", "--no-decisions", "--json"])
    main(["decide", "--rule", "RT-SENSITIVE-PATH", "ask-author"])
    res = scan.scan(kit / "sample-b", decision_files=[decisions.project_file(kit)])
    assert res.findings[0].decision == "ask-author" and res.exit_code == 1
