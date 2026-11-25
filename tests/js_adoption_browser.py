"""Optional real-browser smoke for built React, Preact, Solid and Next.js consumers.

Run after scripts/test_js_adoption.py --install:
  python3 -m venv /tmp/syntyr-js-browser
  /tmp/syntyr-js-browser/bin/pip install playwright
  /tmp/syntyr-js-browser/bin/python -m playwright install chromium
  /tmp/syntyr-js-browser/bin/python tests/js_adoption_browser.py
"""
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
import unittest
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextmanager
def vite_site(fixture="examples/react-vite"):
    folder = ROOT / fixture / "dist"
    if not (folder / "index.html").is_file():
        raise RuntimeError(f"Build {fixture} before browser tests")
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietHandler, directory=str(folder)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port)
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


@contextmanager
def next_site():
    folder = ROOT / "examples/next-app-router"
    if not (folder / ".next").is_dir():
        raise RuntimeError("Build examples/next-app-router before browser tests")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    command = [
        "node", "node_modules/next/dist/bin/next", "start",
        "--hostname", "127.0.0.1", "--port", str(port),
    ]
    process = subprocess.Popen(command, cwd=folder,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    url = "http://127.0.0.1:" + str(port)
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError("Next.js production server exited early")
            try:
                with urlopen(url, timeout=0.2) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.1)
        else:
            raise TimeoutError("Next.js production server did not start")
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


class SyntyrJsxBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            **({"executable_path": os.environ["SYNTYR_CHROMIUM_EXECUTABLE"]}
               if os.environ.get("SYNTYR_CHROMIUM_EXECUTABLE") else {}),
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def check_app(self, site, button_before, button_after):
        page = self.browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        try:
            page.goto(site, wait_until="networkidle")
            self.assertEqual(page.locator(".syn-root").count(), 1)
            self.assertEqual(page.locator(".syn-panel").count(), 1)
            self.assertEqual(page.locator(".syn-root").get_attribute("data-syn-theme"), "studio")
            padding = page.locator(".syn-panel").evaluate(
                "element => getComputedStyle(element).paddingTop")
            self.assertNotEqual(padding, "0px", "Syntyr CSS must actually load")
            self.assertFalse(page.evaluate(
                "document.documentElement.scrollWidth > window.innerWidth"),
                "mobile viewport must not overflow")
            page.get_by_role("button", name=button_before).click()
            self.assertTrue(page.get_by_role("button", name=button_after).is_visible())
            self.assertEqual(errors, [], "JS, hydration or network console errors")
        finally:
            page.close()

    def test_vite_react_hydrates_and_styles(self):
        with vite_site() as url:
            self.check_app(url, "Count: 0", "Count: 1")

    def test_preact_jsx_mounts_and_styles(self):
        with vite_site("examples/preact-jsx") as url:
            self.check_app(url, "Count: 0", "Count: 1")

    def test_solid_tsx_mounts_and_styles(self):
        with vite_site("examples/solid-tsx") as url:
            self.check_app(url, "Count: 0", "Count: 1")

    def test_next_app_router_hydrates_client_island(self):
        with next_site() as url:
            self.check_app(url, "Increment 0", "Increment 1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
