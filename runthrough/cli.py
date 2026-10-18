"""Command line. Every command calls the same functions the UI does, and every command has --json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.markup import escape as esc
from rich.table import Table

from runthrough import TAGLINE, __version__

SEV_STYLE = {"high": "bold red", "medium": "yellow", "low": "cyan", "info": "dim"}
console = Console()


def _out(args, data, render):
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        render(data)


# ---------------------------------------------------------------- inventory
def cmd_inventory(args) -> int:
    from runthrough import inventory

    items = inventory.discover(project=Path(args.project), extra=[Path(p) for p in args.add_path],
                               config=Path(args.config) if args.config else None)
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
            from runthrough.render import escape as raw_escape
            console.print(f"         [dim]> {esc(raw_escape(f['matched'])[:160])}[/]")
        console.print(f"         [dim]why: {esc(f['why'])}[/]")
        console.print(f"         [dim]false positive when: {esc(f['false_positive'])}[/]")
    s = d["summary"]
    console.print(f"\n[bold]{s['open']} open finding(s), {s['accepted']} accepted.[/] By source: {s['by_source']}")
    if len(d["sources"]) > 1:
        console.print(f"Agreement (Jaccard on file+line): {s['agreement']}")
    if s["open"]:
        console.print("[dim]Record a decision: runthrough decide <id> accept|reject|ask-author --note \"...\"[/]")


def _backend_list(arg: str | None) -> list[str]:
    from runthrough import backends

    if not arg:
        return []
    if arg == "installed":
        return [r["name"] for r in backends.describe() if r["installed"] and not r["needs_online"]]
    return [b.strip() for b in arg.split(",") if b.strip()]


def cmd_scan(args) -> int:
    from runthrough import consent, decisions, judges, scan

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
        print(f"runthrough: {target} does not exist", file=sys.stderr)
        return 2
    res = scan.scan(target, backends=_backend_list(args.backends), judge=judge, boxed=args.boxed,
                    online=args.online, decision_files=files)
    scan.save_last(res)
    _out(args, res.to_dict(), _print_scan)
    return res.exit_code


# ---------------------------------------------------------------- raw
def cmd_raw(args) -> int:
    from runthrough import render

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
    from runthrough import decisions

    last = Path.cwd() / ".runthrough" / "last-scan.json"
    if not last.is_file():
        print("runthrough: no scan to decide on yet; run `runthrough scan <path>` first", file=sys.stderr)
        return 2
    data = json.loads(last.read_text(encoding="utf-8"))
    pool = data["findings"] + data["accepted"]
    if args.finding_id:
        chosen = [f for f in pool if f["id"] == args.finding_id]
    else:
        chosen = [f for f in pool if (not args.rule or f["rule_id"] == args.rule)
                  and (not args.file or f["path"] == args.file or f["path"].endswith("/" + args.file))]
    if not chosen or not (args.finding_id or args.rule or args.file):
        print("runthrough: no matching finding in the last scan", file=sys.stderr)
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
    from runthrough import demo

    try:
        dest = demo.write(Path(args.dest), force=args.force)
    except FileExistsError as e:
        print(f"runthrough: {e}", file=sys.stderr)
        return 2
    _out(args, {"demo": str(dest)}, lambda d: console.print(
        f"Demo kit written to {esc(str(dest))}. Run {esc(str(dest))}/run.sh (or run.ps1 on Windows)."))
    return 0


# ---------------------------------------------------------------- backends / judges
def cmd_backends(args) -> int:
    from runthrough import backends

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


def cmd_judges(args) -> int:
    from runthrough import judges

    if args.action == "install":
        return _install_fallback(args)
    rows = judges.detect_all()
    def render(rows):
        t = Table(title="Judges found (a judge is one witness, never the verdict)")
        for c in ("id", "where", "found by", "consent", "usable"):
            t.add_column(c, overflow="fold")
        for r in rows:
            t.add_row(esc(r["id"]), r["kind"] + (f" ({r['provider']})" if r.get("provider") else ""), esc(r.get("found_by", "")),
                      r["consent"], "yes" if r.get("usable", True) else esc("no: " + r.get("reason", "")))
        console.print(t)
        d = judges.default_judge()
        console.print(f"default for --judge auto: {esc(d) if d else 'none (no on-device judge found)'}")
    _out(args, rows, render)
    return 0


def _install_fallback(args) -> int:
    from runthrough.judges import fallback

    if args.name != "fallback":
        print("runthrough: only the 'fallback' judge can be installed by runthrough", file=sys.stderr)
        return 2
    if not args.online:
        print(f"runthrough: this downloads {fallback.FILE} ({fallback.SIZE / 1e9:.1f} GB) from huggingface.co "
              f"({fallback.REPO} @ {fallback.REVISION[:7]}); re-run with --online", file=sys.stderr)
        return 2
    path = fallback.install(lambda done, total: console.print(f"\r{done / total:6.1%}", end=""))
    _out(args, {"installed": path, "sha256": fallback.SHA256},
         lambda d: console.print(f"\nverified and installed {esc(path)}. Runtime: pip install {fallback.INSTALL_RUNTIME}"))
    return 0


# ---------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="runthrough", description=f"Vet AI components on your own laptop. {TAGLINE}")
    p.add_argument("--version", action="version", version=f"runthrough {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    common.add_argument("--no-color", action="store_true", help="no ANSI colour")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("inventory", parents=[common], help="list AI components on this machine and in this project")
    s.add_argument("--project", default=".", help="project root (default: current directory)")
    s.add_argument("--add-path", action="append", default=[], help="extra file or folder to include")
    s.add_argument("--config", help="config file with extra locations (see docs)")
    s.set_defaults(fn=cmd_inventory)

    s = sub.add_parser("scan", parents=[common], help="scan a file or folder")
    s.add_argument("path")
    s.add_argument("--backends", help="comma list of scanner backends, or 'installed'")
    s.add_argument("--judge", help="judge id from `runthrough judges`, or 'auto' for the first on-device one")
    s.add_argument("--boxed", action="store_true", help="run each backend in a no-network box")
    s.add_argument("--online", action="store_true", help="allow backends that make network calls")
    s.add_argument("--remember", action="store_true", help="remember hosted-judge consent beyond this session")
    s.add_argument("--decisions", help="use only this decisions file")
    s.add_argument("--no-decisions", action="store_true", help="ignore recorded decisions")
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
    s.add_argument("--user", action="store_true", help="store in ~/.runthrough instead of the project")
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
