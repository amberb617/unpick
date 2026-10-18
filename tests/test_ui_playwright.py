"""Browser tests at 1920x1080. Screenshots go to docs/screenshots/ui/ for the talk.

Needs the uitest extra and `python -m playwright install chromium`; skipped otherwise.
"""

import threading
from pathlib import Path

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

from runthrough.ui.server import create_app, free_port  # noqa: E402

SHOTS = Path(__file__).resolve().parents[1] / "docs" / "screenshots" / "ui"


@pytest.fixture
def ui(kit):
    from werkzeug.serving import make_server
    port = free_port()
    server = make_server("127.0.0.1", port, create_app(port, "playwright-token", kit), threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}/", kit
    server.shutdown()


@pytest.fixture
def page():
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # browser not installed
            pytest.skip(f"chromium not available: {e}")
        pg = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.on("request", lambda r: r.url.startswith("http://127.0.0.1") or pytest.fail(f"external request: {r.url}"))
        yield pg
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_scan_screen(ui, page, theme):
    url, kit = ui
    page.goto(url + "#scan")
    page.evaluate(f"localStorage.setItem('runthrough-theme', '{theme}')")
    page.reload()
    page.fill("#scan-path", "sample-a")
    page.click("#scan-form button[type=submit]")
    page.wait_for_selector(".finding")
    assert page.locator(".row.flag").count() == 3
    hidden = page.locator("#L24 .hidden-note").inner_text()
    assert "collector@example.invalid" in hidden
    assert page.locator(".finding").first.locator(".decide button").count() == 3
    page.locator("#L24").scroll_into_view_if_needed()
    page.screenshot(path=str(SHOTS / f"scan-{theme}.png"))


def test_tool_description_screen(ui, page):
    url, _ = ui
    page.goto(url + "#scan")
    page.fill("#scan-path", "tools.json")
    page.click("#scan-form button[type=submit]")
    page.wait_for_selector(".finding")
    assert "sidenote" in page.locator("#findings").inner_text()
    page.screenshot(path=str(SHOTS / "scan-tools-json.png"))


def test_decide_from_ui(ui, page):
    url, kit = ui
    page.goto(url + "#scan")
    page.fill("#scan-path", "sample-b")
    page.click("#scan-form button[type=submit]")
    page.wait_for_selector(".finding")
    page.click(".finding .decide button:text('accept')")
    page.wait_for_selector(".finding.decided")
    assert (kit / ".runthrough" / "decisions.json").is_file()
    page.screenshot(path=str(SHOTS / "scan-false-positive-accepted.png"))


def test_backends_screen(ui, page):
    url, _ = ui
    page.goto(url + "#backends")
    page.wait_for_selector("#be-table tbody tr")
    assert "cisco-skill-scanner" in page.locator("#be-table").inner_text()
    page.screenshot(path=str(SHOTS / "backends-and-judges.png"), full_page=True)
