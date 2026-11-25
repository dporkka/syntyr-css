"""Real Unpoly 3.15 and Turbo 8 browser-compatibility regression tests.

Development-only external fixtures:
  curl -fsSL https://cdn.jsdelivr.net/npm/unpoly@3.15.0/unpoly.js -o /tmp/syntyr-unpoly-3.15.0.js
  curl -fsSL https://cdn.jsdelivr.net/npm/unpoly@3.15.0/unpoly.css -o /tmp/syntyr-unpoly-3.15.0.css
  curl -fsSL https://cdn.jsdelivr.net/npm/@hotwired/turbo@8.0.23/dist/turbo.es2017-esm.min.js -o /tmp/syntyr-turbo-8.0.23.js
  UNPOLY_JS_PATH=/tmp/syntyr-unpoly-3.15.0.js \
  UNPOLY_CSS_PATH=/tmp/syntyr-unpoly-3.15.0.css \
  TURBO_JS_PATH=/tmp/syntyr-turbo-8.0.23.js python3 tests/hypertext_browser.py
"""
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
import os
import shutil
import sys
import unittest

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.hypertext_server import DemoHandler

ROOT = Path(__file__).resolve().parents[1]


class GatedDemoHandler(DemoHandler):
    def do_GET(self):
        if self.path.startswith("/customers/"):
            if not self.server.gate.wait(timeout=10):
                self.send_error(504, "test request gate timeout")
                return
        super().do_GET()


class HypertextBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = {
            "unpoly_js": os.getenv("UNPOLY_JS_PATH", ""),
            "unpoly_css": os.getenv("UNPOLY_CSS_PATH", ""),
            "turbo_js": os.getenv("TURBO_JS_PATH", ""),
        }
        if not all(value and Path(value).is_file() for value in paths.values()):
            raise unittest.SkipTest("Set pinned UNPOLY_JS_PATH, UNPOLY_CSS_PATH and TURBO_JS_PATH")
        cls.paths = paths
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GatedDemoHandler)
        cls.server.gate = Event()
        cls.server.gate.set()
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.p = sync_playwright().start()
        engine = os.environ.get("SYNTYR_BROWSER", "chromium")
        if engine not in ("chromium", "firefox", "webkit"):
            raise ValueError(f"Unknown SYNTYR_BROWSER: {engine}")
        executable = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                      or shutil.which("chromium") or shutil.which("chromium-browser")) if engine == "chromium" else None
        options = {"headless": True}
        if executable:
            options["executable_path"] = executable
            options["args"] = ["--no-sandbox"]
        try:
            cls.browser = getattr(cls.p, engine).launch(**options)
        except Exception:
            cls.p.stop()
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=2)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.p.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(8000)
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        fixtures = (
            ("https://cdn.jsdelivr.net/npm/unpoly@3.15.0/unpoly.js", "unpoly_js", "text/javascript"),
            ("https://cdn.jsdelivr.net/npm/unpoly@3.15.0/unpoly.css", "unpoly_css", "text/css"),
            ("https://cdn.jsdelivr.net/npm/@hotwired/turbo@8.0.23/dist/turbo.es2017-esm.min.js", "turbo_js", "text/javascript"),
        )
        def fixture_handler(path, content_type):
            def handler(route):
                route.fulfill(path=path, content_type=content_type)
            return handler
        for url, key, mime in fixtures:
            self.page.route(url, fixture_handler(self.paths[key], mime))

    def tearDown(self):
        self.server.gate.set()
        try:
            self.assertEqual(self.errors, [])
        finally:
            self.context.close()

    def test_unpoly_form_has_real_pending_feedback_then_swaps_fragment(self):
        self.page.goto(self.url + "/examples/unpoly.html")
        self.page.wait_for_function("() => window.up && document.documentElement.classList.contains('up-booted')")
        self.page.locator("#unpoly-query").fill("Acme")
        self.page.evaluate("window.__syntyrRoot = document.querySelector('main.syn-root')")
        self.server.gate.clear()
        try:
            self.page.locator("#unpoly-submit").click()
            self.page.locator("#unpoly-search.up-active").wait_for()
            self.page.locator("#customer-results.up-loading").wait_for()
            button = self.page.locator("#unpoly-submit")
            if not button.is_disabled():
                self.assertEqual(button.evaluate("e => getComputedStyle(e).cursor"), "progress")
            self.assertEqual(self.page.locator("main.syn-root").get_attribute("data-syn-theme"), "studio")
            self.server.gate.set()
            self.page.get_by_text("Acme Corporation").wait_for()
            self.page.wait_for_function("() => !document.querySelector('#unpoly-search').classList.contains('up-active')")
            self.assertEqual(self.page.locator("#customer-results").count(), 1)
            self.assertEqual(self.page.locator("main.syn-root").get_attribute("data-syn-theme"), "studio")
            self.assertTrue(self.page.evaluate(
                "() => window.__syntyrRoot === document.querySelector('main.syn-root')"))
        finally:
            self.server.gate.set()

    def test_turbo_frame_busy_then_morphs_without_losing_theme(self):
        self.page.goto(self.url + "/examples/turbo.html")
        self.page.wait_for_function("() => window.Turbo && customElements.get('turbo-frame')")
        self.page.locator("#turbo-query").fill("Acme")
        self.page.evaluate("window.__syntyrRoot = document.querySelector('main.syn-root')")
        self.server.gate.clear()
        try:
            self.page.locator("#turbo-submit").click()
            self.page.locator("turbo-frame#customer-results[busy]").wait_for()
            button = self.page.locator("#turbo-submit")
            if not button.is_disabled():
                self.assertEqual(button.evaluate("e => getComputedStyle(e).cursor"), "progress")
            self.server.gate.set()
            self.page.get_by_text("Acme Corporation").wait_for()
            self.page.wait_for_function("() => !document.querySelector('#customer-results').hasAttribute('busy')")
            self.assertEqual(self.page.locator("main.syn-root").get_attribute("data-syn-theme"), "studio")
            self.assertEqual(self.page.locator("turbo-frame#customer-results").count(), 1)
            self.assertEqual(self.page.locator("#turbo-query").input_value(), "Acme")
            self.assertTrue(self.page.evaluate(
                "() => window.__syntyrRoot === document.querySelector('main.syn-root')"))
        finally:
            self.server.gate.set()

    def test_turbo_stream_updates_target_without_replacing_theme_or_search_frame(self):
        self.page.goto(self.url + "/examples/turbo.html")
        self.page.wait_for_function("() => window.Turbo && customElements.get('turbo-frame')")
        self.page.evaluate("""() => {
            window.__syntyrRoot = document.querySelector('main.syn-root');
            window.__syntyrFrame = document.querySelector('turbo-frame#customer-results');
        }""")
        self.page.locator("#turbo-stream-query").fill("Acme")
        self.page.locator("#turbo-stream-submit").click()
        self.page.locator("#turbo-stream-results").get_by_text("Acme Corporation").wait_for()
        self.assertTrue(self.page.evaluate(
            "() => window.__syntyrRoot === document.querySelector('main.syn-root')"))
        self.assertTrue(self.page.evaluate(
            "() => window.__syntyrFrame === document.querySelector('turbo-frame#customer-results')"))
        self.assertEqual(self.page.locator("main.syn-root").get_attribute("data-syn-theme"), "studio")

    def test_unpoly_validation_failure_replaces_form_without_losing_theme(self):
        self.page.goto(self.url + "/examples/unpoly.html")
        self.page.wait_for_function("() => window.up && document.documentElement.classList.contains('up-booted')")
        self.page.evaluate("window.__syntyrRoot = document.querySelector('main.syn-root')")
        self.page.locator("#unpoly-query").fill("")
        self.page.locator("#unpoly-submit").click()
        self.page.locator("#unpoly-search-error").wait_for()
        field = self.page.locator("#unpoly-query")
        self.assertEqual(field.get_attribute("aria-invalid"), "true")
        self.assertEqual(field.get_attribute("aria-describedby"), "unpoly-search-error")
        self.assertEqual(self.page.locator("#unpoly-search").count(), 1)
        self.assertTrue(self.page.evaluate(
            "() => window.__syntyrRoot === document.querySelector('main.syn-root')"))
        # A valid retry must clear server validation feedback as well as update results.
        field.fill("Northstar")
        self.page.locator("#unpoly-submit").click()
        self.page.locator("#customer-results").get_by_text("Northstar Media").wait_for()
        self.assertEqual(self.page.locator("#unpoly-search-error").count(), 0)
        self.assertNotEqual(self.page.locator("#unpoly-query").get_attribute("aria-invalid"), "true")

    def test_optional_server_states_remain_scoped_and_preserve_disabled(self):
        self.page.goto(self.url + "/examples/turbo.html")
        self.page.evaluate("""() => {
            const root = document.querySelector('main.syn-root');
            const form = document.createElement('form');
            form.id = 'phoenix-form';
            form.className = 'phx-submit-loading';
            form.innerHTML = '<button class="syn-button" type="submit">Submit</button>';
            root.append(form);
            for (const state of ['phx-click-loading', 'phx-change-loading', 'data-loading']) {
                const button = document.createElement('button');
                button.id = 'state-' + state;
                button.className = 'syn-button';
                if (state === 'data-loading') button.setAttribute(state, '');
                else button.classList.add(state);
                root.append(button);
            }
            const outside = document.createElement('button');
            outside.className = 'syn-button';
            outside.id = 'outside-loading';
            outside.setAttribute('data-loading', '');
            document.body.append(outside);
        }""")
        for selector in ("#phoenix-form button", "#state-phx-click-loading",
                         "#state-phx-change-loading", "#state-data-loading"):
            with self.subTest(selector=selector):
                button = self.page.locator(selector)
                self.assertEqual(button.evaluate("e => getComputedStyle(e).cursor"), "progress")
                button.evaluate("e => e.disabled = true")
                self.assertNotEqual(button.evaluate("e => getComputedStyle(e).cursor"), "progress")
        self.assertNotEqual(
            self.page.locator("#outside-loading").evaluate("e => getComputedStyle(e).cursor"),
            "progress")

    def test_unpoly_and_turbo_work_with_javascript_disabled(self):
        for framework, field, submit in (
            ("unpoly", "unpoly-query", "unpoly-submit"),
            ("turbo", "turbo-query", "turbo-submit"),
            ("turbo", "turbo-stream-query", "turbo-stream-submit"),
        ):
            with self.subTest(framework=framework, field=field):
                context = self.browser.new_context(java_script_enabled=False)
                page = context.new_page()
                try:
                    page.goto(self.url + f"/examples/{framework}.html")
                    page.locator(f"#{field}").fill("Acme")
                    page.locator(f"#{submit}").click()
                    page.get_by_text("Acme Corporation").wait_for()
                    self.assertIn("q=Acme", page.url)
                    self.assertEqual(page.locator("main.syn-root").get_attribute("data-syn-theme"), "studio")
                finally:
                    context.close()


if __name__ == "__main__":
    unittest.main()
