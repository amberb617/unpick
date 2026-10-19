"""Regenerate the talk's screenshots and docs/SLIDES.md.

    PATH=<scanners on PATH>:$PATH python tests/slides.py

Runs the real UI (2x device pixels, 1920x1080 viewport) on a fresh demo kit, with whichever offline scanners
are installed, and records the repo commit and every scanner version used. No personal paths are shown:
the kit lives in a neutral folder and the UI shows paths relative to it.
"""

from __future__ import annotations

import html
import shutil
import subprocess
import threading
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from unpick import __version__, backends, demo
from unpick.ui.server import create_app, free_port

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
KIT = Path.home() / ".unpick" / "slides" / "demo"


def terminal_png(page, out: Path, title: str, transcript: str) -> None:
    body = html.escape(transcript)
    page.set_content(f"""<html><body style="margin:0;background:#E7EEFA;font-family:-apple-system,Segoe UI,Arial">
<div style="margin:48px;border:1px solid #040E27;border-radius:12px;box-shadow:6px 6px 0 #FF97BF;overflow:hidden">
<div style="background:#0E182B;color:#FF97BF;font:700 14px 'Courier New',monospace;letter-spacing:.08em;padding:12px 18px">{html.escape(title)}</div>
<pre style="margin:0;background:#040E27;color:#E7EEFA;font:22px/1.5 'Courier New',monospace;padding:22px 26px;white-space:pre-wrap">{body}</pre>
</div></body></html>""")
    page.locator("body > div").screenshot(path=str(out))  # just the terminal, no empty page below it


def handout_transcript() -> str:
    run = lambda c: subprocess.run(["bash", "-c", c], cwd=KIT / "sample-a", capture_output=True, text=True).stdout  # noqa: E731
    cmds = [
        ("LC_ALL=C cat -v SKILL.md | grep -n 'M-'", "LC_ALL=C cat -v SKILL.md | grep -n 'M-' | cut -c1-58"),
        ("LC_ALL=C grep -nE \\\n  $'\\xe2\\x80[\\x8b-\\x8f\\xaa-\\xae]|\\xf3\\xa0' SKILL.md",
         "LC_ALL=C grep -nE $'\\xe2\\x80[\\x8b-\\x8f\\xaa-\\xae]|\\xf3\\xa0' SKILL.md | LC_ALL=C cut -c1-40"),
        ("grep -niE \\\n 'prereq|\\| *(ba)?sh|base64|\\.ssh|\\.env|tell the user' \\\n SKILL.md",
         "grep -niE 'prereq|\\| *(ba)?sh|base64|\\.ssh|\\.env|tell the user' SKILL.md | cut -c1-58"),
    ]
    return "\n".join(f"$ {shown}\n{run(real).rstrip()}\n" for shown, real in cmds)


def main() -> None:
    shutil.rmtree(KIT, ignore_errors=True)
    demo.write(KIT)
    SHOTS.mkdir(parents=True, exist_ok=True)
    port = free_port()
    server = make_server("127.0.0.1", port, create_app(port, "slides", KIT), threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/"
    installed = [r for r in backends.describe() if r["installed"] and not r["needs_online"]]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)

        def scan(path: str, with_backends: bool):
            page.goto(url + "#scan")
            page.reload()
            page.fill("#scan-path", path)
            if with_backends:
                page.locator("details.options").evaluate("d => d.open = true")
                if not page.is_disabled("#scan-backends"):
                    page.check("#scan-backends")
            page.click("#scan-form button[type=submit]")
            page.wait_for_selector(".finding", timeout=600_000)

        scan("sample-a", True)
        page.locator("details.options").evaluate("d => d.open = false")
        page.screenshot(path=str(SHOTS / "slide-17.png"))  # verdict plus "Scan details": every source that ran, nothing sent
        page.locator("#L24").scroll_into_view_if_needed()
        page.screenshot(path=str(SHOTS / "slide-18.png"))
        scan("sample-b", False)
        page.click(".finding .decide button:text('False alarm')")
        page.wait_for_selector(".decided-line")
        page.screenshot(path=str(SHOTS / "slide-19.png"))
        term = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        terminal_png(term, SHOTS / "slide-23.png", "NO INSTALL NEEDED: MACOS / LINUX", handout_transcript())
        term.close()  # its own tab: set_content keeps the URL, so a hash goto would not reload the app
        page.goto(url + "#backends")
        page.wait_for_selector("#be-table tbody tr", timeout=120_000)
        page.screenshot(path=str(SHOTS / "slide-25.png"), full_page=True)
        scan("tools.json", True)
        page.screenshot(path=str(SHOTS / "slide-B2.png"))
        browser.close()
    server.shutdown()

    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rows = "\n".join(f"| {r['name']} | {r['version']} | {r['tested_version']} | {r['maintainer']} |" for r in installed) or "| (none installed) | | | |"
    (ROOT / "docs" / "SLIDES.md").write_text(f"""# Slides: what each one shows and how to reproduce it

Generated {date.today().isoformat()} by `python tests/slides.py` from unpick {__version__} at commit `{sha}`.
Screenshots are 2x PNGs (3840x2160 for full screens) in docs/screenshots/. The demo kit is regenerated
fresh with `unpick demo`; no personal paths appear.

| slide | what it shows | reproduce | screenshot |
|---|---|---|---|
| 17 | Run the check where it can't hurt you: every source that ran, its version, local, network none | `unpick ui`, Scan screen, `sample-a`, Installed scanners on | screenshots/slide-17.png |
| 18 | Sample A rendered vs raw: the three planted lines, the hidden sentence decoded | `unpick raw demo/sample-a/SKILL.md` or the Scan screen | screenshots/slide-18.png |
| 19 | Sample B: a flag is a question, accepted with a note | `unpick scan demo/sample-b`, then `unpick decide <id> accept --note ...` | screenshots/slide-19.png |
| 23 | Reading the raw bytes with no install (macOS / Linux; PowerShell in docs/HANDOUT-COMMANDS.md) | the three commands in docs/HANDOUT-COMMANDS.md | screenshots/slide-23.png |
| 25 | Free, open source, offline-capable: maintainer, licence and network behaviour of each scanner | `unpick backends`, or the Settings screen | screenshots/slide-25.png |
| B2 | A poisoned MCP tool description read without starting any server | `unpick scan demo/tools.json --backends installed` | screenshots/slide-B2.png |

Also in docs/screenshots/ui/ (from the Playwright tests): rehearse.png (the box run of sample A),
check.png, verify.png, recover.png, scan-light.png and scan-dark.png.

## Scanner versions used

| backend | version found | adapter tested against | maintainer |
|---|---|---|---|
{rows}
""", encoding="utf-8")
    print((ROOT / "docs" / "SLIDES.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
