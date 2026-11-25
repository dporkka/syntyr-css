"""Optional real-browser smoke for copy-owned Node HTMX + Datastar fragments.

Run with separately downloaded, pinned browser bundles (not Syntyr assets):
  HTMX_JS_PATH=/tmp/syntyr-htmx2.js DATASTAR_JS_PATH=/tmp/syntyr-datastar-v1.0.5.js \
    python3 tests/server_html_fragments_browser.py

Requires developer-installed Playwright and Chromium. Not part of core test suite.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import unittest
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/server-components-node/fragments/server.mjs"
HTMX_URL = "https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js"
DATASTAR_URL = "https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.5/bundles/datastar.js"


class BrowserFragmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.htmx = Path(os.environ.get("HTMX_JS_PATH", ""))
        cls.datastar = Path(os.environ.get("DATASTAR_JS_PATH", ""))
        if not cls.htmx.is_file() or not cls.datastar.is_file():
            raise unittest.SkipTest("Set HTMX_JS_PATH and DATASTAR_JS_PATH to pinned local bundles")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.url = f"http://127.0.0.1:{cls.port}"
        cls.server = subprocess.Popen(["node", str(EXAMPLE)], cwd=ROOT,
                                      env={**os.environ, "SYNTYR_PORT": str(cls.port)},
                                      stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for _ in range(75):
            if cls.server.poll() is not None:
                raise RuntimeError(f"Node server exited: {cls.server.stderr.read().decode()}")
            try:
                with urlopen(cls.url + "/htmx", timeout=0.5):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            cls.server.terminate()
            raise RuntimeError("fragment test server did not start")
        cls.p = sync_playwright().start()
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or shutil.which("chromium")
        args = {"headless": True, "args": ["--no-sandbox", "--disable-gpu", "--disk-cache-size=0"]}
        if executable:
            args.update(executable_path=executable)
        try:
            cls.browser = cls.p.chromium.launch(**args)
        except Exception:
            cls.p.stop()
            cls.server.terminate()
            cls.server.wait(timeout=5)
            cls.server.stderr.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.p.stop()
        cls.server.terminate()
        cls.server.wait(timeout=5)
        cls.server.stderr.close()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(8000)
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.route(HTMX_URL, lambda route: route.fulfill(path=str(self.htmx), content_type="text/javascript"))
        self.page.route(DATASTAR_URL, lambda route: route.fulfill(path=str(self.datastar), content_type="text/javascript"))

    def tearDown(self):
        try:
            self.assertEqual(self.errors, [])
        finally:
            self.context.close()

    def test_htmx_updates_components_and_displays_server_validation(self):
        self.page.goto(self.url + "/htmx")
        self.page.wait_for_function("() => typeof htmx !== 'undefined'")
        self.page.evaluate("window._syntyrRoot = document.querySelector('body.syn-root')")
        self.page.locator("#resource-query").fill("CRM")
        self.page.locator("form[role=search] button[type=submit]").click()
        self.page.get_by_role("rowheader", name="CRM").wait_for()
        self.page.wait_for_url("**?q=CRM")
        self.assertTrue(self.page.evaluate("window._syntyrRoot === document.querySelector('body.syn-root')"))
        self.page.locator("#resource-query").fill("x" * 81)
        self.page.locator("form[role=search] button[type=submit]").click()
        self.page.locator("#resource-query[aria-invalid=true]").wait_for()
        self.assertEqual(self.page.locator("#resource-query").get_attribute("aria-describedby"), "resource-query-error")
        self.page.get_by_role("alert").wait_for()
        self.assertEqual(self.page.locator('#resource-results').count(), 0)
        self.page.locator("#resource-query").fill("Inventory")
        self.page.locator("form[role=search] button[type=submit]").click()
        self.page.get_by_role("rowheader", name="Inventory").wait_for()
        self.assertEqual(self.page.locator("#resource-query").get_attribute("aria-invalid"), None)

    def test_datastar_signals_render_components_and_preserve_theme(self):
        self.page.goto(self.url + "/datastar")
        self.page.wait_for_function("() => document.querySelector('form[role=search]').getAttribute('aria-busy') === 'false'")
        self.page.evaluate("window._syntyrRoot = document.querySelector('body.syn-root')")
        self.page.locator("#resource-query").fill("Inventory")
        self.page.locator("form[role=search] button[type=submit]").click()
        self.page.get_by_role("rowheader", name="Inventory").wait_for()
        self.assertTrue(self.page.evaluate("window._syntyrRoot === document.querySelector('body.syn-root')"))
        self.assertEqual(self.page.locator("body.syn-root").get_attribute("data-syn-theme"), "studio")
        self.assertEqual(self.page.locator("#resource-query").input_value(), "Inventory")
        self.page.locator("#resource-query").fill("zzzz")
        self.page.locator("form[role=search] button[type=submit]").click()
        self.page.get_by_text("No matching resources.").wait_for()
        self.assertEqual(self.page.locator("#resource-query").input_value(), "zzzz")

    def test_both_pages_support_native_get_without_javascript(self):
        context = self.browser.new_context(java_script_enabled=False)
        try:
            for mode in ("htmx", "datastar"):
                page = context.new_page()
                page.goto(self.url + "/" + mode)
                page.locator("#resource-query").fill("CRM")
                page.locator("form[role=search] button[type=submit]").click()
                page.get_by_role("rowheader", name="CRM").wait_for()
                self.assertIn("?q=CRM", page.url)
                page.close()
        finally:
            context.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
