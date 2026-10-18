"""Self-contained HTML exports: no external assets, readable in black and white.

The CLI (`--html FILE`) and the UI's export buttons both call these functions, so an export from either
is the same document. Everything user-controlled is HTML-escaped; links are only ever rendered for
http(s) URLs.
"""

from __future__ import annotations

import html
from datetime import UTC, datetime
from pathlib import Path

from unpick import TAGLINE, __version__

CSS = (Path(__file__).resolve().parent / "ui" / "static" / "report.css")


def _e(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def _page(title: str, body: str) -> str:
    css = CSS.read_text(encoding="utf-8") if CSS.exists() else ""
    stamp = datetime.now(UTC).isoformat(timespec="seconds")
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">"
        f"<title>{_e(title)}</title><style>{css}</style></head><body>"
        f"<header><p class=\"kicker\">UNPICK {_e(__version__)}</p><h1>{_e(title)}</h1>"
        f"<p class=\"muted\">{_e(TAGLINE)} Generated {_e(stamp)}.</p></header>{body}</body></html>"
    )


def _sev(s: str) -> str:
    return f"<span class=\"sev sev-{_e(s)}\">{_e(s.upper())}</span>"


def scan_html(d: dict) -> str:
    runs = "".join(
        f"<li><b>{_e(r.get('source'))}</b> {_e(r.get('version') or '')} &middot; "
        f"{'hosted' if r.get('on_device') is False else 'local'} &middot; {_e(r.get('status'))}"
        f"{' &middot; <b>NETWORK</b>: ' + _e(r.get('network_detail')) if r.get('network') else ''}</li>"
        for r in d.get("runs", [])
    )
    rows = []
    for f in d.get("findings", []) + d.get("accepted", []):
        ctx = "".join(f"<div class=\"ctx{' hit' if c['line'] == f['line'] else ''}\"><span>{c['line']}</span>{_e(c['text'])}</div>"
                      for c in f.get("context", []))
        rows.append(
            f"<article class=\"finding\"><p>{_sev(f['severity'])} <b>{_e(f['rule_id'])}</b> "
            f"<span class=\"badge\">{_e(f['source'])}</span> {_e(f['path'])}:{f['line']} "
            f"&middot; agreed by {len(f.get('agreed_by', []))} of {len(d.get('sources', []))}"
            f"{' &middot; decision: ' + _e(f['decision']) if f.get('decision') else ''}</p>"
            f"<p>{_e(f['message'])}</p><pre>{ctx}</pre>"
            f"<p class=\"muted\">Why: {_e(f['why'])}<br>False positive when: {_e(f['false_positive'])}</p></article>"
        )
    s = d.get("summary", {})
    agreement = "".join(f"<tr><td>{_e(k)}</td><td>{_e(v)}</td></tr>" for k, v in (s.get("agreement") or {}).items())
    body = (
        f"<section><h2>Scan of {_e(d.get('target'))}</h2><p>{s.get('open', 0)} open, {s.get('accepted', 0)} accepted, "
        f"{len(d.get('files', []))} files read.</p><ul>{runs or '<li>built-in checks only</li>'}</ul>"
        + (f"<table><tr><th>sources</th><th>agreement</th></tr>{agreement}</table>" if agreement else "")
        + "</section><section><h2>Findings</h2>" + ("".join(rows) or "<p>No findings.</p>") + "</section>"
    )
    return _page("Scan report", body)


def inventory_html(items: list[dict]) -> str:
    rows = "".join(
        f"<tr><td>{_e(c['kind'])}</td><td>{_e(c['host'])}</td><td>{_e(c['scope'])}</td><td>{_e(c['name'])}</td>"
        f"<td class=\"mono\">{_e(c['display_path'])}</td><td class=\"mono\">{_e(c['sha256'][:12])}</td>"
        f"<td>{_e(c['modified'][:10])}</td></tr>" for c in items
    )
    body = (f"<section><h2>{len(items)} AI components</h2><table><tr><th>kind</th><th>host</th><th>scope</th>"
            f"<th>name</th><th>path</th><th>sha256</th><th>modified</th></tr>{rows}</table></section>")
    return _page("Inventory", body)


def write(path: Path, doc: str) -> Path:
    path.write_text(doc, encoding="utf-8")
    return path

