from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from typing import Any
from urllib.request import urlopen


REQUIRED_PAGE_TEXT = (
    "Historical Charts",
    "Global View And Drilldown",
    "Latest Radar",
    "Source Health",
    "Contradicting Evidence",
    "Changes Since Last Report",
    "Archive",
    "Methodology",
    "Scoring version",
    "Framework coverage",
)


def run_static_site_qa(site_dir: Path) -> dict[str, Any]:
    site_dir = site_dir.resolve()
    index_path = site_dir / "index.html"
    report_state_path = site_dir / "data" / "report_state.json"
    if not index_path.exists():
        raise FileNotFoundError(f"Missing static site index: {index_path}")
    if not report_state_path.exists():
        raise FileNotFoundError(f"Missing static report state: {report_state_path}")

    report_state = json.loads(report_state_path.read_text(encoding="utf-8"))
    if "source_health" not in report_state:
        raise AssertionError("report_state.json is missing source_health.")
    if "source_freshness" not in report_state:
        raise AssertionError("report_state.json is missing source_freshness.")

    with _static_server(site_dir) as base_url:
        html = _fetch_text(f"{base_url}/index.html")
        missing = [text for text in REQUIRED_PAGE_TEXT if text not in html]
        if missing:
            raise AssertionError(f"Static index is missing required text: {', '.join(missing)}")
        screenshot_result = _optional_playwright_screenshot(f"{base_url}/index.html", site_dir)

    return {
        "site_dir": str(site_dir),
        "checked_url": f"{base_url}/index.html",
        "required_text_count": len(REQUIRED_PAGE_TEXT),
        "browser_screenshot": screenshot_result,
    }


@contextmanager
def _static_server(site_dir: Path):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(site_dir), **kwargs)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _fetch_text(url: str) -> str:
    with urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def _optional_playwright_screenshot(url: str, site_dir: Path) -> dict[str, str]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except Exception:
        return {"status": "skipped", "reason": "playwright is not installed"}

    screenshot_dir = site_dir / "qa"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / "index-desktop.png"

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1366, "height": 900})
            page.goto(url, wait_until="networkidle")
            for text in REQUIRED_PAGE_TEXT:
                if page.get_by_text(text).count() == 0:
                    raise AssertionError(f"Browser QA could not find visible text: {text}")
            page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()
    except PlaywrightError as exc:
        return {"status": "skipped", "reason": f"playwright browser unavailable: {exc}"}

    if screenshot_path.stat().st_size < 10_000:
        raise AssertionError(f"Screenshot is unexpectedly small: {screenshot_path}")
    return {"status": "captured", "path": str(screenshot_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local static-site QA checks.")
    parser.add_argument("site_dir", nargs="?", default="exports/site", type=Path)
    args = parser.parse_args()
    result = run_static_site_qa(args.site_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
