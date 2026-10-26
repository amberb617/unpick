import asyncio
import json
import platform
from types import SimpleNamespace

import pytest

from tests.test_schema_inventory import _fake_home
from unpick import backends, cli, integrations

SCANNERS = [{"name": n, "installed": n == "yara-x", "version": "1.21.0" if n == "yara-x" else None, "network": "none"}
            for n in ("jiffy", "cisco-skill-scanner", "yara-x")]


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = _fake_home(tmp_path, monkeypatch)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    for var in ("JIFFY_TOKEN", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(backends, "which", lambda cmd: "/usr/bin/jiffy" if cmd == "jiffy" else None)
    monkeypatch.setattr(backends, "describe", lambda cached=False: SCANNERS)
    return home


def _save_jiffy_login(home, data):
    cfg = home / ".config" / "jiffy" / "config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def test_jiffy_is_connected_by_saved_login_or_env(env, monkeypatch):
    assert integrations.jiffy_status()["connected"] is False
    _save_jiffy_login(env, "{not json")
    assert integrations.jiffy_status()["connected"] is False
    _save_jiffy_login(env, {"token": ""})
    assert integrations.jiffy_status()["connected"] is False
    _save_jiffy_login(env, {"token": "jfy_saved"})
    assert integrations.jiffy_status()["how"] == "saved login"
    monkeypatch.setenv("JIFFY_TOKEN", "jfy_env")
    assert integrations.jiffy_status()["how"] == "$JIFFY_TOKEN"


def test_key_reaches_jiffy_login_through_the_environment_only(env):
    calls = []
    def runner(argv, **kw):
        calls.append((argv, kw))
        return SimpleNamespace(returncode=0, stdout="Logged in as amber (jiffy)", stderr="")
    code, msg = integrations.connect_jiffy("  jfy_secret \n", runner)
    argv, kw = calls[0]
    assert code == 0 and "Logged in" in msg
    assert argv == ["jiffy", "login"] and not any("jfy_secret" in a for a in argv)
    assert kw["env"]["JIFFY_TOKEN"] == "jfy_secret"


def test_browser_sign_in_keeps_the_terminal(env):
    calls = []
    integrations.connect_jiffy(None, lambda argv, **kw: calls.append(kw) or SimpleNamespace(returncode=0))
    assert calls == [{}]  # no captured output, no injected token: the device flow talks to you directly


def test_missing_jiffy_cli_says_how_to_install(env, monkeypatch):
    monkeypatch.setattr(backends, "which", lambda cmd: None)
    code, msg = integrations.connect_jiffy("jfy_x", lambda *a, **k: pytest.fail("must not run"))
    assert code == 2 and integrations.JIFFY_PACKAGE in msg
    assert integrations.rows()[0]["status"] == "Jiffy CLI not installed"


def test_rows_and_online_backends(env, monkeypatch):
    _save_jiffy_login(env, {"token": "jfy_saved"})
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    rows = {r["id"]: r for r in integrations.rows()}
    assert rows["jiffy"]["ready"] and rows["yara-x"]["ready"] and not rows["cisco-skill-scanner"]["ready"]
    assert rows["cisco-skill-scanner"]["action"] == ["backends", "install", "cisco-skill-scanner", "--online"]
    assert rows["api:openai"]["ready"] and not rows["api:anthropic"]["ready"] and rows["api:openai"]["action"] is None
    assert "sk-test" not in json.dumps(rows)  # status says a key is set, never what it is
    assert integrations.online_backends() == ["jiffy", "yara-x"]  # hosted AI review is not a scanner


def test_connect_refuses_without_a_terminal(env, monkeypatch, capsys):
    monkeypatch.setattr(integrations, "connect_jiffy", lambda key: pytest.fail("must not run"))
    assert cli.main(["integrations", "connect", "jiffy"]) == 2 and "JIFFY_TOKEN" in capsys.readouterr().err


def test_home_screen_integrations_and_online_scan(env, monkeypatch):
    from unpick import tui_app

    _save_jiffy_login(env, {"token": "jfy_saved"})
    skill = env / ".claude" / "skills" / "tidy"
    monkeypatch.setattr(tui_app.inventory, "discover", lambda project: [
        {"path": str(skill), "kind": "skill", "host": "claude-code", "name": "tidy", "display_path": "~/tidy"}])
    monkeypatch.setattr(tui_app.Home, "MIN_SPLASH", 0)
    handed = []
    monkeypatch.setattr(tui_app, "hand_over", lambda app, argv: handed.append(argv))

    async def go():
        app = tui_app.Home(scanner=lambda p: SimpleNamespace(exit_code=0, findings=[]))
        async with app.run_test(size=(120, 40)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause(0.2)
            body = str(app.query_one("#integrations-body").render())
            assert "Jiffy: key saved in the Jiffy CLI, not checked" in body and "1 of 2 scanners installed" in body
            assert "\u2713 Jiffy" not in body  # no tick for a key nobody has checked
            await pilot.press("i", "o")
            assert handed[-1] == ["scan", str(skill), "--backends", "jiffy,yara-x", "--online"]
            await pilot.press("escape", "n", "enter")  # first row is Jiffy
            assert handed[-1] == ["integrations", "connect", "jiffy"]

    asyncio.run(go())


def test_status_says_saved_not_working_and_names_a_non_default_server(env, monkeypatch):
    _save_jiffy_login(env, {"token": "jfy_saved", "apiUrl": "http://localhost:3000"})
    jiffy = integrations.rows()[0]
    assert jiffy["status"] == "key saved in the Jiffy CLI, not checked; server http://localhost:3000"
    _save_jiffy_login(env, {"token": "jfy_saved"})
    assert integrations.rows()[0]["status"] == "key saved in the Jiffy CLI, not checked"
    monkeypatch.setenv("JIFFY_API_URL", "https://staging.example/")
    assert integrations.rows()[0]["status"].endswith("; server https://staging.example")


def test_check_runs_whoami(env):
    calls = []
    def runner(argv, **kw):
        calls.append(argv)
        return SimpleNamespace(returncode=1, stdout="", stderr="Token is invalid or revoked. Run `jiffy login`.")
    assert integrations.check_jiffy(runner) == (1, "Token is invalid or revoked. Run `jiffy login`.")
    assert calls == [["jiffy", "whoami"]]


def test_check_command_reports_a_rejected_key(env, monkeypatch, capsys):
    monkeypatch.setattr(integrations, "check_jiffy", lambda: (1, "Token is invalid or revoked."))
    assert cli.main(["integrations", "check", "jiffy"]) == 1
    out = capsys.readouterr().out
    assert "Token is invalid or revoked." in out and "unpick integrations connect jiffy" in out
    monkeypatch.setattr(integrations, "check_jiffy", lambda: (0, "Logged in as amber (jiffy)"))
    assert cli.main(["integrations", "check", "jiffy"]) == 0 and "accepted the saved key" in capsys.readouterr().out


def test_an_api_key_is_caught_before_anything_is_sent(env):
    code, msg = integrations.connect_jiffy("jsk_realbutwrongkind", lambda *a, **k: pytest.fail("must not run"))
    assert code == 2 and "CLI token" in msg and "settings/cli-tokens" in msg and "Nothing was sent" in msg
    assert integrations.JIFFY_KEYS_URL.endswith("/settings/cli-tokens")
