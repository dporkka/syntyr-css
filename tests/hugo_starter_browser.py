"""Optional real-browser check for the four standalone Hugo presets.

Run with HUGO_BIN and PLAYWRIGHT_CHROMIUM_EXECUTABLE; set SYNTYR_HUGO_CSS_ROOT
to a local immutable release directory to exercise its exact CSS bytes.
No browser dependency is required to build or serve the site.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_hugo_cms_starter import build, CSS_ROOT


class HugoStarterBrowserTests(unittest.TestCase):
    def test_presets_without_javascript(self):
        hugo = os.environ.get("HUGO_BIN") or shutil.which("hugo")
        if not hugo:
            self.skipTest("Set HUGO_BIN to exercise real Hugo output")
        css_root = Path(os.environ.get("SYNTYR_HUGO_CSS_ROOT", CSS_ROOT))
        options = {"headless": True}
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        if executable:
            options["executable_path"] = executable
        with TemporaryDirectory() as temp:
            root = Path(temp)
            handler = partial(SimpleHTTPRequestHandler, directory=root)
            with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                origin = f"http://127.0.0.1:{server.server_port}/"
                thread = Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    for preset in ("cms", "personal", "business", "documentation"):
                        build(root / preset, hugo=hugo, preset=preset, css_root=css_root,
                              base_url=origin + preset + "/")
                    with sync_playwright() as p:
                        browser = p.chromium.launch(**options)
                        try:
                            for width in (320, 768, 1280):
                                context = browser.new_context(
                                    java_script_enabled=False,
                                    viewport={"width": width, "height": 900})
                                try:
                                    external = []
                                    def local_only(route):
                                        if route.request.url.startswith(origin):
                                            route.continue_()
                                        else:
                                            external.append(route.request.url)
                                            route.abort()
                                    context.route("**/*", local_only)
                                    page = context.new_page()
                                    for preset in ("cms", "personal", "business", "documentation"):
                                        prefix = origin + preset + "/"
                                        for html in sorted((root / preset).rglob("*.html")):
                                            route = html.relative_to(root / preset).as_posix()
                                            with self.subTest(preset=preset, width=width, route=route):
                                                response = page.goto(prefix + route, wait_until="load")
                                                self.assertEqual(response.status, 200)
                                                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),
                                                                     width)
                                                self.assertEqual(page.locator("h1").count(), 1)
                                                self.assertTrue(page.get_by_role("navigation", name="Primary").is_visible())
                                                self.assertTrue(page.locator("body").evaluate(
                                                    "(el) => getComputedStyle(el).getPropertyValue('--syn-text').trim()"))
                                        page.goto(prefix, wait_until="load")
                                        page.keyboard.press("Tab")
                                        self.assertEqual(page.evaluate("document.activeElement.textContent.trim()"),
                                                         "Skip to content")
                                        page.keyboard.press("Enter")
                                        self.assertEqual(page.evaluate("document.activeElement.id"), "content")
                                        if preset == "cms":
                                            disclosure = page.locator("details").first
                                            disclosure.locator("summary").click()
                                            self.assertIsNotNone(disclosure.get_attribute("open"))
                                        else:
                                            primary = page.get_by_role("navigation", name="Primary")
                                            primary.get_by_role("link").nth(1).click()
                                            self.assertTrue(page.url.startswith(prefix))
                                            self.assertNotEqual(page.url, prefix)
                                    self.assertEqual(external, [])
                                finally:
                                    context.close()
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()


if __name__ == "__main__":
    unittest.main()
