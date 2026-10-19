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
    scan.save_last(res, ctx["project"])
    return jsonify(ctx["last"])


def api_raw():
    p = Path(request.args.get("path", "")).expanduser()
    if not p.is_file():
        return jsonify({"error": "not a file"}), 400
    return jsonify(render.to_json(p.read_bytes().decode("utf-8", errors="replace")))


def api_decide():
    ctx = _ctx()
    body = request.get_json(force=True) or {}
    last_file = ctx["project"] / ".unpick" / "last-scan.json"
    last = ctx["last"] or (json.loads(last_file.read_text(encoding="utf-8")) if last_file.is_file() else None)
    if not last:
        return jsonify({"error": "no scan yet"}), 400
    f = next((x for x in last["findings"] + last["accepted"] if x["id"] == body.get("id")), None)
    if not f or body.get("choice") not in decisions.CHOICES:
        return jsonify({"error": "unknown finding or choice"}), 400
    return jsonify(decisions.record(decisions.project_file(ctx["project"]), f, body["choice"], body.get("note", "")))


def api_backends():
    return jsonify(backends.describe())


def api_judges():
    return jsonify({"judges": judges.detect_all(), "default": judges.default_judge()})


def _download(doc: str, mimetype: str, name: str) -> Response:
    return Response(doc, mimetype=mimetype, headers={"Content-Disposition": f"attachment; filename={name}"})


def export_scan_html():
    last = _ctx()["last"] or abort(404)
    return _download(report.scan_html(last), "text/html", "unpick-scan.html")


def export_scan_json():
    last = _ctx()["last"] or abort(404)
    return _download(json.dumps(last, indent=2, ensure_ascii=False), "application/json", "unpick-scan.json")


def export_inventory_html():
    return _download(report.inventory_html(inventory.discover(project=_ctx()["project"])), "text/html",
                     "unpick-inventory.html")


def api_check():
    from unpick import check, quarantine
    body = request.get_json(force=True) or {}
    try:
        return jsonify(check.run(str(body.get("ref", "")), offline=bool(body.get("offline"))))
    except (quarantine.Refused, OSError) as e:
        return jsonify({"error": str(e)}), 400


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


ROUTES = [
    ("/", index, ["GET"]), ("/static/<path:name>", static_file, ["GET"]),
    ("/api/meta", api_meta, ["GET"]), ("/api/inventory", api_inventory, ["GET"]), ("/api/scan", api_scan, ["POST"]),
    ("/api/raw", api_raw, ["GET"]), ("/api/decide", api_decide, ["POST"]), ("/api/backends", api_backends, ["GET"]),
    ("/api/judges", api_judges, ["GET"]), ("/api/export/scan.html", export_scan_html, ["GET"]),
    ("/api/export/scan.json", export_scan_json, ["GET"]), ("/api/export/inventory.html", export_inventory_html, ["GET"]),
    ("/api/check", api_check, ["POST"]), ("/api/check/approve", api_check_approve, ["POST"]),
    ("/api/rehearse", api_rehearse_start, ["POST"]), ("/api/rehearse/<job_id>", api_rehearse_poll, ["GET"]),
    ("/api/verify", api_verify, ["GET"]), ("/api/lock", api_lock, ["POST"]),
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
