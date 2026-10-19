"""Command line. Every command calls the same functions the UI does, and every command has --json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.markup import escape as esc
from rich.table import Table

from unpick import TAGLINE, __version__

SEV_STYLE = {"high": "bold red", "medium": "yellow", "low": "cyan", "info": "dim"}
console = Console()


def _out(args, data, render):
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        render(data)


# ---------------------------------------------------------------- inventory
def cmd_inventory(args) -> int:
    from unpick import inventory

    items = inventory.discover(project=Path(args.project), extra=[Path(p) for p in args.add_path],
                               config=Path(args.config) if args.config else None)
    if args.html:
        from unpick import report
        report.write(Path(args.html), report.inventory_html(items))
    def render(rows):
        t = Table(title=f"AI components found ({len(rows)})", show_lines=False)
        for col in ("kind", "host", "scope", "name", "path", "sha256", "modified", "provenance"):
            t.add_column(col, overflow="fold")
        for r in rows:
            t.add_row(r["kind"], r["host"], r["scope"], esc(r["name"]), esc(r["display_path"]), r["sha256"][:12],
                      r["modified"][:10], esc(r.get("provenance") or ""))
        console.print(t)
    _out(args, items, render)
    return 0


# ---------------------------------------------------------------- scan
def _print_scan(d: dict) -> None:
    runs = d["runs"]
    strip = ["builtin checks"] + [
        f"{r['source']} {r.get('version') or ''} [{'on-device' if r.get('on_device', True) else 'hosted'}]"
        f"{' NETWORK' if r.get('network') else ''} ({r.get('status')})" for r in runs]
    console.print("[bold]ran:[/] " + esc(" | ".join(strip)))
    net = d["summary"]["network_calls"]
    console.print("[bold]network:[/] " + ("none" if not net else esc("; ".join(f"{r['source']}: {r.get('network_detail')}" for r in net))))
    for e in d["errors"]:
        console.print(f"[red]error:[/] {esc(e)}")
    current = None
    for f in d["findings"]:
        if f["path"] != current:
            current = f["path"]
            console.print(f"\n[bold underline]{esc(current)}[/]")
        badge = f["source"].split(":")[0]
        agreed = f"agreed by {len(f['agreed_by'])} of {len(d['sources'])}"
        console.print(f"  [{SEV_STYLE[f['severity']]}]{f['severity']:>6}[/] {f['rule_id']} [dim]({badge}; {agreed}; id {f['id']})[/]")
        console.print(f"         line {f['line']}: {esc(f['message'])}")
        if f["matched"]:
            from unpick.render import escape as raw_escape
            console.print(f"         [dim]> {esc(raw_escape(f['matched'])[:160])}[/]")
        console.print(f"         [dim]why: {esc(f['why'])}[/]")
        console.print(f"         [dim]false positive when: {esc(f['false_positive'])}[/]")
    s = d["summary"]
    console.print(f"\n[bold]{s['open']} open finding(s), {s['accepted']} accepted.[/] By source: {s['by_source']}")
    if d.get("skipped"):
        console.print(f"[dim]{len(d['skipped'])} file(s) not read (binary, too large or not text); see --json \"skipped\".[/]")
    if len(d["sources"]) > 1:
        console.print(f"Agreement (Jaccard on file+line): {s['agreement']}")
    if s["open"]:
        console.print("[dim]Record a decision: unpick decide <id> accept|reject|ask-author --note \"...\"[/]")


def _backend_list(arg: str | None) -> list[str]:
    from unpick import backends

    if not arg:
        return []
    if arg == "installed":
        return [r["name"] for r in backends.describe() if r["installed"] and not r["needs_online"]]
    return [b.strip() for b in arg.split(",") if b.strip()]


def cmd_scan(args) -> int:
    from unpick import consent, decisions, judges, scan

    consent.REMEMBER = args.remember
    judge = args.judge
    if judge == "auto":
        judge = judges.default_judge()
        if not judge:
            console.print("[yellow]no on-device judge found; continuing without one[/]", highlight=False) if not args.json else None
    if args.no_decisions:
        files = []
    elif args.decisions:
        files = [Path(args.decisions)]
    else:
        files = [decisions.project_file(), decisions.user_file()]
    target = Path(args.path)
    if not target.exists():
        print(f"unpick: {target} does not exist", file=sys.stderr)
        return 2
    res = scan.scan(target, backends=_backend_list(args.backends), judge=judge, boxed=args.boxed,
                    online=args.online, decision_files=files)
    scan.save_last(res)
    if args.html:
        from unpick import report
        report.write(Path(args.html), report.scan_html(res.to_dict()))
    _out(args, res.to_dict(), _print_scan)
    return res.exit_code


# ---------------------------------------------------------------- raw
def cmd_raw(args) -> int:
    from unpick import render

    text = Path(args.file).read_bytes().decode("utf-8", errors="replace")
    rows = render.to_json(text)
    def show(rows):
        t = Table(title=f"{args.file}: rendered (what you see) vs raw (what the model reads)", show_lines=False, expand=True)
        t.add_column("#", justify="right", style="dim", no_wrap=True)
        t.add_column("rendered", ratio=1, overflow="fold")
        t.add_column("raw", ratio=1, overflow="fold")
        t.add_column("hidden", style="red", overflow="fold")
        for r in rows:
            style = "on #3a0d14" if r["differs"] else ""
            t.add_row(str(r["line"]), esc(r["rendered"]), esc(r["raw"]), esc("; ".join(r["reasons"])), style=style)
        console.print(t)
        n = sum(r["differs"] for r in rows)
        console.print(f"[bold]{n} line(s) differ between the rendered view and the raw bytes.[/]")
    _out(args, rows, show)
    return 1 if any(r["differs"] for r in rows) else 0


# ---------------------------------------------------------------- decide
def cmd_decide(args) -> int:
    from unpick import decisions

    last = Path.cwd() / ".unpick" / "last-scan.json"
    if not last.is_file():
        print("unpick: no scan to decide on yet; run `unpick scan <path>` first", file=sys.stderr)
        return 2
    data = json.loads(last.read_text(encoding="utf-8"))
    pool = data["findings"] + data["accepted"]
    if args.finding_id:
        chosen = [f for f in pool if f["id"] == args.finding_id]
    else:
        chosen = [f for f in pool if (not args.rule or f["rule_id"] == args.rule)
                  and (not args.file or f["path"] == args.file or f["path"].endswith("/" + args.file))]
    if not chosen or not (args.finding_id or args.rule or args.file):
        print("unpick: no matching finding in the last scan", file=sys.stderr)
        return 2
    if args.decisions_file:
        path = Path(args.decisions_file)
    else:
        path = decisions.user_file() if args.user else decisions.project_file()
    entries = [decisions.record(path, f, args.choice, args.note or "") for f in chosen]
    _out(args, {"decisions_file": str(path), "recorded": entries},
         lambda d: console.print(f"recorded {args.choice} for {len(entries)} finding(s) in {esc(str(path))}"))
    return 0


# ---------------------------------------------------------------- demo
def cmd_demo(args) -> int:
    from unpick import demo

    try:
        dest = demo.write(Path(args.dest), force=args.force)
    except FileExistsError as e:
        print(f"unpick: {e}", file=sys.stderr)
        return 2
    _out(args, {"demo": str(dest)}, lambda d: console.print(
        f"Demo kit written to {esc(str(dest))}. Run {esc(str(dest))}/run.sh (or run.ps1 on Windows)."))
    return 0


# ---------------------------------------------------------------- backends / judges
def cmd_backends(args) -> int:
    from unpick import backends

    if args.action == "install":
        code, msg = backends.install(args.name, online=args.online, docker=args.docker)
        _out(args, {"exit_code": code, "output": msg}, lambda d: console.print(esc(msg)))
        return code
    rows = backends.describe()
    def render(rows):
        t = Table(title="Scanner backends (all optional)")
        for c in ("name", "installed", "version", "tested", "maintainer", "license", "network (as invoked)"):
            t.add_column(c, overflow="fold")
        for r in rows:
            t.add_row(r["name"], "yes" if r["installed"] else "no", esc(r["version"] or "-"), esc(r["tested_version"]),
                      esc(r["maintainer"]), r["license"], esc(r["network"]) + (" [UNVERIFIED]" if r["unverified"] else ""))
        console.print(t)
    _out(args, rows, render)
    return 0


def _adv(a: dict | None) -> str:
    if not a:
        return "not recorded"
    if a["reliable"]:
        return f"reliable ({a['recorded']})"
    return f"UNRELIABLE: fooled on {a['missed_files']} of {a['files']} files ({a['recorded']})"


def cmd_judges(args) -> int:
    from unpick import judges

    if args.action == "install":
        return _install_fallback(args)
    rows = judges.detect_all()
    def render(rows):
        t = Table(title="Judges found (a judge is one witness, never the verdict)")
        for c in ("id", "where", "found by", "consent", "usable", "adversarial corpus"):
            t.add_column(c, overflow="fold")
        for r in rows:
            t.add_row(esc(r["id"]), r["kind"] + (f" ({r['provider']})" if r.get("provider") else ""), esc(r.get("found_by", "")),
                      r["consent"], "yes" if r.get("usable", True) else esc("no: " + r.get("reason", "")), _adv(r.get("adversarial")))
        console.print(t)
        d = judges.default_judge()
        console.print(f"default for --judge auto: {esc(d) if d else 'none (no on-device judge found)'}")
    _out(args, rows, render)
    return 0


def _install_fallback(args) -> int:
    from unpick.judges import fallback

    if args.name != "fallback":
        print("unpick: only the 'fallback' judge can be installed by unpick", file=sys.stderr)
        return 2
    if not args.online:
        print(f"unpick: this installs {fallback.RUNTIME} from PyPI and downloads {fallback.FILE} "
              f"({fallback.SIZE / 1e9:.1f} GB) from huggingface.co ({fallback.REPO} @ {fallback.REVISION[:7]}); "
              "re-run with --online", file=sys.stderr)
        return 2
    code, log = fallback.install_runtime()
    if code != 0:
        print(f"unpick: could not install the runtime ({' '.join(fallback.runtime_argv()[3:])}):\n{log}", file=sys.stderr)
        return 2
    path = str(fallback.MODEL) if fallback.verified() else fallback.install(
        lambda done, total: console.print(f"\r{done / total:6.1%}", end=""))
    _out(args, {"installed": path, "sha256": fallback.SHA256, "runtime": fallback.RUNTIME},
         lambda d: console.print(f"\nverified and installed {esc(path)} and {fallback.RUNTIME}"))
    return 0


def cmd_lock(args) -> int:
    from unpick import lock

    data = lock.lock(Path(args.project), Path(args.lockfile) if args.lockfile else None)
    _out(args, {"lockfile": args.lockfile or str(Path(args.project) / lock.LOCKFILE), "components": len(data["components"])},
         lambda d: console.print(f"locked {d['components']} component(s) in {esc(d['lockfile'])}"))
    return 0


def _print_verify(r: dict) -> None:
    console.print(f"{r['unchanged']} unchanged, {len(r['changed'])} changed, {len(r['added'])} added, {len(r['removed'])} removed")
    for a in r["added"]:
        console.print(f"[yellow]added[/]   {a['kind']} {esc(a['name'])} {esc(a['display_path'])}")
    for a in r["removed"]:
        console.print(f"[dim]removed[/] {a['kind']} {esc(a['name'])} {esc(a['path'])}")
    for c in r["changed"]:
        console.print(f"[bold red]changed[/] {c['kind']} {esc(c['name'])} {esc(c['path'])}")
        if c.get("commit"):
            console.print(f"   commit {c['commit']['old']} -> {c['commit']['new']}")
        for ch in c.get("config_changes", []):
            console.print(f"   config {esc(ch['field'])}: {esc(json.dumps(ch['old']))} -> {esc(json.dumps(ch['new']))}")
        for f in c.get("files", []):
            console.print(f"   {f['status']:8} {esc(f['file'])}")
            if f.get("diff"):
                console.print(esc(f["diff"].rstrip()), highlight=False)
        if "scan" in c:
            console.print(f"   re-scan: {c['scan']['open']} open finding(s)")


def cmd_verify(args) -> int:
    from unpick import lock

    try:
        r = lock.verify(Path(args.project), Path(args.lockfile) if args.lockfile else None, rescan=not args.no_scan)
    except FileNotFoundError as e:
        print(f"unpick: {e}", file=sys.stderr)
        return 2
    if args.quiet and r["ok"]:
        return 0
    _out(args, r, _print_verify)
    return 0 if r["ok"] else 1


def _print_check(m: dict) -> None:
    console.print(f"[bold]checked {esc(m['ref'])}[/] -> quarantine id [bold]{esc(m['id'])}[/]")
    card = m["provenance"]
    if card:
        shown = {k: v for k, v in card.items() if k not in ("project_urls",) and v not in (None, "", [])}
        console.print("who made it: " + esc(", ".join(f"{k}={v}" for k, v in shown.items())))
    if m.get("provenance_error"):
        console.print(f"[yellow]{esc(m['provenance_error'])}[/]")
    if m["network"]:
        console.print("[bold]network:[/] " + esc("; ".join(m["network"])))
    for q in m["questions"]:
        console.print(f"[yellow]?[/] {esc(q)}")
    if not m["questions"] and card:
        console.print("[dim]Nothing stood out on the provenance card. That is not the same as safe.[/]")
    _print_scan(m["scan"])
    console.print(f"\nRead it raw: unpick raw \"{esc(m['root'])}/<file>\"   Approve: unpick check --approve {esc(m['id'])}")


def cmd_check(args) -> int:
    from unpick import check, consent, judges, quarantine

    consent.REMEMBER = args.remember
    try:
        if args.approve:
            r = check.approve(args.approve, Path(args.project))
            _out(args, r, lambda d: console.print(
                f"Install command (not run; run it yourself if you agree):\n  {esc(d['install_command'])}\n"
                f"Recorded in {esc(d['lockfile'])} with {d['open_findings_at_approval']} open finding(s) at approval."))
            return 0
        if not args.ref:
            print("unpick: give a URL, npm:<pkg>, pypi:<pkg>, archive or path, or --approve <id>", file=sys.stderr)
            return 2
        judge = judges.default_judge() if args.judge == "auto" else args.judge
        m = check.run(args.ref, backends=_backend_list(args.backends), judge=judge, boxed=args.boxed, offline=args.offline)
    except quarantine.Refused as e:
        print(f"unpick: refused: {e}", file=sys.stderr)
        return 2
    _out(args, m, _print_check)
    return 1 if m["scan"]["summary"]["open"] or m["questions"] else 0


def cmd_outdated(args) -> int:
    from unpick import outdated

    if not args.online:
        print("unpick: outdated asks npm, PyPI and GitHub about the components in your lockfile (by name) and "
              "fetches new git versions into quarantine; re-run with --online", file=sys.stderr)
        return 2
    try:
        rows = outdated.outdated(Path(args.project), fetch=not args.no_fetch)
    except FileNotFoundError as e:
        print(f"unpick: {e}", file=sys.stderr)
        return 2
    def render(rows):
        for r in rows:
            if r.get("error"):
                console.print(f"[yellow]{esc(r['name'])}: could not check ({esc(r['error'])})[/]")
                continue
            flag = "[bold red]newer upstream[/]" if r.get("outdated") else "current"
            console.print(f"{esc(r['name'])} ({r['kind']}): pinned {esc(str(r.get('pinned')))}, latest {esc(str(r.get('latest')))}: {flag}")
            if r.get("publisher_changed"):
                console.print(f"   [bold red]publisher changed[/]: {esc(json.dumps(r['publishers']))}")
            if r.get("moved"):
                console.print("   [bold red]repository was renamed or transferred[/]")
            if r.get("note"):
                console.print(f"   {esc(r['note'])}")
            if r.get("diff"):
                console.print(esc(r["diff"].rstrip()), highlight=False)
                console.print(f"   upstream scan: {r['scan_open']} open finding(s); copy in {esc(r['quarantine'])}")
    _out(args, rows, render)
    return 1 if any(r.get("outdated") or r.get("publisher_changed") for r in rows) else 0


def cmd_hook(args) -> int:
    from unpick import hook

    if args.action == "run":
        return hook.run(args.agent, min_severity=args.min_severity)
    r = hook.apply(args.agent, install=args.action == "install", dry_run=args.dry_run)
    def render(d):
        verb = "would change" if d["dry_run"] else "changed"
        console.print(f"{verb} {esc(d['path'])}" if d["changed"] else f"no change needed in {esc(d['path'])}")
        if d["diff"]:
            console.print(esc(d["diff"].rstrip()), highlight=False)
        if not d["dry_run"] and d["changed"]:
            console.print("[dim]A timestamped backup of the previous file sits next to it.[/]")
    _out(args, r, render)
    return 0


def cmd_watch(args) -> int:
    from unpick import watch

    if args.print_service:
        print(watch.service(args.print_service), end="")
        return 0
    if args.list:
        _out(args, [str(p) for p in watch.roots(Path(args.project))], lambda d: [console.print(esc(p)) for p in d])
        return 0
    watch.run(Path(args.project))
    return 0


def cmd_record(args) -> int:
    from unpick import flight

    try:
        flight.append({**json.loads(sys.stdin.read() or "{}"), "agent": args.agent})
    except (json.JSONDecodeError, OSError):
        pass  # the recorder must never break the agent
    return 0


def cmd_rehearse(args) -> int:
    from unpick import quarantine, rehearse

    if args.build:
        if not args.online:
            print("unpick: building the box downloads python:3.12-slim, Debian packages and llama-cpp-python; re-run with --online",
                  file=sys.stderr)
            return 2
        code, log = rehearse.build_image()
        _out(args, {"image": rehearse.IMAGE, "exit_code": code, "log": log}, lambda d: console.print(esc(d["log"][-800:])))
        return 0 if code == 0 else 2
    if not args.component:
        print("unpick: give a component path or a check id", file=sys.stderr)
        return 2
    target = Path(args.component)
    if not target.exists():
        try:
            target = Path(quarantine.load_meta(args.component)[1]["root"])
        except quarantine.Refused as e:
            print(f"unpick: {e}", file=sys.stderr)
            return 2
    try:
        r = rehearse.run(target, task=args.task, max_steps=args.max_steps, keep=args.keep, canary_dns=args.canary_dns)
    except rehearse.NotReady as e:
        print(f"unpick: {e}", file=sys.stderr)
        return 2
    def render(d):
        console.print(f"[bold]box:[/] network none, read-only root, no capabilities, fake secrets only, model {esc(d['box']['model'])}")
        for e in d["events"]:
            console.print(f"  {esc(e['ts'][11:19])} {esc(str(e['tool']))} {esc(json.dumps(e['input'])[:140])}")
        for i in d["evidence"]:
            console.print(f"  [bold red]{i['rule']}[/] {esc(i['detail'])}")
        console.print(f"\n[bold]verdict:[/] {esc(d['verdict'])}\n[dim]{esc(d['scope'])}[/]")
    _out(args, r, render)
    return 1 if r["findings"] else 0


def cmd_recover(args) -> int:
    from datetime import datetime

    from unpick import recover

    if not args.component and not args.all:
        print("unpick: name a component (or its path), or pass --all", file=sys.stderr)
        return 2
    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since)
        except ValueError:
            print("unpick: --since takes an ISO date or datetime, e.g. 2026-10-17 or 2026-10-17T09:00", file=sys.stderr)
            return 2
        if since.tzinfo is None:
            since = since.astimezone()
    r = recover.run(None if args.all else args.component, Path(args.project), since, apply=args.yes)
    def render(d):
        console.print(f"[bold]{esc(d['summary'])}[/]\n")
        console.print("[bold]1. Contain[/]")
        for x in d["contain"]:
            console.print(f"   {esc(x)}")
        for p in d["processes"]:
            console.print(f"   [red]running[/] pid {p['pid']}: {esc(p['command'])}")
        console.print("[bold]2. Rotate[/] (names and locations only)")
        for v in d["reach"]["rotate"].values():
            console.print(f"   [ ] {esc(v['provider'])}: {esc(v['what'])}. {esc(v['how'])} {esc(v['url'] or '')}")
        console.print(f"[bold]3. Agent actions that matter:[/] {len(d['timeline']['flagged'])} of {d['timeline']['events']}")
        for e in d["timeline"]["flagged"][-15:]:
            console.print(f"   {esc(str(e['ts']))} {esc(str(e['agent']))} {esc(str(e['tool']))}: {esc('; '.join(e['why']))}")
        lf = d["changed"].get("lockfile")
        console.print(f"[bold]4. Changed on disk:[/] {len(lf['changed']) if lf else 'no lockfile'}; modified since: {len(d['changed']['recent'])}")
        console.print(f"[bold]5. Egress:[/] {esc(d['egress'])}")
        for ch in d["report_to"]:
            console.print(f"[bold]6. Report to[/] {esc(ch['registry'])}: {esc(ch['url'])}")
        console.print(f"\nFull report: {esc(d['report'])}")
    _out(args, r, render)
    return 0


def cmd_ui(args) -> int:
    try:
        from unpick.ui.server import serve
    except ImportError:
        print("unpick: the UI needs the ui extra: pipx install '.[ui]'", file=sys.stderr)
        return 2
    serve(project=Path(args.project), open_browser=not args.no_browser, port=args.port)
    return 0


# ---------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="unpick", description=f"Vet AI components on your own laptop. {TAGLINE}")
    p.add_argument("--version", action="version", version=f"unpick {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    common.add_argument("--no-color", action="store_true", help="no ANSI colour")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("inventory", parents=[common], help="list AI components on this machine and in this project")
    s.add_argument("--project", default=".", help="project root (default: current directory)")
    s.add_argument("--add-path", action="append", default=[], help="extra file or folder to include")
    s.add_argument("--config", help="config file with extra locations (see docs)")
    s.add_argument("--html", help="also write a self-contained HTML report to this file")
    s.set_defaults(fn=cmd_inventory)

    s = sub.add_parser("scan", parents=[common], help="scan a file or folder")
    s.add_argument("path")
    s.add_argument("--backends", help="comma list of scanner backends, or 'installed'")
    s.add_argument("--judge", help="judge id from `unpick judges`, or 'auto' for the first on-device one")
    s.add_argument("--boxed", action="store_true", help="run each backend in a no-network box")
    s.add_argument("--online", action="store_true", help="allow backends that make network calls")
    s.add_argument("--remember", action="store_true", help="remember hosted-judge consent beyond this session")
    s.add_argument("--decisions", help="use only this decisions file")
    s.add_argument("--no-decisions", action="store_true", help="ignore recorded decisions")
    s.add_argument("--html", help="also write a self-contained HTML report to this file")
    s.set_defaults(fn=cmd_scan)

    s = sub.add_parser("raw", parents=[common], help="show a Markdown file rendered vs raw, line by line")
    s.add_argument("file")
    s.set_defaults(fn=cmd_raw)

    s = sub.add_parser("decide", parents=[common], help="record accept / reject / ask-author for a finding from the last scan")
    s.add_argument("finding_id", nargs="?", help="finding id from the last scan")
    s.add_argument("choice", choices=["accept", "reject", "ask-author"])
    s.add_argument("--note", default="")
    s.add_argument("--rule", help="select findings by rule id instead of id")
    s.add_argument("--file", help="select findings by file path instead of id")
    s.add_argument("--user", action="store_true", help="store in ~/.unpick instead of the project")
    s.add_argument("--decisions-file", help="store in this file")
    s.set_defaults(fn=cmd_decide)

    s = sub.add_parser("demo", parents=[common], help="write the talk's demo kit")
    s.add_argument("dest", nargs="?", default="demo")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_demo)

    s = sub.add_parser("backends", parents=[common], help="list or install scanner backends")
    s.add_argument("action", nargs="?", choices=["list", "install"], default="list")
    s.add_argument("name", nargs="?")
    s.add_argument("--online", action="store_true", help="allow the download that install needs")
    s.add_argument("--docker", action="store_true", help="build a Docker image for --boxed instead of installing on the host")
    s.set_defaults(fn=cmd_backends)

    s = sub.add_parser("lock", parents=[common], help="pin every inventoried component with per-file hashes")
    s.add_argument("--project", default=".")
    s.add_argument("--lockfile")
    s.set_defaults(fn=cmd_lock)

    s = sub.add_parser("verify", parents=[common], help="compare this machine with the lockfile; diff and re-scan what changed")
    s.add_argument("--project", default=".")
    s.add_argument("--lockfile")
    s.add_argument("--no-scan", action="store_true", help="skip re-scanning changed components (faster)")
    s.add_argument("--quiet", action="store_true", help="print nothing when everything matches (for shell start)")
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("outdated", parents=[common], help="newer upstream versions of locked components, with a diff and scan")
    s.add_argument("--project", default=".")
    s.add_argument("--online", action="store_true", help="required: this asks registries and GitHub")
    s.add_argument("--no-fetch", action="store_true", help="report only; do not fetch new git versions")
    s.set_defaults(fn=cmd_outdated)

    s = sub.add_parser("check", parents=[common], help="fetch into quarantine, show who made it, scan; never installs")
    s.add_argument("ref", nargs="?", help="GitHub/git URL, npm:<pkg>[@v], pypi:<pkg>[==v], archive or path")
    s.add_argument("--approve", metavar="ID", help="print the install command for a checked component and lock it")
    s.add_argument("--offline", action="store_true", help="skip the provenance lookup (fetching a URL still needs the network)")
    s.add_argument("--backends")
    s.add_argument("--judge")
    s.add_argument("--boxed", action="store_true")
    s.add_argument("--remember", action="store_true")
    s.add_argument("--project", default=".")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("hook", parents=[common], help="install, remove or run the pre-install hook for an agent")
    s.add_argument("action", choices=["install", "uninstall", "run"])
    s.add_argument("agent", choices=["claude-code", "codex", "cursor"])
    s.add_argument("--dry-run", action="store_true", help="show the settings change without writing it")
    s.add_argument("--min-severity", choices=["low", "medium", "high"], default=None,
                   help="block at this severity or above (default high, or $UNPICK_HOOK_MIN_SEVERITY)")
    s.set_defaults(fn=cmd_hook)

    s = sub.add_parser("watch", parents=[common], help="scan AI components as they land (a backstop to the hook)")
    s.add_argument("--project", default=".")
    s.add_argument("--list", action="store_true", help="show the folders that would be watched")
    s.add_argument("--print-service", choices=["launchd", "systemd", "windows"], help="print a run-at-login recipe")
    s.set_defaults(fn=cmd_watch)

    s = sub.add_parser("record", parents=[common], help="flight recorder: append the hook event on stdin to ~/.unpick/flight")
    s.add_argument("--agent", default="claude-code")
    s.set_defaults(fn=cmd_record)

    for alias in ("rehearse", "detonate"):
        s = sub.add_parser(alias, parents=[common], help="first run in a no-network box with fake secrets (alias: detonate)"
                           if alias == "rehearse" else argparse.SUPPRESS)
        s.add_argument("component", nargs="?", help="component path, or a check id from `unpick check`")
        s.add_argument("--task", default="Summarise the README in this folder.")
        s.add_argument("--max-steps", type=int, default=8)
        s.add_argument("--keep", action="store_true", help="keep the box's home and trace folder for inspection")
        s.add_argument("--canary-dns", metavar="EMAIL_OR_WEBHOOK",
                       help="NETWORK, opt-in: create a free canarytokens.org DNS token and plant it in the fake .env")
        s.add_argument("--build", action="store_true", help="build the box image (needs --online, once)")
        s.add_argument("--online", action="store_true")
        s.set_defaults(fn=cmd_rehearse)

    s = sub.add_parser("recover", parents=[common], help="incident runbook: contain, rotate, what happened, report")
    s.add_argument("component", nargs="?", help="component name or path")
    s.add_argument("--all", action="store_true", help="no single suspect: run every step for the whole machine")
    s.add_argument("--since", help="start of the window (ISO date or datetime)")
    s.add_argument("--yes", action="store_true", help="actually contain (move the component, edit configs with backups)")
    s.add_argument("--project", default=".")
    s.set_defaults(fn=cmd_recover)

    s = sub.add_parser("ui", parents=[common], help="open the local web UI (127.0.0.1 only)")
    s.add_argument("--project", default=".")
    s.add_argument("--port", type=int, help="fixed port instead of a random free one")
    s.add_argument("--no-browser", action="store_true")
    s.set_defaults(fn=cmd_ui)

    s = sub.add_parser("judges", parents=[common], help="list the AI judges on this machine, or install the fallback judge")
    s.add_argument("action", nargs="?", choices=["list", "install"], default="list")
    s.add_argument("name", nargs="?")
    s.add_argument("--online", action="store_true", help="allow the model download that install needs")
    s.set_defaults(fn=cmd_judges)
    return p


def main(argv: list[str] | None = None) -> int:
    global console
    argv = list(sys.argv[1:] if argv is None else argv)
    # `decide accept` without an id: argparse would read "accept" as the id.
    if argv[:1] == ["decide"] and len(argv) > 1 and argv[1] in ("accept", "reject", "ask-author"):
        argv.insert(1, "")
    args = build_parser().parse_args(argv)
    console = Console(no_color=args.no_color, highlight=False, soft_wrap=False)
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        return 2
