"""Regression checks for the homepage's above-the-fold message and actions.

Run with: python3 -m unittest tests/test_homepage_fold.py
Requires Playwright and a Chromium executable; no runtime dependency is added.
"""
import os
from pathlib import Path
import shutil
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class HomepageFoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        opts = {"headless": True}
        executable = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                      or shutil.which("chromium")
                      or shutil.which("chromium-browser"))
        if executable:
            opts.update(executable_path=executable, args=["--no-sandbox"])
        cls.browser = cls.playwright.chromium.launch(**opts)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_homepage_fold_at_common_viewports(self):
        page = self.browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            html = (ROOT / "index.html").read_text(encoding="utf-8")
            # Keep the browser test entirely local: the site has no runtime CSS CDN.
            for asset in ("dist/syntyr.core.css", "dist/syntyr.recipes.css",
                          "dist/syntyr.effects.css"):
                link = f'<link rel="stylesheet" href="{asset}">'
                css = (ROOT / asset).read_text(encoding="utf-8")
                self.assertIn(link, html)
                html = html.replace(link, f"<style>{css}</style>", 1)
            page.set_content(html, wait_until="load")

            desktop = ((1440, 900), (1366, 768), (1280, 720), (1024, 768))
            mobile = ((390, 844), (375, 667), (360, 640), (320, 568))
            for width, height in desktop + mobile:
                with self.subTest(width=width, height=height):
                    page.set_viewport_size({"width": width, "height": height})
                    measurements = page.evaluate("""() => {
                      const rect = s => {
                        const {top, bottom} = document.querySelector(s).getBoundingClientRect();
                        return {top, bottom};
                      };
                      return {
                        header: rect('.site-header'),
                        hero: rect('.site-hero'),
                        heading: rect('#hero-title'),
                        description: rect('.site-lede'),
                        primary: rect('.site-hero .syn-actions a:first-child'),
                        secondary: rect('.site-hero .syn-actions a:nth-child(2)'),
                        scrollWidth: document.documentElement.scrollWidth,
                      };
                    }""")
                    self.assertLessEqual(measurements["scrollWidth"], width)
                    for element in ("header", "heading", "description", "primary", "secondary"):
                        self.assertGreaterEqual(measurements[element]["top"], 0)
                        self.assertLessEqual(measurements[element]["bottom"], height,
                                             f"{element} falls below {width}x{height} fold")
                    if (width, height) in desktop:
                        self.assertLessEqual(measurements["hero"]["bottom"], height,
                                             f"desktop hero extends below {width}x{height} fold")

            # The compact header must not make the original links unreachable.
            page.locator(".site-mobile-menu summary").click()
            for href in ("docs/site-builders.html", "docs/console-kit.html",
                         "docs/design-resources.html"):
                # Other resources may be promoted in sections rather than the menu.
                self.assertGreater(page.locator(f'a[href="{href}"]').count(), 0)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
