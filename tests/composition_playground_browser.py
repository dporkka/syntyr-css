"""Exercise real static-site preview and downloads with the production CSP."""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from zipfile import ZipFile
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_cloudflare_site import build, HEADERS
from playwright.sync_api import sync_playwright, expect


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def end_headers(self):
        # Local HTTP tests omit only the production HTTPS upgrade directive.
        csp = next(line.strip().split(": ", 1)[1] for line in HEADERS.splitlines()
                   if line.strip().startswith("Content-Security-Policy:"))
        self.send_header("Content-Security-Policy", csp.replace("; upgrade-insecure-requests", ""))
        super().end_headers()


def main():
    with TemporaryDirectory() as tmp:
        site = Path(tmp) / "site"
        build(site, check=False)
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(site)))
        Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{server.server_port}/docs/composition-playground.html"
        try:
            with sync_playwright() as p:
                for engine in ("chromium", "firefox"):
                    browser = getattr(p, engine).launch()
                    for width in (375, 1280):
                        ctx = browser.new_context(viewport={"width": width, "height": 900},
                                                  accept_downloads=True)
                        page = ctx.new_page()
                        page.goto(url)
                        expect(page.locator("#composition-status")).to_contain_text("5 canonical")
                        frame = page.frame_locator("#composition-preview")
                        expect(frame.locator("main > section")).to_have_count(5)
                        expect(frame.locator("a[href]")).to_have_count(0)
                        assert frame.locator("body").evaluate(
                            "e=>getComputedStyle(e).getPropertyValue('--syn-bg').trim()"), engine
                        page.get_by_role("button", name="CRM dashboard").click()
                        expect(page.locator("#composition-status")).to_contain_text("4 canonical")
                        expect(frame.get_by_role("heading", name="Deal pipeline")).to_be_visible()
                        assert "authorized mutations" in page.locator("#composition-obligations").inner_text()
                        with page.expect_download() as download:
                            page.get_by_role("button", name="Download HTML/CSS ZIP").click()
                        with ZipFile(download.value.path()) as z:
                            assert z.testzip() is None
                            assert "Deal pipeline" in z.read("index.html").decode()
                            assert "<script" not in z.read("index.html").decode()
                            assert "Offline validation has not run" in z.read("README.txt").decode()
                        with page.expect_download() as download:
                            page.get_by_role("button", name="Download project JSON").click()
                        assert len(json.loads(Path(download.value.path()).read_text())["blocks"]) == 4
                        page.locator("#composition-title").fill("Modified")
                        assert page.locator("#composition-zip").is_disabled()
                        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                        print("PASS", engine, width, "presets, styled sandbox, obligations, ZIP, JSON, stale export")
                        ctx.close()
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
