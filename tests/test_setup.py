import json
import platform

import pytest

from tests.test_schema_inventory import _fake_home
from unpick import cli, hook, setup


def _scripted(*answers):
    it = iter(answers)
    return lambda question, choices, default: next(it)


def _hook_command(agent):
    data = json.loads(hook.settings_path(agent).read_text(encoding="utf-8"))
    return data["hooks"]["PreToolUse"][-1]["hooks"][0]["command"]


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = _fake_home(tmp_path, monkeypatch)  # has ~/.claude and ~/.cursor, not ~/.codex
    (h / ".claude" / "settings.json").write_text(json.dumps({"keep": True}), encoding="utf-8")
    monkeypatch.setattr(setup, "can_watch", lambda: True)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    return h


def test_interview_asks_only_about_agents_that_are_installed(home):
    choices = setup.interview(_scripted("y", "n", "medium", "allow", "y", "y"))
    assert choices == {"agents": ["claude-code"], "min_severity": "medium", "fail_open": True, "watch": True, "quarantine": "high"}


def test_no_agents_chosen_skips_the_hook_questions(home):
    choices = setup.interview(_scripted("n", "n", "n"))
    assert choices["agents"] == [] and not choices["watch"]


def test_plan_writes_nothing(home):
    p = setup.plan(setup.interview(_scripted("y", "y", "high", "block", "y", "n")))
    assert [h["changed"] for h in p["hooks"]] == [True, True]
    assert json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8")) == {"keep": True}
    assert not (home / ".cursor" / "hooks.json").exists()
    assert not (home / ".config").exists()


def test_apply_bakes_choices_into_the_hook_and_undo_removes_everything(home):
    calls = []
    runner = lambda cmd: calls.append(cmd) or (0, "")  # noqa: E731
    choices = setup.interview(_scripted("y", "n", "medium", "allow", "y", "y"))
    r = setup.apply(choices, runner)
    cmd = _hook_command("claude-code")
    assert "--min-severity medium" in cmd and "--fail-open" in cmd
    args = cli.build_parser().parse_args(("hook " + cmd.split(" hook ", 1)[1]).split())
    assert (args.min_severity, args.fail_open) == ("medium", True)  # the baked-in command still parses
    unit = home / ".config" / "systemd" / "user" / "unpick-watch.service"
    assert r["service"]["errors"] == [] and "--quarantine high" in unit.read_text(encoding="utf-8")
    assert calls[0][:3] == ["systemctl", "--user", "disable"] and ["systemctl", "--user", "enable", "--now", "unpick-watch"] in calls
    assert setup.apply(choices, runner)["hooks"][0]["changed"] is False  # re-run is idempotent

    u = setup.undo(runner)
    assert u["service_removed"] and not unit.exists()
    assert [h["path"] for h in u["hooks"]] == [str(home / ".claude" / "settings.json")]
    assert json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8")) == {"keep": True}


def test_reinstall_with_a_new_level_replaces_the_old_hook(home):
    hook.apply("claude-code", install=True, dry_run=False, min_severity="low")
    hook.apply("claude-code", install=True, dry_run=False, min_severity="high")
    data = json.loads(hook.settings_path("claude-code").read_text(encoding="utf-8"))
    assert len(data["hooks"]["PreToolUse"]) == 1 and "--min-severity high" in _hook_command("claude-code")


def test_watcher_failure_is_reported_not_hidden(home):
    r = setup.apply({"agents": [], "min_severity": "high", "fail_open": False, "watch": True, "quarantine": None},
                    lambda cmd: (1, "Failed to connect to bus") if "enable" in cmd else (0, ""))
    assert r["service"]["errors"] and "Failed to connect to bus" in r["service"]["errors"][0]


def test_windows_uses_a_logon_task_and_writes_no_file(home, monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    p = setup.plan({"agents": [], "min_severity": "high", "fail_open": False, "watch": True, "quarantine": "high"})
    create = p["service"]["commands"][0]
    assert p["service"]["file"] is None and create[:5] == ["schtasks", "/Create", "/SC", "ONLOGON", "/TN"]
    assert create[create.index("/TR") + 1].endswith("watch --quarantine high")


def test_setup_refuses_without_a_terminal(home, monkeypatch, capsys):
    monkeypatch.setenv("UNPICK_NONINTERACTIVE", "1")
    assert cli.main(["setup"]) == 2 and "hook install" in capsys.readouterr().err
