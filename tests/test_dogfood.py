"""unpick scan . on this repository passes with zero unaccepted findings."""

from pathlib import Path

from unpick import scan

ROOT = Path(__file__).resolve().parents[1]


def test_repo_scans_clean(monkeypatch):
    monkeypatch.chdir(ROOT)  # .unpickignore counts only for the current directory
    res = scan.scan(ROOT, decision_files=[ROOT / ".unpick" / "decisions.json"])
    assert not res.errors
    assert not res.findings, "\n".join(f"{f.path}:{f.line} {f.rule_id} {f.message}" for f in res.findings[:30])
