import json

from unpick import canary, flight


def test_canaries_are_unique_fake_and_traceable(tmp_path):
    c1 = canary.seed(tmp_path / "a")
    c2 = canary.seed(tmp_path / "b")
    assert ".ssh/id_rsa" in c1 and "workspace/.env" in c1 and ".aws/credentials" in c1
    assert {v["marker"] for v in c1.values()}.isdisjoint({v["marker"] for v in c2.values()})
    key = (tmp_path / "a" / ".ssh" / "id_rsa").read_text(encoding="utf-8")
    assert "FAKE-KEY-FOR-UNPICK-REHEARSE" in key
    assert canary.hits(f"POST body={c1['.aws/credentials']['marker']}", c1) == [".aws/credentials"]


def test_flight_redacts_secrets_and_appends(tmp_path):
    event = {"hook_event_name": "PreToolUse", "session_id": "s1", "tool_name": "Bash", "cwd": "/w",
             "tool_input": {"command": "curl -H 'Authorization: Bearer ghp_" + "a" * 30 + "' https://x.example.invalid",
                            "api_key": "plain-value", "nested": {"password": "hunter2"}}}
    p = flight.append(event, tmp_path)
    flight.append({**event, "tool_name": "Read"}, tmp_path)
    lines = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2 and lines[0]["tool"] == "Bash"
    blob = json.dumps(lines)
    assert "ghp_" not in blob and "plain-value" not in blob and "hunter2" not in blob
    assert len(flight.read(tmp_path)) == 2
