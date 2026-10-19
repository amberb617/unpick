"""The local UI server: localhost-only guards and the same engine as the CLI."""

import pytest

pytest.importorskip("flask")

from unpick.ui.server import create_app  # noqa: E402

PORT, TOKEN = 47000, "t0ken"


@pytest.fixture
def client(kit):
    app = create_app(PORT, TOKEN, kit)
    return app.test_client()


def h(**extra):
    return {"Host": f"127.0.0.1:{PORT}", "X-Unpick-Token": TOKEN, **extra}


def test_rejects_foreign_host(client):
    assert client.get("/", headers={"Host": "evil.example"}).status_code == 403
    assert client.get("/api/meta", headers={**h(), "Host": f"attacker.test:{PORT}"}).status_code == 403


def test_api_needs_token(client):
    assert client.get("/api/meta", headers={"Host": f"127.0.0.1:{PORT}"}).status_code == 403
    assert client.get("/api/meta", headers=h(**{"X-Unpick-Token": "wrong"})).status_code == 403
    assert client.get("/api/meta", headers=h()).status_code == 200


def test_never_answers_cors_preflight(client):
    r = client.options("/api/scan", headers=h(Origin="https://evil.example", **{"Access-Control-Request-Method": "POST"}))
    assert r.status_code == 403 and "Access-Control-Allow-Origin" not in r.headers


def test_strict_csp_and_no_external_assets(client):
    r = client.get("/", headers={"Host": f"localhost:{PORT}"})
    assert "default-src 'none'" in r.headers["Content-Security-Policy"] and "script-src 'self'" in r.headers["Content-Security-Policy"]
    page = r.get_data(as_text=True)
    assert "http://" not in page.replace("http://127.0.0.1", "") and "https://" not in page
    for asset in ("app.js", "app.css", "tokens.css"):
        body = client.get(f"/static/{asset}", headers={"Host": f"localhost:{PORT}"}).get_data(as_text=True)
        assert "https://" not in body and "@import" not in body and "fonts.g" not in body


def test_scan_matches_cli_json(client, kit, capsys):
    import json

    from unpick.cli import main
    ui = client.post("/api/scan", json={"path": str(kit / "sample-a")}, headers=h()).get_json()
    main(["scan", str(kit / "sample-a"), "--json", "--no-decisions"])
    cli = json.loads(capsys.readouterr().out)
    assert [f["id"] for f in ui["findings"]] == [f["id"] for f in cli["findings"]]


def test_decide_and_exports(client, kit):
    d = client.post("/api/scan", json={"path": str(kit / "sample-b")}, headers=h()).get_json()
    fid = d["findings"][0]["id"]
    assert client.post("/api/decide", json={"id": fid, "choice": "accept"}, headers=h()).status_code == 200
    again = client.post("/api/scan", json={"path": str(kit / "sample-b")}, headers=h()).get_json()
    assert again["summary"]["open"] == 0
    html = client.get("/api/export/scan.html", headers=h()).get_data(as_text=True)
    assert "<script" not in html and "Scan report" in html


def test_export_html_escapes_untrusted_content(tmp_path):
    from unpick import report
    d = {"target": "<script>x</script>", "runs": [], "sources": ["builtin"], "files": [], "summary": {},
         "findings": [{"rule_id": "R", "source": "builtin", "severity": "high", "path": "a", "line": 1,
                       "message": "<img src=x onerror=alert(1)>", "why": "w.", "false_positive": "f.",
                       "context": [{"line": 1, "text": "<b>"}], "agreed_by": []}], "accepted": []}
    out = report.scan_html(d)
    assert "<script>x" not in out and "<img src=x" not in out and "&lt;img" in out


def test_full_report_is_self_contained(kit, tmp_path, monkeypatch):
    import json

    from unpick.cli import main
    monkeypatch.chdir(kit)
    reh = tmp_path / "r.json"
    reh.write_text(json.dumps({"verdict": "made the agent start programs", "scope": "Evidence, not proof.",
                               "events": [{"ts": "2026-10-18T01:11:00", "tool": "run_shell", "input": {"command": "<b>x</b>"}}],
                               "evidence": [{"rule": "RT-REHEARSE-SPAWN", "detail": "started bash"}]}))
    out = tmp_path / "report.html"
    assert main(["report", "sample-a", "--html", str(out), "--rehearse-json", str(reh), "--json"]) == 0
    html = out.read_text(encoding="utf-8")
    assert "First run in a box" in html and "RT-PREREQ" in html and "&lt;b&gt;x" in html
    assert "<script" not in html and "http://" not in html.split("</style>")[1].replace("https://", "")
