"""`unpick ui`: a local web app on 127.0.0.1, calling the same engine functions as the CLI.

Hardening, because a page on any website can try to talk to localhost:
  * binds 127.0.0.1 only, on a random free port;
  * rejects any request whose Host header is not localhost / 127.0.0.1 on that port (DNS rebinding);
  * every /api call needs a random per-launch token in the X-Unpick-Token header. A cross-origin page
    cannot set that header without a CORS preflight, and this server never answers one (CSRF);
  * strict Content-Security-Policy, no inline script, no external assets: it works with Wi-Fi off.
The UI never shells out to the CLI.
"""

from __future__ import annotations

import json
import os
import secrets
import socket
import threading
import webbrowser
from pathlib import Path

from flask import Flask, Response, abort, current_app, jsonify, request, send_from_directory

from unpick import TAGLINE, __version__, backends, consent, decisions, inventory, judges, render, report, scan

STATIC = Path(__file__).resolve().parent / "static"
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; "
       "font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _ctx() -> dict:
    return current_app.config["RT"]


def guard():
    ctx = _ctx()
    if request.host not in ctx["hosts"]:
        abort(403)
    if request.method == "OPTIONS":
        abort(403)  # no CORS preflight is ever answered
    if request.path.startswith("/api/") and not secrets.compare_digest(request.headers.get("X-Unpick-Token", ""), ctx["token"]):
        abort(403)


def security_headers(resp: Response):
    resp.headers["Content-Security-Policy"] = CSP
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    return resp


def index():
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    page = page.replace("{{TOKEN}}", _ctx()["token"]).replace("{{VERSION}}", __version__).replace("{{TAGLINE}}", TAGLINE)
    return Response(page, mimetype="text/html")


def static_file(name):
    return send_from_directory(STATIC, name)


def api_meta():
    return jsonify({"version": __version__, "project": str(_ctx()["project"]), "tagline": TAGLINE})


def api_inventory():
    return jsonify(inventory.discover(project=_ctx()["project"]))


def api_scan():
    ctx = _ctx()
    body = request.get_json(force=True) or {}
    target = Path(body.get("path") or ctx["project"]).expanduser()
    if not target.is_absolute():
        target = ctx["project"] / target
    if not target.exists():
        return jsonify({"error": f"{target} does not exist"}), 400
    judge = body.get("judge") or None
    if judge == "auto":
        judge = judges.default_judge()
    granted = set(body.get("consent") or [])
    res = scan.scan(target, backends=body.get("backends") or [], judge=judge, boxed=bool(body.get("boxed")),
                    online=bool(body.get("online")),
                    decision_files=[decisions.project_file(ctx["project"]), decisions.user_file()],
                    consent=lambda text: any(p in text for p in granted))
    declined = next((r for r in res.runs if r.get("status") == "declined"), None)
    if declined:
        return jsonify({"need_consent": declined["provider"], "prompt": consent.prompt_text(declined["provider"])}), 409
    ctx["last"] = res.to_dict()
    _remember(ctx, ctx["last"])
    scan.save_last(res, ctx["project"])
    return jsonify(ctx["last"])


def api_raw():
    p = Path(request.args.get("path", "")).expanduser()
    if not p.is_file():
        return jsonify({"error": "not a file"}), 400
    return jsonify(render.to_json(p.read_bytes().decode("utf-8", errors="replace")))


def _remember(ctx, result: dict) -> None:
    """Every finding shown this session stays decidable, not only the latest scan's (batch scans, web checks)."""
    # ponytail: grows for the life of the UI process; a session scans dozens of add-ons, not thousands.
    known = ctx.setdefault("known", {})
    for f in result["findings"] + result["accepted"]:
        known[f["id"]] = f
    ctx.setdefault("results", {})[result["target"]] = result


def api_decide():
    ctx = _ctx()
    body = request.get_json(force=True) or {}
    last_file = ctx["project"] / ".unpick" / "last-scan.json"
    last = ctx["last"] or (json.loads(last_file.read_text(encoding="utf-8")) if last_file.is_file() else None)
    if not last and not ctx.get("known"):
        return jsonify({"error": "no scan yet"}), 400
    f = ctx.get("known", {}).get(body.get("id")) or next((x for x in (last or {}).get("findings", []) + (last or {}).get("accepted", [])
                                                          if x["id"] == body.get("id")), None)
    if not f:
        return jsonify({"error": "unknown finding"}), 400
    path = decisions.project_file(ctx["project"])
    if body.get("choice") == "undo":
        return jsonify({"undone": decisions.forget(path, f)})
    if body.get("choice") not in decisions.CHOICES:
        return jsonify({"error": "unknown choice"}), 400
    return jsonify(decisions.record(path, f, body["choice"], body.get("note", "")))


def api_demo():
    """Write the demo kit somewhere predictable so a newcomer can try unpick in one click."""
    from unpick import demo
    dest = Path.home() / ".unpick" / "demo"
    if not (dest / "sample-a" / "SKILL.md").is_file():
        demo.write(dest, force=True)
    return jsonify({"path": str(dest), "samples": {"dangerous": str(dest / "sample-a"), "safe": str(dest / "sample-b"),
                                                   "tools": str(dest / "tools.json")}})


def api_backends():
    return jsonify(backends.describe(cached=True))


def api_judges():
    return jsonify({"judges": judges.detect_all(), "default": judges.default_judge()})


def _download(doc: str, mimetype: str, name: str) -> Response:
    return Response(doc, mimetype=mimetype, headers={"Content-Disposition": f"attachment; filename={name}"})


def _shown_scan() -> dict:
    """The result the page is showing (it names it in a header), so a report never describes another add-on."""
    ctx = _ctx()
    return ctx.get("results", {}).get(request.headers.get("X-Unpick-Target", "")) or ctx["last"] or abort(404)


def export_scan_html():
    last = _shown_scan()
    return _download(report.scan_html(last), "text/html", "unpick-scan.html")


def export_scan_json():
    last = _shown_scan()
    return _download(json.dumps(last, indent=2, ensure_ascii=False), "application/json", "unpick-scan.json")


def export_inventory_html():
    return _download(report.inventory_html(inventory.discover(project=_ctx()["project"])), "text/html",
                     "unpick-inventory.html")


def api_check():
    from unpick import check, quarantine
    body = request.get_json(force=True) or {}
    try:
        res = check.run(str(body.get("ref", "")), offline=bool(body.get("offline")))
    except (quarantine.Refused, OSError) as e:
        return jsonify({"error": str(e)}), 400
    _ctx()["last"] = res["scan"]
    _remember(_ctx(), res["scan"])  # so warnings reviewed from a web check can be decided like any scan's
    return jsonify(res)


def api_check_approve():
    from unpick import check, quarantine
    body = request.get_json(force=True) or {}
    try:
        return jsonify(check.approve(str(body.get("id", "")), _ctx()["project"]))
    except quarantine.Refused as e:
        return jsonify({"error": str(e)}), 400


_JOBS: dict[str, dict] = {}


def api_rehearse_start():
    import threading

    from unpick import quarantine, rehearse
    body = request.get_json(force=True) or {}
    target = Path(str(body.get("path", ""))).expanduser()
    if not target.is_absolute():
        target = _ctx()["project"] / target
    if not target.exists():
        try:
            target = Path(quarantine.load_meta(str(body.get("path", "")))[1]["root"])
        except quarantine.Refused as e:
            return jsonify({"error": str(e)}), 400
    job_id = secrets.token_hex(6)
    job = _JOBS[job_id] = {"status": "starting", "trace": None, "result": None, "error": None}

    def work():
        try:
            job["status"] = "running"
            job["result"] = rehearse.run(target, task=body.get("task") or "Summarise the README in this folder.",
                                         on_start=lambda t: job.update(trace=t))
            job["status"] = "done"
        except Exception as e:  # surfaced to the UI, never swallowed
            job["status"], job["error"] = "error", str(e)

    threading.Thread(target=work, daemon=True).start()
    return jsonify({"job": job_id})


def api_rehearse_poll(job_id):
    from unpick import flight
    job = _JOBS.get(job_id) or abort(404)
    if job["result"]:
        events = job["result"]["events"]
    else:
        events = flight.read(job["trace"]) if job["trace"] else []  # follow the recorder while the box runs
    return jsonify({"status": job["status"], "error": job["error"], "events": events, "result": job["result"]})


def api_verify():
    from unpick import lock
    try:
        return jsonify(lock.verify(_ctx()["project"]))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 400


def api_lock():
    from unpick import lock
    data = lock.lock(_ctx()["project"])
    return jsonify({"components": len(data["components"])})


def api_recover():
    from datetime import datetime

    from unpick import recover
    body = request.get_json(force=True) or {}
    since = None
    if body.get("since"):
        try:
            since = datetime.fromisoformat(body["since"]).astimezone()
        except ValueError:
            return jsonify({"error": "since must be an ISO date or datetime"}), 400
    r = recover.run(body.get("component") or None, _ctx()["project"], since, apply=bool(body.get("apply")))
    _ctx()["incident"] = r
    return jsonify(r)


def export_incident():
    r = _ctx().get("incident") or abort(404)
    return _download(Path(r["report"]).read_text(encoding="utf-8"), "text/markdown", Path(r["report"]).name)


def _target(body) -> Path:
    t = Path(str(body.get("path", ""))).expanduser()
    return t if t.is_absolute() else _ctx()["project"] / t


def _shared_by(t: Path, components: list[dict]) -> list[dict]:
    """The other add-ons that would go with t if it were moved whole: entries in a config file, or add-ons inside a folder."""
    hits = []
    for c in components:
        p, _, entry = c["path"].partition("#")
        cp = Path(p)
        if (entry and cp == t) or (not entry and cp != t and cp.is_relative_to(t)):
            hits.append(c)
    return hits


def api_isolate():
    from unpick import inventory, isolate
    body = request.get_json(force=True) or {}
    t = Path(os.path.abspath(_target(body)))  # absolute, but never through a symlink
    components = inventory.discover(project=_ctx()["project"])
    want = str(body.get("component") or "")
    try:
        if "#" in want:  # one entry in a shared config, chosen from Installed: take out only that entry
            c = next((c for c in components if c["path"] == want), None)
            if not c:
                return jsonify({"error": "That add-on is no longer listed in its settings file. Reload Installed and try again."}), 400
            return jsonify(isolate.isolate(c, reason="quarantined from the UI"))
        shared = _shared_by(t, components)
        if shared:
            names = ", ".join(sorted({c["name"] for c in shared})[:6])
            return jsonify({"error": f"{t} also holds {len(shared)} other add-ons ({names}). unpick will not move it whole. "
                                     "Open the one you mean from Installed and move that one."}), 400
        return jsonify(isolate.isolate({"path": str(t), "name": t.name}, reason="quarantined from the UI"))
    except isolate.CannotIsolate as e:
        return jsonify({"error": str(e)}), 400


def api_isolated():
    from unpick import isolate
    return jsonify(isolate.isolated())


def api_restore():
    from unpick import isolate
    try:
        return jsonify({"message": isolate.restore(str((request.get_json(force=True) or {}).get("id", "")))})
    except isolate.CannotIsolate as e:
        return jsonify({"error": str(e)}), 400


def api_clean():
    from unpick import clean
    t = _target(request.get_json(force=True) or {})
    try:
        return jsonify(clean.clean(t))
    except (FileExistsError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 400


ROUTES = [
    ("/", index, ["GET"]), ("/static/<path:name>", static_file, ["GET"]),
    ("/api/meta", api_meta, ["GET"]), ("/api/inventory", api_inventory, ["GET"]), ("/api/scan", api_scan, ["POST"]),
    ("/api/raw", api_raw, ["GET"]), ("/api/decide", api_decide, ["POST"]), ("/api/backends", api_backends, ["GET"]),
    ("/api/judges", api_judges, ["GET"]), ("/api/export/scan.html", export_scan_html, ["GET"]),
    ("/api/export/scan.json", export_scan_json, ["GET"]), ("/api/export/inventory.html", export_inventory_html, ["GET"]),
    ("/api/check", api_check, ["POST"]), ("/api/check/approve", api_check_approve, ["POST"]),
    ("/api/rehearse", api_rehearse_start, ["POST"]), ("/api/rehearse/<job_id>", api_rehearse_poll, ["GET"]),
    ("/api/verify", api_verify, ["GET"]), ("/api/lock", api_lock, ["POST"]),
    ("/api/recover", api_recover, ["POST"]), ("/api/demo", api_demo, ["POST"]),
    ("/api/isolate", api_isolate, ["POST"]), ("/api/isolated", api_isolated, ["GET"]), ("/api/restore", api_restore, ["POST"]),
    ("/api/clean", api_clean, ["POST"]), ("/api/export/incident.md", export_incident, ["GET"]),
]


def create_app(port: int, token: str, project: Path | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["RT"] = {"hosts": {f"127.0.0.1:{port}", f"localhost:{port}"}, "token": token,
                        "project": (project or Path.cwd()).resolve(), "last": None}
    app.before_request(guard)
    app.after_request(security_headers)
    for rule, view, methods in ROUTES:
        app.add_url_rule(rule, view.__name__, view, methods=methods)
    return app


def serve(project: Path | None = None, open_browser: bool = True, port: int | None = None) -> None:
    from werkzeug.serving import make_server

    port = port or free_port()
    token = secrets.token_urlsafe(24)
    app = create_app(port, token, project)
    server = make_server("127.0.0.1", port, app, threaded=True)
    url = f"http://127.0.0.1:{port}/"
    print(f"unpick UI on {url}  (local only; Ctrl+C to stop)", flush=True)
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
