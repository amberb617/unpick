import io
import json

import pytest

from tests.test_schema_inventory import _fake_home
from unpick import hook, watch


@pytest.mark.parametrize("cmd,ref", [
    ("claude mcp add mail -- npx -y mail-mcp@1.0.16", "npm:mail-mcp@1.0.16"),
    ("codex mcp add fs -- uvx fs-mcp==0.3", "pypi:fs-mcp==0.3"),
    ("npx skills add acme/agent-skills", "https://github.com/acme/agent-skills"),
    ("claude plugin install https://github.com/acme/plugin", "https://github.com/acme/plugin"),
    ("git clone https://github.com/acme/s ~/.claude/skills/s", "https://github.com/acme/s"),
])
def test_install_commands_are_recognised(cmd, ref):
    assert hook.targets(cmd) == [ref]


@pytest.mark.parametrize("cmd", ["ls -la", "npm test", "git clone https://github.com/acme/app ~/code/app", "claude --help"])
def test_ordinary_commands_pass(cmd):
    assert hook.targets(cmd) == []
    assert hook.decide({"tool_name": "Bash", "tool_input": {"command": cmd}})[0]


def fake_meta(findings):
    return lambda ref: {"id": "q1", "scan": {"findings": findings}}


BAD = [{"severity": "high", "rule_id": "RT-SECRECY", "path": "SKILL.md", "line": 3, "message": "do not tell the user"}]


def test_blocks_install_with_high_findings():
    ok, msg = hook.decide({"tool_name": "Bash", "tool_input": {"command": "npx skills add acme/x"}}, runner=fake_meta(BAD))
    assert not ok and "RT-SECRECY" in msg and "unpick check" in msg


def test_allows_install_below_threshold():
    low = [{**BAD[0], "severity": "low"}]
    assert hook.decide({"tool_name": "Bash", "tool_input": {"command": "npx skills add acme/x"}}, runner=fake_meta(low))[0]


def test_unverifiable_install_fails_closed(monkeypatch):
    cmd = {"tool_name": "Bash", "tool_input": {"command": "claude mcp add thing -- ./run-server"}}
    assert not hook.decide(cmd)[0]
    monkeypatch.setenv("UNPICK_HOOK_FAIL_OPEN", "1")
    assert hook.decide(cmd)[0]


def test_edit_to_mcp_config_is_scanned(tmp_path):
    poisoned = json.dumps({"mcpServers": {"x": {"command": "npx", "args": ["mcp-remote@0.1.10", "https://a.example.invalid"]}}})
    ok, msg = hook.decide({"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / ".mcp.json"), "content": poisoned}})
    assert not ok and "RT-MCP-LAUNCH" in msg


def test_hook_process_exit_codes():
    err = io.StringIO()
    ev = json.dumps({"tool_name": "Bash", "tool_input": {"command": "claude mcp add t -- ./bin"}})
    assert hook.run("claude-code", stdin=io.StringIO(ev), stderr=err) == 2 and "cannot tell" in err.getvalue()
    assert hook.run("claude-code", stdin=io.StringIO("not json")) == 0
    out = io.StringIO()
    assert hook.run("cursor", stdin=io.StringIO(json.dumps({"command": "claude mcp add t -- ./bin"})), stdout=out) == 0
    assert json.loads(out.getvalue())["permission"] == "deny"


@pytest.mark.parametrize("agent", ["claude-code", "codex", "cursor"])
def test_install_dry_run_then_install_then_uninstall(tmp_path, monkeypatch, agent):
    _fake_home(tmp_path, monkeypatch)
    path = hook.settings_path(agent)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"keep": True}))
    dry = hook.apply(agent, install=True, dry_run=True)
    assert dry["changed"] and json.loads(path.read_text(encoding="utf-8")) == {"keep": True}
    hook.apply(agent, install=True, dry_run=False)
    assert hook.apply(agent, install=True, dry_run=False)["changed"] is False  # idempotent
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["keep"] and hook.MARK in json.dumps(data["hooks"])
    assert list(path.parent.glob(path.name + ".unpick-backup-*"))
    hook.apply(agent, install=False, dry_run=False)
    assert json.loads(path.read_text(encoding="utf-8")) == {"keep": True}


def test_watch_roots_and_component_root(tmp_path, monkeypatch):
    h = _fake_home(tmp_path, monkeypatch)
    (tmp_path / "proj").mkdir(exist_ok=True)
    deep, shallow = watch.watch_plan(tmp_path / "proj")
    assert (h / ".claude" / "skills").resolve() in deep
    assert h.resolve() not in deep  # never the whole home tree
    root = h / ".claude" / "skills"
    assert watch.component_root(root / "tidy" / "SKILL.md", [root]) == root / "tidy"


def test_watch_scan_and_report_logs(tmp_path, monkeypatch, kit):
    monkeypatch.setattr(watch, "LOG", tmp_path / "watch.log")
    monkeypatch.setattr(watch, "notify", lambda t, b: None)
    e = watch.scan_and_report(kit / "sample-a")
    assert e["high"] >= 1 and json.loads((tmp_path / "watch.log").read_text(encoding="utf-8"))["path"].endswith("sample-a")


@pytest.mark.parametrize("kind,needle", [("launchd", "RunAtLoad"), ("systemd", "WantedBy=default.target"), ("windows", "/SC ONLOGON")])
def test_service_recipes(kind, needle):
    assert needle in watch.service(kind)


@pytest.mark.parametrize("script", [
    "python3 - <<'EOF'\nprint('example: claude mcp add x -- ./bin')\nEOF",
    "cat > notes.md <<EOF\nRun claude mcp add mail -- npx -y mail-mcp to install.\nEOF",
    'echo "claude mcp add x -- npx -y pkg"',
    "git commit -m 'docs: explain npx skills add acme/x'",
    "grep -n 'claude mcp add' README.md",
])
def test_install_text_that_is_only_data_is_ignored(script):
    assert hook.targets(script) == []


@pytest.mark.parametrize("script,ref", [
    ("cd proj && claude mcp add mail -- npx -y mail-mcp@2", "npm:mail-mcp@2"),
    ("FOO=1 sudo claude mcp add mail -- npx -y mail-mcp@2", "npm:mail-mcp@2"),
    ("sh -c 'claude mcp add mail -- npx -y mail-mcp@2'", "npm:mail-mcp@2"),
    ("bash -c \"npx skills add acme/x\"", "https://github.com/acme/x"),
    ("echo start\nnpx -y skills add acme/x\necho done", "https://github.com/acme/x"),
])
def test_real_installs_inside_scripts_are_found(script, ref):
    assert hook.targets(script) == [ref]


def test_unparseable_script_errs_toward_checking():
    assert hook.targets("echo 'unterminated ; claude mcp add x -- npx -y pkg") == ["npm:pkg"]


def test_unquoted_heredoc_substitutions_still_count():
    script = "cat <<EOF\ninstalled: $(npx skills add acme/x)\nEOF"
    assert hook.targets(script) == ["https://github.com/acme/x"]
    assert hook.targets(script.replace("<<EOF", "<<'EOF'")) == []


@pytest.mark.parametrize("cmd", ['C:\\Tools\\unpick.EXE hook run codex', '"C:\\Program Files\\unpick\\unpick.exe" hook run cursor',
                                 "/usr/local/bin/unpick hook run claude-code", "python -m unpick hook run codex"])
def test_hook_marker_recognises_every_install_form(cmd):
    assert hook._ours({"command": cmd})
    assert not hook._ours({"command": "prettier --write"})
