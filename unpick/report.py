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
from unpick.render import finding_groups, scan_verdict

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


def _scan_section(d: dict) -> str:
    runs = "".join(
        f"<li><b>{_e(r.get('source'))}</b> {_e(r.get('version') or '')} &middot; "
        f"{'hosted' if r.get('on_device') is False else 'local'} &middot; {_e(r.get('status'))}"
        f"{' &middot; <b>NETWORK</b>: ' + _e(r.get('network_detail')) if r.get('network') else ''}</li>"
        for r in d.get("runs", [])
    )
    rows = []
    for title, group in finding_groups(d.get("findings", []) + d.get("accepted", [])):
        rows.append(f"<h3>{_e(title)}</h3>")
        for entry in dict.fromkeys(entry for entry, _ in group):
            rows.append(f"<p>{_e(entry.what_it_means)}</p><p>Next step: {_e(entry.what_to_do)}</p>")
        rows.extend(_finding_html(f, d) for _, f in group)
    s = d.get("summary", {})
    agreement = "".join(f"<tr><td>{_e(k)}</td><td>{_e(v)}</td></tr>" for k, v in (s.get("agreement") or {}).items())
    skipped = "".join(f"<li>{_e(x['path'])}: {_e(x['reason'])}</li>" for x in d.get("skipped", []))
    errors = "".join(f"<li>{_e(e)}</li>" for e in d.get("errors", []) + d.get("unavailable", []))
    return (
        f"<section><h2>Scan of {_e(d.get('target'))}</h2><p><b>{_e(scan_verdict(d))}</b></p>"
        f"<p>{s.get('open', 0)} findings to review, {s.get('accepted', 0)} previously accepted (not cleared), "
        f"{len(d.get('files', []))} files read.</p><ul>{runs or '<li>built-in checks only</li>'}</ul>"
        + (f"<p>Checks incomplete:</p><ul>{errors}</ul>" if errors else "")
        + (f"<table><tr><th>sources</th><th>agreement</th></tr>{agreement}</table>" if agreement else "")
        + (f"<p>Not read:</p><ul>{skipped}</ul>" if skipped else "")
        + "</section><section><h2>Findings</h2>" + "".join(rows) + "</section>"
    )


def _finding_html(f: dict, d: dict) -> str:
    ctx = "".join(f"<div class=\"ctx{' hit' if c['line'] == f['line'] else ''}\"><span>{c['line']}</span>{_e(c['text'])}</div>"
                  for c in f.get("context", []))
    return (
        f"<article class=\"finding\"><p>{_sev(f['severity'])} <b>{_e(f['rule_id'])}</b> "
        f"<span class=\"badge\">{_e(f['source'])}</span> {_e(f['path'])}:{f['line']} "
        f"&middot; agreed by {len(f.get('agreed_by', []))} of {len(d.get('sources', []))}"
        f"{' &middot; decision: ' + _e(f['decision']) if f.get('decision') else ''}</p>"
        f"<p>{_e(f['message'])}</p><pre>{ctx}</pre>"
        f"<p class=\"muted\">Why: {_e(f['why'])}<br>False positive when: {_e(f['false_positive'])}</p></article>"
    )


def judge_section(d: dict) -> str:
    """What each judge said, shown apart from the findings: a witness, not the verdict."""
    seen: dict[str, str] = {}
    for f in d.get("findings", []) + d.get("accepted", []):
        if f["source"].startswith("judge:") and f.get("extra", {}).get("judge_explanation"):
            seen.setdefault(f["source"], f["extra"]["judge_explanation"])
    if not seen:
        return ""
    items = "".join(f"<li><b>{_e(src)}</b>: {_e(text)}</li>" for src, text in seen.items())
    return f"<section><h2>Judge opinions (one witness each, never the verdict)</h2><ul>{items}</ul></section>"


def rehearse_section(r: dict | None) -> str:
    if not r:
        return ""
    events = "".join(f"<tr><td>{_e((e.get('ts') or '')[11:19])}</td><td>{_e(e.get('tool'))}</td>"
                     f"<td class=\"mono\">{_e(str(e.get('input'))[:200])}</td></tr>" for e in r.get("events", []))
    evidence = "".join(f"<li><b>{_e(i['rule'])}</b> {_e(i['detail'])}</li>" for i in r.get("evidence", []))
    return (f"<section><h2>First run in a box</h2><p><b>{_e(r.get('verdict'))}</b></p><p class=\"muted\">{_e(r.get('scope'))}</p>"
            f"<ul>{evidence}</ul><table><tr><th>time</th><th>tool</th><th>input</th></tr>{events}</table></section>")


def decisions_section(decided: list[dict]) -> str:
    if not decided:
        return ""
    rows = "".join(f"<tr><td>{_e(x['decision'])}</td><td>{_e(x['rule_id'])}</td><td>{_e(x.get('path'))}:{_e(x.get('line'))}</td>"
                   f"<td>{_e(x.get('note'))}</td></tr>" for x in decided)
    return (f"<section><h2>Decisions on record</h2><table><tr><th>decision</th><th>rule</th><th>where</th><th>note</th></tr>"
            f"{rows}</table></section>")


def inventory_section(items: list[dict]) -> str:
    rows = "".join(
        f"<tr><td>{_e(c['kind'])}</td><td>{_e(c['host'])}</td><td>{_e(c['scope'])}</td><td>{_e(c['name'])}</td>"
        f"<td class=\"mono\">{_e(c['display_path'])}</td><td class=\"mono\">{_e(c['sha256'][:12])}</td>"
        f"<td>{_e(c['modified'][:10])}</td></tr>" for c in items
    )
    return (f"<section><h2>{len(items)} AI components</h2><table><tr><th>kind</th><th>host</th><th>scope</th>"
            f"<th>name</th><th>path</th><th>sha256</th><th>modified</th></tr>{rows}</table></section>")


def scan_html(d: dict) -> str:
    return _page("Scan report", _scan_section(d) + judge_section(d))


def inventory_html(items: list[dict]) -> str:
    return _page("Inventory", inventory_section(items))


def full_html(scan: dict, inventory: list[dict] | None = None, rehearse: dict | None = None,
              decided: list[dict] | None = None) -> str:
    """`unpick report --html`: everything in one document."""
    body = (_scan_section(scan) + judge_section(scan) + rehearse_section(rehearse)
            + decisions_section(decided or []) + (inventory_section(inventory) if inventory else ""))
    return _page("unpick report", body)


def write(path: Path, doc: str) -> Path:
    path.write_text(doc, encoding="utf-8")
    return path

