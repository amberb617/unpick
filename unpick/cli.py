"""Command line. Every command calls the same functions the UI does, and every command has --json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.markup import escape as esc
from rich.table import Table

from unpick import __version__

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
def _print_scan(d: dict, *, args=None, saved: bool = False, headline: str | None = None, lead: bool = True) -> None:
    """The collapsed view of a scan (unpick.scan_output), with the on-device summary when it is wanted."""
    from unpick import scan_output, summary

    lines, note = summary.pick(d) if args is not None and summary.wanted(args) and d.get("findings") else ([], "")
    scan_output.render(console, d, details=getattr(args, "details", False), rule=getattr(args, "rule", None),
                       severity=getattr(args, "severity", None), where=getattr(args, "place", None),
                       summary=lines, summary_label=summary.LABEL, saved=saved, headline=headline, lead=lead)
    if note:
        console.print(f"[dim]{esc(note)}[/]")


def cmd_explain(args) -> int:
    from dataclasses import asdict

    from unpick.explain import get_explanation

    try:
        entry = get_explanation(args.rule_id)
    except KeyError:
        print(f"unpick: unknown rule {args.rule_id!r}; use a rule ID from your scan", file=sys.stderr)
        return 2

    def show(data):
        console.print(data["title"], markup=False)
        console.print(data["what_it_means"], markup=False)
        console.print("Next step: " + data["what_to_do"], markup=False)

    _out(args, asdict(entry), show)
    return 0


def _backend_list(arg: str | None) -> list[str]:
    from unpick import backends

    if not arg:
        return []
    if arg == "installed":
        return [r["name"] for r in backends.describe() if r["installed"] and not r["needs_online"]]
    return [b.strip() for b in arg.split(",") if b.strip()]



def _scan_display_data(data: dict, requested_judge: str | None, selected_judge: str | None) -> dict:
    """Keep JSON and exit codes stable while showing missing auto reviews in human exports."""
    if requested_judge == "auto" and not selected_judge:
        return {**data, "unavailable": [*data["unavailable"], "on-device AI reviewer (--judge auto)"]}
    return data

def cmd_scan(args) -> int:
    from unpick import consent, decisions, judges, scan

    consent.REMEMBER = args.remember
    judge = args.judge
    if judge == "auto":
        judge = judges.default_judge()
    if args.no_decisions:
        files = []
    elif args.decisions:
        files = [Path(args.decisions)]
    else:
        files = [decisions.project_file(), decisions.user_file()]
    target = Path(args.path)
    if not target.exists():
        message = f"unpick: {target} does not exist"
        if not args.json:
            message = (f"Cannot assess this: {str(target)!r} does not exist; "
                       "run `unpick scan --help` to choose a file or folder.")
        print(message, file=sys.stderr)
        return 2
    res = scan.scan(target, backends=_backend_list(args.backends), judge=judge, boxed=args.boxed,
                    online=args.online, decision_files=files)
    scan.save_last(res)
    if args.html:
        from unpick import report
        report.write(Path(args.html), report.scan_html(_scan_display_data(res.to_dict(), args.judge, judge)))
    def show(data):
        _print_scan(_scan_display_data(data, args.judge, judge), args=args)
    _out(args, res.to_dict(), show)
    return res.exit_code


def _last_scan() -> dict | None:
    last = Path.cwd() / ".unpick" / "last-scan.json"
    return json.loads(last.read_text(encoding="utf-8")) if last.is_file() else None


def cmd_results(args) -> int:
    d = _last_scan()
    if d is None:
        print("unpick: no saved scan here yet; run `unpick scan <path>` in this folder first", file=sys.stderr)
        return 2
    _out(args, d, lambda data: _print_scan(data, args=args, saved=True))
    return 0


def cmd_show(args) -> int:
    import textwrap

    from unpick import digest
    from unpick.render import escape as raw_escape

    d = _last_scan()
    f = next((x for x in (d or {}).get("findings", []) + (d or {}).get("accepted", []) if x["id"] == args.finding_id), None)
    if f is None:
        print(f"unpick: no finding {args.finding_id!r} in the last scan here; run `unpick results` to list them", file=sys.stderr)
        return 2

    def render(f):
        e = digest._explanation(f["rule_id"])
        console.print(f"[bold]{esc(e.title.rstrip('.'))}[/]")
        console.print(f"[dim]Scan of {esc(d.get('target', ''))}, saved {esc(d.get('started_at', '')[:16])}[/]")
        console.print(f"{f['severity']}  {f['rule_id']}  {esc(raw_escape(f['path']))}:{f.get('line') or '-'}  id {f['id']}")
        console.print(esc(raw_escape(f["message"])))
        width = max(40, console.width)
        for c in f.get("context", []):
            mark = ">" if c["line"] == f.get("line") else " "
            head = f"  {mark} {c['line']:>5} | "
            text = raw_escape(c["text"]) or " "
            console.print(esc(textwrap.fill(text, width, initial_indent=head, subsequent_indent=" " * (len(head) - 2) + "| ",
                                            drop_whitespace=False, replace_whitespace=False)))
        console.print(f"\nWhat it means: {esc(e.what_it_means)}")
        console.print(f"Why it was flagged: {esc(f.get('why', ''))}")
        console.print(f"May be legitimate when: {esc(f.get('false_positive', ''))}")
        console.print(f"Next: {esc(e.what_to_do)}")
        console.print("\nRecord a decision, one of:")
        for choice in ("accept", "reject", "ask-author"):
            console.print(f"  unpick decide {f['id']} {choice}")
    _out(args, f, render)
    return 0


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


def _connect_jiffy(args) -> int:
    from unpick import integrations

    key = None
    if not args.browser:
        if not sys.stdin.isatty():
            print("unpick: connecting asks for your key; run it in a terminal, or set JIFFY_TOKEN", file=sys.stderr)
            return 2
        import getpass
        console.print(f"Create a key at {integrations.JIFFY_KEYS_URL}\n"
                      "It goes to the Jiffy CLI, which checks it and saves it for your user. unpick does not keep it.")
        key = getpass.getpass("Jiffy API key (hidden; press Enter alone to sign in with your browser instead): ").strip() or None
    code, msg = integrations.connect_jiffy(key)
    if msg:
        console.print(esc(msg))
    if code == 0:
        console.print("Jiffy accepted the key. Use it with: unpick scan <path> --backends jiffy --online")
    return code


def cmd_integrations(args) -> int:
    from unpick import integrations

    if args.action == "connect":
        return _connect_jiffy(args)
    if args.action == "check":
        code, msg = integrations.check_jiffy()
        if msg:
            console.print(esc(msg))
        console.print("Jiffy accepted the saved key." if code == 0 else
                      "Jiffy did not accept it. Run: unpick integrations connect jiffy")
        return 0 if code == 0 else 1
    if args.action == "disconnect":
        code, msg = integrations.disconnect_jiffy()
        console.print(esc(msg) or "Jiffy disconnected.")
        return code
    def render(rows):
        t = Table(title="Scanning integrations (all optional)")
        for c in ("name", "kind", "status", "what leaves your machine", "set up with"):
            t.add_column(c, overflow="fold")
        for r in rows:
            t.add_row(r["name"], r["kind"], ("[green]" if r["ready"] else "[yellow]") + esc(r["status"]) + "[/]",
                      esc(r["network"]), esc("unpick " + " ".join(r["action"])) if r["action"] else "")
        console.print(t)
        console.print("[dim]Network scanners and hosted AI review only run when you pass --online or --judge.[/]")
    _out(args, integrations.rows(), render)
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
    from unpick.render import scan_verdict

    # questions about the source and provenance errors are the check's to report; the scan cannot see them
    console.print(scan_verdict(m["scan"], questions=bool(m["questions"]), provenance_error=bool(m.get("provenance_error"))),
                  style="bold", markup=False, soft_wrap=True)
    console.print(f"[bold]checked {esc(m['ref'])}[/] -> quarantine id [bold]{esc(m['id'])}[/]")
    console.print("Scanned copy: " + esc(m["root"]))
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
    console.print()
    _print_scan(m["scan"], lead=False)


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
        last = Path.cwd() / ".unpick" / "last-scan.json"
        last.parent.mkdir(parents=True, exist_ok=True)
        last.write_text(json.dumps(m["scan"], indent=2, ensure_ascii=False), encoding="utf-8")
    except quarantine.Refused as e:
        message = f"unpick: refused: {e}"
        if not args.json:
            message = f"Cannot assess this: the check was refused; run `unpick check --help` before retrying.\nReason: {e}"
        print(message, file=sys.stderr)
        return 2
    except OSError as e:
        print(f"unpick: could not fetch it: {e}", file=sys.stderr)
        return 2
    def show(data):
        _print_check({**data, "scan": _scan_display_data(data["scan"], args.judge, judge)})
    _out(args, m, show)
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
    import os

    from unpick import hook

    if args.action == "run":
        if args.fail_open:
            os.environ["UNPICK_HOOK_FAIL_OPEN"] = "1"
        return hook.run(args.agent, min_severity=args.min_severity)
    r = hook.apply(args.agent, install=args.action == "install", dry_run=args.dry_run,
                   min_severity=args.min_severity, fail_open=args.fail_open)
    def render(d):
        verb = "would change" if d["dry_run"] else "changed"
        console.print(f"{verb} {esc(d['path'])}" if d["changed"] else f"no change needed in {esc(d['path'])}")
        if d["diff"]:
            console.print(esc(d["diff"].rstrip()), highlight=False)
        if not d["dry_run"] and d["changed"]:
            console.print("[dim]A timestamped backup of the previous file sits next to it.[/]")
    _out(args, r, render)
    return 0


def _ask(question: str, choices: list[str], default: str) -> str:
    shown = "/".join(c.upper() if c == default else c for c in choices)
    while True:
        try:
            a = input(f"{question} [{shown}] ").strip().lower() or default
        except EOFError:
            raise KeyboardInterrupt from None  # Ctrl-D quits like Ctrl-C, before anything is written
        if a in choices:
            return a
        match = [c for c in choices if c.startswith(a)]
        if len(match) == 1:
            return match[0]


def _print_setup_plan(p: dict) -> None:
    for h in p["hooks"]:
        console.print(f"\n[bold]{'change' if h['changed'] else 'already set'}:[/] {esc(h['path'])}")
        if h["diff"]:
            console.print(esc(h["diff"].rstrip()), highlight=False)
    if p["service"]:
        s = p["service"]
        if s["file"]:
            console.print(f"\n[bold]write:[/] {esc(s['file'])}")
        for cmd in s["commands"]:
            console.print(f"[bold]run:[/] {esc(' '.join(cmd))}")


def cmd_setup(args) -> int:
    import os

    from unpick import setup

    if args.undo:
        r = setup.undo()
        _out(args, r, lambda d: console.print(
            "\n".join([f"removed the hook from {esc(h['path'])}" for h in d["hooks"]]
                      + (["stopped and removed the background watcher"] if d["service_removed"] else [])) or "nothing to remove"))
        return 0
    if not sys.stdin.isatty() or os.environ.get("UNPICK_NONINTERACTIVE"):
        print("unpick: setup asks questions; run it in a terminal, or use `unpick hook install <agent>`", file=sys.stderr)
        return 2
    found = setup.detected()
    console.print("Agents found: " + (", ".join(setup.AGENTS[a][0] for a in found) or
                                      "none of Claude Code, Codex CLI or Cursor"))
    if not setup.can_watch():
        console.print("[dim]" + esc("The background watcher needs the watch extra: pipx install 'unpick[watch]'") + "[/]")
    choices = setup.interview(_ask)
    p = setup.plan(choices)
    if not p["hooks"] and not p["service"]:
        console.print("Nothing to set up.")
        return 0
    console.print("\n[bold]This is everything setup will change.[/] Settings files are backed up first.")
    _print_setup_plan(p)
    if args.dry_run or _ask("\nMake these changes?", ["y", "n"], "n") != "y":
        console.print("Nothing changed.")
        return 0
    r = setup.apply(choices)
    for h in r["hooks"]:
        console.print(f"hooked {esc(h['path'])}")
    if r["service"]:
        for e in r["service"]["errors"]:
            console.print(f"[red]watcher did not start:[/] {esc(e)}")
        if not r["service"]["errors"]:
            console.print("background watcher running, and it starts at login")
    console.print("Undo all of it: unpick setup --undo")
    return 1 if r["service"] and r["service"]["errors"] else 0


def cmd_watch(args) -> int:
    from unpick import watch

    if args.print_service:
        print(watch.service(args.print_service), end="")
        return 0
    if args.list:
        _out(args, [str(p) for p in watch.roots(Path(args.project))], lambda d: [console.print(esc(p)) for p in d])
        return 0
    watch.run(Path(args.project), quarantine_at=args.quarantine)
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


def cmd_report(args) -> int:
    from unpick import decisions, inventory, judges, report, scan

    judge = judges.default_judge() if args.judge == "auto" else args.judge
    res = scan.scan(Path(args.path), backends=_backend_list(args.backends), judge=judge, boxed=args.boxed)
    d = res.to_dict()
    inv = inventory.discover(project=Path(args.project)) if args.inventory else None
    reh = json.loads(Path(args.rehearse_json).read_text(encoding="utf-8")) if args.rehearse_json else None
    decided = [x for p in (decisions.project_file(), decisions.user_file()) if p.is_file()
               for x in json.loads(p.read_text(encoding="utf-8")).get("decisions", [])]
    doc = report.full_html(d, inv, reh, decided)
    report.write(Path(args.html), doc)
    _out(args, {"html": args.html, "open": d["summary"]["open"], "accepted": d["summary"]["accepted"]},
         lambda x: console.print(f"wrote {esc(x['html'])}: {x['open']} open, {x['accepted']} accepted"))
    return 0


def cmd_quarantine(args) -> int:
    from unpick import inventory, isolate

    if args.list or not args.target:
        rows = isolate.isolated()
        _out(args, rows, lambda d: [console.print(f"{esc(r['id'])}  {esc(r['name'])}  from {esc(r['original'])}"
                                                   f"{'#' + esc(r['entry']) if r.get('entry') else ''}  ({esc(r.get('reason') or '')})") for r in d]
             or console.print("Nothing in quarantine."))
        return 0
    p = Path(args.target).expanduser()
    if p.exists():
        matches = [{"path": str(p.resolve()), "name": p.name}]
    else:
        matches = [c for c in inventory.discover(project=Path(args.project)) if c["name"] == args.target]
    if not matches:
        print(f"unpick: no file, folder or installed add-on called {args.target}", file=sys.stderr)
        return 2
    if len(matches) > 1:
        print(f"unpick: {len(matches)} add-ons are called {args.target}; give the path instead", file=sys.stderr)
        return 2
    try:
        r = isolate.isolate(matches[0], reason=args.reason or "quarantined by hand")
    except isolate.CannotIsolate as e:
        print(f"unpick: {e}", file=sys.stderr)
        return 2
    _out(args, r, lambda d: console.print(f"moved {esc(d['name'])} into quarantine as {esc(d['id'])}. Undo: unpick restore {esc(d['id'])}"))
    return 0


def cmd_restore(args) -> int:
    from unpick import isolate

    try:
        msg = isolate.restore(args.id)
    except isolate.CannotIsolate as e:
        print(f"unpick: {e}", file=sys.stderr)
        return 2
    _out(args, {"restored": args.id, "message": msg}, lambda d: console.print(esc(d["message"])))
    return 0


def cmd_clean(args) -> int:
    from unpick import clean

    try:
        r = clean.clean(Path(args.path), Path(args.out) if args.out else None)
    except (FileExistsError, FileNotFoundError) as e:
        print(f"unpick: {e}", file=sys.stderr)
        return 2
    def render(d):
        n = sum(len(v) for v in d["changes"].values())
        console.print(f"wrote a cleaned copy to {esc(d['clean'])} ({n} change(s)); the original is unchanged")
        for rel, changes in d["changes"].items():
            for c in changes:
                console.print(f"   {esc(rel)}: {esc(c)}")
        console.print(f"still flagged after cleaning: {len(d['still_flagged'])}; details in {esc(d['report'])}")
    _out(args, r, render)
    return 1 if r["still_flagged"] else 0


def cmd_ui(args) -> int:
    try:
        from unpick.ui.server import serve
    except ImportError:
        print("unpick: the UI needs the ui extra: pipx install '.[ui]'", file=sys.stderr)
        return 2
    serve(project=Path(args.project), open_browser=not args.no_browser, port=args.port)
    return 0


# ---------------------------------------------------------------- main
def _view_flags(s) -> None:
    s.add_argument("--details", action="store_true", help="list every finding under its group")
    s.add_argument("--rule", help="only this rule, e.g. RT-SENSITIVE-PATH")
    s.add_argument("--severity", choices=["high", "medium", "low"], help="only this severity")
    s.add_argument("--place", choices=["code", "docs/config", "other"], help="only findings in this kind of file")
    s.add_argument("--no-summary", action="store_true", help="skip the on-device summary at the top")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="unpick", usage="unpick [-h] [--version] COMMAND ...",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""Check AI add-ons before trusting them.

Start here:
  check         Inspect a copy before installing; nothing is installed.
                Example: unpick check ./downloaded-skill
  scan          Review a file or folder already on your computer.
                Example: unpick scan ./my-project
  hook install  Add checks before your agent installs add-ons.
                Example: unpick hook install claude-code

Use unpick COMMAND --help for options.""")
    p.add_argument("--version", action="version", version=f"unpick {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    common.add_argument("--no-color", action="store_true", help="no ANSI colour")
    sub = p.add_subparsers(dest="cmd", title="More commands", metavar="COMMAND")

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
    _view_flags(s)
    s.set_defaults(fn=cmd_scan)

    s = sub.add_parser("results", parents=[common], help="show the last scan saved in this folder again, without rescanning")
    _view_flags(s)
    s.set_defaults(fn=cmd_results)

    s = sub.add_parser("show", parents=[common], help="one finding from the last scan, with the lines around it")
    s.add_argument("finding_id")
    s.set_defaults(fn=cmd_show)

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
    s.add_argument("--fail-open", action="store_true", help="allow installs unpick cannot check, with a warning")
    s.set_defaults(fn=cmd_hook)

    s = sub.add_parser("integrations", parents=[common], help="see and connect scanning integrations (Jiffy, scanners, AI review)")
    s.add_argument("action", nargs="?", choices=["list", "connect", "check", "disconnect"], default="list")
    s.add_argument("name", nargs="?", choices=["jiffy"], help="the integration to connect, check or disconnect")
    s.add_argument("--browser", action="store_true", help="sign in to Jiffy in your browser instead of pasting a key")
    s.set_defaults(fn=cmd_integrations)

    s = sub.add_parser("setup", parents=[common], help="first run: pick which agents to protect, see every change, then apply")
    s.add_argument("--dry-run", action="store_true", help="ask the questions and show the changes without making them")
    s.add_argument("--undo", action="store_true", help="remove every hook and the background watcher setup added")
    s.set_defaults(fn=cmd_setup)

    s = sub.add_parser("watch", parents=[common], help="scan AI components as they land (a backstop to the hook)")
    s.add_argument("--project", default=".")
    s.add_argument("--list", action="store_true", help="show the folders that would be watched")
    s.add_argument("--print-service", choices=["launchd", "systemd", "windows"], help="print a run-at-login recipe")
    s.add_argument("--quarantine", choices=["high", "medium"], help="opt-in: move add-ons with warnings at this severity out of the agent's reach")
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

    s = sub.add_parser("report", parents=[common], help="one self-contained HTML report: scan, judges, rehearse, decisions, inventory")
    s.add_argument("path")
    s.add_argument("--html", required=True, help="output file")
    s.add_argument("--inventory", action="store_true", help="include the machine's inventory")
    s.add_argument("--rehearse-json", help="include a saved `unpick rehearse --json` result")
    s.add_argument("--backends")
    s.add_argument("--judge")
    s.add_argument("--boxed", action="store_true")
    s.add_argument("--project", default=".")
    s.set_defaults(fn=cmd_report)

    s = sub.add_parser("quarantine", parents=[common], help="move an add-on out of your agent's reach (undo with restore)")
    s.add_argument("target", nargs="?", help="path, or the name of an installed add-on")
    s.add_argument("--list", action="store_true", help="show what is in quarantine")
    s.add_argument("--reason", default="")
    s.add_argument("--project", default=".")
    s.set_defaults(fn=cmd_quarantine)

    s = sub.add_parser("restore", parents=[common], help="put a quarantined add-on back where it was")
    s.add_argument("id")
    s.set_defaults(fn=cmd_restore)

    s = sub.add_parser("clean", parents=[common], help="write a cleaned copy: hidden text removed, decode-and-run lines disabled")
    s.add_argument("path")
    s.add_argument("--out", help="where to write the copy (default: next to it, .unpick-clean)")
    s.set_defaults(fn=cmd_clean)

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
    s = sub.add_parser("explain", parents=[common], help="explain a finding and what to do next")
    s.add_argument("rule_id", help="rule ID shown under a finding, for example RT-UNICODE")
    s.set_defaults(fn=cmd_explain)
    # Keep all parsers available while showing the three entry points only once.
    sub._choices_actions = [a for a in sub._choices_actions
                            if a.dest not in {"check", "scan", "hook"} and a.help != argparse.SUPPRESS]
    return p


def _home(parser) -> int:
    """`unpick` alone: the home screen in a terminal with the tui extra, otherwise the command list."""
    import importlib.util
    import os

    if sys.stdin.isatty() and sys.stdout.isatty() and not os.environ.get("UNPICK_NONINTERACTIVE"):
        if importlib.util.find_spec("textual"):
            from unpick import tui
            tui.run()
            return 0
        parser.print_help()
        print("\nFor the home screen: pipx install 'unpick[tui]'")
        return 0
    parser.print_help()
    return 0


def main(argv: list[str] | None = None) -> int:
    global console
    argv = list(sys.argv[1:] if argv is None else argv)
    # `decide accept` without an id: argparse would read "accept" as the id.
    if argv[:1] == ["decide"] and len(argv) > 1 and argv[1] in ("accept", "reject", "ask-author"):
        argv.insert(1, "")
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        return _home(parser)
    console = Console(no_color=args.no_color, highlight=False, soft_wrap=False)
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        return 2
