"""The Textual screens behind `unpick` with no arguments. Imported only when Textual is installed; the data
they show comes from unpick.tui, which needs nothing extra."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.theme import Theme
from textual.widgets import DataTable, Footer, Input, Label, Static

from unpick import TAGLINE, __version__, inventory, scan
from unpick.tui import BUCKETS, COLOR, alerts, bars, bucket, next_steps, places, protection, watcher

THEME = Theme(name="unpick", primary="#ff97bf", secondary="#95adda", accent="#ff97bf", foreground="#e7eefa",
              background="#040e27", surface="#09132d", panel="#0e182b", warning="#ffc000", error="#ff4e4e",
              success="#5a935a", dark=True)


def hand_over(app, argv: list[str]) -> None:
    """Give the terminal to a CLI command, wait for Enter, come back."""
    from unpick import cli
    with app.suspend():
        try:
            cli.main(argv)
        except SystemExit:
            pass
        try:
            input("\nPress Enter to go back to unpick. ")
        except (EOFError, KeyboardInterrupt):
            pass

class Card(Vertical, can_focus=True):
    pass

class AskRef(ModalScreen[str]):
    BINDINGS = [Binding("escape", "dismiss('')", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="ask"):
            yield Label("What do you want to check?")
            yield Label("A GitHub URL, npm:<pkg>, pypi:<pkg>, an archive or a folder.", classes="muted")
            yield Input(placeholder="https://github.com/owner/skill")

    @on(Input.Submitted)
    def done(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())

class AddOns(Screen):
    BINDINGS = [Binding("escape,q", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("[b]Add-ons on this machine[/]  worst first. Enter shows the full scan.", id="bar")
        yield DataTable(cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        t = self.query_one(DataTable)
        t.add_columns("worst", "kind", "host", "name", "path")
        app = self.app
        order = {b: i for i, b in enumerate(BUCKETS)}
        rows = sorted(app.items, key=lambda i: order.get(app.results.get(i["path"], "not scanned yet"), 9))
        self.paths = [i["path"] for i in rows]  # several MCP servers can share one config file, so rows key by position
        for i in rows:
            b = app.results.get(i["path"], "not scanned yet")
            t.add_row(Text(b, style=COLOR.get(b, "#95adda")), i["kind"], i["host"], i["name"], i["display_path"])

    @on(DataTable.RowSelected)
    def scan_row(self, event: DataTable.RowSelected) -> None:
        hand_over(self.app, ["scan", self.paths[event.cursor_row]])

class Home(App):
    TITLE = "unpick"
    CSS = """
    Screen { background: #040e27; color: #e7eefa; }
    #bar { dock: top; height: 1; background: #09132d; color: #95adda; padding: 0 1; }
    #hello { padding: 1 4 0 4; height: auto; }
    #cards { height: auto; padding: 1 3; }
    Card { width: 1fr; height: auto; min-height: 12; margin: 0 1; padding: 1 2;
           background: #09132d; border: tall #142040; }
    Card:focus { border: tall #ff97bf; background: #0e182b; }
    .title { text-style: bold; color: #ffffff; padding-bottom: 1; }
    .muted { color: #95adda; }
    #alerts { padding: 0 5; height: auto; }
    #ask { width: 72; height: auto; padding: 1 2; background: #09132d; border: tall #ff97bf; }
    AskRef { align: center middle; background: #040e27 60%; }
    DataTable { background: #040e27; }
    """
    BINDINGS = [Binding("s", "setup", "Set up"), Binding("c", "check", "Check"), Binding("i", "addons", "Add-ons"),
                Binding("r", "rescan", "Rescan"), Binding("enter", "open", "Open", show=False), Binding("q", "quit", "Quit")]

    def __init__(self, scanner=None):
        super().__init__()
        self.items: list[dict] = []
        self.results: dict[str, str] = {}
        self.scanner = scanner or scan.scan

    def compose(self) -> ComposeResult:
        yield Static(id="bar")
        yield Static(id="hello")
        with Horizontal(id="cards"):
            with Card(id="protect"):
                yield Static("Protection", classes="title")
                yield Static(id="protect-body")
            with Card(id="addons"):
                yield Static("Add-ons on this machine", classes="title")
                yield Static(id="addons-body")
        yield Static(id="alerts")
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(THEME)
        self.theme = THEME.name
        self.refresh_status()
        self.query_one("#protect").focus()
        self.action_rescan()

    def refresh_status(self) -> None:
        rows = protection()
        w = watcher()
        state = {True: "[#5a935a]●[/] watcher on", False: "[#95adda]○[/] watcher off", None: "watcher: see Task Scheduler"}[w]
        self.query_one("#bar", Static).update(f"[b #ff97bf]unpick[/] {__version__}   {state}")
        steps = "\n".join(f"{n}. {s}" for n, s in enumerate(next_steps(rows), 1))
        self.query_one("#hello", Static).update(f"[b]{TAGLINE}[/]\n\n{steps}")
        body = Text()
        for r in rows:
            if not r["installed"]:
                body.append(f"   {r['label']:<13}", style="#95adda").append("not installed\n", style="#95adda")
            elif r["hooked"]:
                body.append(" ✓ ", style="bold #5a935a").append(f"{r['label']:<13}")
                body.append(f"blocks {r['level']} and above\n", style="#95adda")
            else:
                body.append(" ! ", style="bold #ffc000").append(f"{r['label']:<13}").append("not protected\n", style="#ffc000")
        if any(r["fail_open"] for r in rows):
            body.append("\nInstalls unpick cannot check are let through.", style="#ffc000")
        body.append("\nEnter or s: run setup", style="#95adda")
        self.query_one("#protect-body", Static).update(body)
        found = alerts()
        text = Text("Recent watcher alerts\n", style="bold") if found else Text()
        for e in found:
            text.append(f"  {e['ts'][:16].replace('T', ' ')}  ", style="#95adda").append(f"{e['high']} high", style=COLOR["high"])
            text.append(f", {e['open']} open  {Path(e['path']).name}\n")
        self.query_one("#alerts", Static).update(text)

    def show_addons(self, done: int, total: int) -> None:
        counts = {b: 0 for b in BUCKETS}
        for b in self.results.values():
            counts[b] += 1
        head = Text(f"{len(self.items)} add-ons in {total} places\n\n")
        if done == total:
            note = Text("\nNothing found is not the same as safe.", style="#95adda")
        else:
            filled = round(16 * done / (total or 1))
            note = Text("\n" + "\u2501" * filled, style="#ff97bf").append("\u2501" * (16 - filled), style="#142040")
            note.append(f"  scanning {done} of {total}", style="#95adda")
        self.query_one("#addons-body", Static).update(head + bars(counts) + note)

    @work(thread=True, exclusive=True)
    def action_rescan(self) -> None:
        self.items = inventory.discover(project=Path.cwd())
        todo = places(self.items)
        self.results = {}
        self.call_from_thread(self.show_addons, 0, len(todo))
        for n, p in enumerate(todo, 1):
            try:
                self.results[str(p)] = bucket(self.scanner(p))
            except Exception:  # one unreadable place must not stop the rest
                self.results[str(p)] = "not read"
            self.call_from_thread(self.show_addons, n, len(todo))

    def action_open(self) -> None:
        {"protect": self.action_setup, "addons": self.action_addons}.get(getattr(self.focused, "id", ""), lambda: None)()

    def action_setup(self) -> None:
        hand_over(self, ["setup"])
        self.refresh_status()

    def action_check(self) -> None:
        def go(ref: str | None) -> None:
            if ref:
                hand_over(self, ["check", ref])
        self.push_screen(AskRef(), go)

    def action_addons(self) -> None:
        self.push_screen(AddOns())
