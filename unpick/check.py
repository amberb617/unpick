"""`unpick check <git-url | npm:pkg | pypi:pkg | archive | path>`: vet a component before it is installed.

1. Fetch it into quarantine with nothing executed (unpick.quarantine).
2. Provenance: the 60-second "who made it?" card (unpick.provenance). This is the one subcommand where
   the network is on by default, because fetching needs it; `--offline` skips the card.
3. Scan the quarantined copy with the built-in checks, any scanners and judge you chose.
4. `unpick check --approve <id>` prints the install command (it never runs it) and adds the component
   to unpick.lock.json with its hashes, so `verify` notices if it changes later.
"""

from __future__ import annotations

import json
from pathlib import Path

from unpick import lock, provenance, quarantine, scan


def run(ref: str, backends=None, judge=None, boxed=False, offline=False, consent=None) -> dict:
    src = quarantine.parse(ref)
    if offline and quarantine.needs_network(src):
        raise quarantine.Refused(f"fetching {ref} needs the network; drop --offline or check a local copy")
    dest, info = quarantine.fetch(src)
    root = Path(info["root"])
    card, questions, card_error = {}, [], None
    readme = next((p for p in (root / "SKILL.md", root / "README.md", root / "readme.md") if p.is_file()), None)
    readme_text = readme.read_text(encoding="utf-8", errors="replace") if readme else ""
    if not offline:
        try:
            if src.kind == "git" and src.extra.get("owner"):
                card = provenance.github(src.extra["owner"], src.extra["repo"])
            elif src.kind == "npm":
                card = provenance.npm(info["registry"], info["version"])
            elif src.kind == "pypi":
                card = provenance.pypi(info["registry"])
        except OSError as e:
            card_error = f"provenance lookup failed: {e}"
        questions = provenance.questions(card, src.name, readme_text)
    res = scan.scan(root, backends=backends or [], judge=judge, boxed=boxed, decision_files=[], consent=consent)
    meta = {
        "id": dest.name, "ref": ref, "kind": src.kind, "name": src.name, "root": str(root),
        "version": info.get("version") or src.version, "commit": info.get("commit"),
        "digest": info.get("integrity") or info.get("sha256"), "provenance": card, "questions": questions,
        "provenance_error": card_error, "scan": res.to_dict(),
        "network": _network_note(src, offline),
    }
    quarantine.save_meta(dest, meta)
    return meta


def _network_note(src, offline: bool) -> list[str]:
    hosts = {"git": "the git host", "npm": "registry.npmjs.org", "pypi": "pypi.org and files.pythonhosted.org",
             "archive": "the archive URL", "path": None}
    out = []
    if quarantine.needs_network(src):
        out.append(f"fetched {src.name} from {hosts[src.kind]}")
    if not offline and src.kind == "git" and src.extra.get("owner"):
        out.append(f"looked up {src.extra['owner']}/{src.extra['repo']} on api.github.com")
    return out


def install_command(meta: dict) -> str:
    root, name, ver = meta["root"], meta["name"], meta.get("version")
    if meta["kind"] == "npm":
        return f"claude mcp add {name.split('/')[-1]} -- npx -y {name}@{ver}"
    if meta["kind"] == "pypi":
        return f"claude mcp add {name} -- uvx {name}=={ver}"
    if (Path(root) / "SKILL.md").is_file():
        return f'cp -R "{root}" ~/.claude/skills/{name}   # the exact copy that was scanned'
    return f'cp -R "{root}" <destination>   # the exact copy that was scanned'


def approve(check_id: str, project: Path) -> dict:
    dest, meta = quarantine.load_meta(check_id)
    root = Path(meta["root"])
    lf = project / lock.LOCKFILE
    data = json.loads(lf.read_text(encoding="utf-8")) if lf.is_file() else {"tool": "unpick", "components": {}}
    data.setdefault("approved", {})[meta["id"]] = {
        "ref": meta["ref"], "kind": meta["kind"], "name": meta["name"], "version": meta.get("version"),
        "commit": meta.get("commit"), "digest": meta.get("digest"), "files": lock.file_hashes(root),
        "open_findings_at_approval": meta["scan"]["summary"]["open"],
    }
    lf.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return {"id": meta["id"], "install_command": install_command(meta), "lockfile": str(lf),
            "open_findings_at_approval": meta["scan"]["summary"]["open"]}
