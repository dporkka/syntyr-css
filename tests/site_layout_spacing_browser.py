"""CSS-first site hierarchy and mobile navigation regression tests.

Run: uv run --with playwright python tests/site_layout_spacing_browser.py
Tests committed local site assets, not a mutable deployed preview.
"""
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class SiteLayoutSpacingBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def page_at(self, name, width, height=900):
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.goto((ROOT / name).as_uri(), wait_until="load")
        return page

    def test_generated_docs_mobile_contents_does_not_precede_article_at_full_height(self):
        for width in (320, 390):
            with self.subTest(width=width):
                page = self.page_at("docs/components.html", width)
                try:
                    toc = page.locator(".docs-article-toc-mobile")
                    self.assertTrue(toc.is_visible())
                    self.assertFalse(toc.evaluate("el => el.open"))
                    heading = page.locator(".docs-prose h1")
                    self.assertLess(heading.bounding_box()["y"], 700)
                    toc.locator("summary").click()
                    self.assertTrue(toc.evaluate("el => el.open"))
                    self.assertTrue(toc.get_by_role("link", name="Loading and scoping").is_visible())
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width + 1)
                finally:
                    page.close()

    def test_generated_docs_desktop_has_sticky_contents_navigation(self):
        page = self.page_at("docs/components.html", 1440)
        try:
            self.assertTrue(page.locator(".docs-article-toc-desktop").is_visible())
            self.assertFalse(page.locator(".docs-article-toc-mobile").is_visible())
            self.assertEqual(page.locator(".docs-article-sidebar").evaluate("e=>getComputedStyle(e).position"), "sticky")
        finally:
            page.close()

    def test_documentation_landing_header_stays_compact_on_desktop(self):
        page = self.page_at("docs/index.html", 1440)
        try:
            self.assertLessEqual(page.locator(".docs-header").bounding_box()["height"], 100)
            self.assertTrue(page.locator(".docs-header .site-mobile-menu summary").is_visible())
            self.assertTrue(page.locator(".docs-header .syn-nav a[href='catalog.html']").is_visible())
        finally:
            page.close()

    def test_marketing_header_shows_only_one_navigation_mode(self):
        for width in (390, 1440):
            with self.subTest(width=width):
                page = self.page_at("index.html", width)
                try:
                    self.assertEqual(page.locator(".site-nav").is_visible(), width == 1440)
                    self.assertEqual(page.locator(".site-mobile-menu").is_visible(), width < 1440)
                finally:
                    page.close()

    def test_component_index_is_compact_on_mobile_and_complete_on_desktop(self):
        mobile = self.page_at("docs/catalog.html", 390)
        try:
            disclosure = mobile.locator(".catalog-mobile-index")
            self.assertTrue(disclosure.is_visible())
            self.assertFalse(disclosure.evaluate("e=>e.open"))
            self.assertLess(mobile.locator("#catalog-title").bounding_box()["y"], 350)
            disclosure.locator("summary").click()
            self.assertEqual(disclosure.locator("a[href^='#catalog-']").count(), 49)
        finally:
            mobile.close()
        desktop = self.page_at("docs/catalog.html", 1440)
        try:
            self.assertTrue(desktop.locator("#catalog-index").is_visible())
            self.assertFalse(desktop.locator(".catalog-mobile-index").is_visible())
        finally:
            desktop.close()


    def test_mobile_blocks_gallery_offers_compact_previews_without_losing_examples(self):
        page = self.page_at("docs/blocks.html", 390)
        try:
            previews = page.locator(".blocks-preview-disclosure")
            self.assertEqual(previews.count(), 68)
            self.assertEqual(page.locator(".blocks-preview-disclosure[open]").count(), 2)
            compact_height = page.evaluate("document.documentElement.scrollHeight")
            button = page.locator("#blocks-preview-toggle")
            self.assertTrue(button.is_visible())
            button.click()
            self.assertEqual(page.locator(".blocks-preview-disclosure[open]").count(), 68)
            expanded_height = page.evaluate("document.documentElement.scrollHeight")
            self.assertLess(compact_height, expanded_height * 0.75)
            button.click()
            self.assertEqual(page.locator(".blocks-preview-disclosure[open]").count(), 2)
            page.locator(".blocks-preview-disclosure").nth(3).locator("summary").click()
            self.assertTrue(previews.nth(3).evaluate("e => e.open"))
        finally:
            page.close()

    def test_blocks_gallery_no_js_and_desktop_show_all_previews(self):
        desktop = self.page_at("docs/blocks.html", 1440)
        try:
            self.assertEqual(desktop.locator(".blocks-preview-disclosure[open]").count(), 68)
            self.assertFalse(desktop.locator("#blocks-preview-toggle").is_visible())
        finally:
            desktop.close()
        context = self.browser.new_context(viewport={"width": 390, "height": 844},
                                           java_script_enabled=False)
        page = context.new_page()
        try:
            page.goto((ROOT / "docs/blocks.html").as_uri(), wait_until="load")
            self.assertEqual(page.locator(".blocks-preview-disclosure[open]").count(), 68)
        finally:
            context.close()

    def test_blocks_category_navigation_works_without_javascript(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844},
                                           java_script_enabled=False)
        page = context.new_page()
        try:
            page.goto((ROOT / "docs/blocks.html").as_uri(), wait_until="load")
            links = page.locator(".blocks-category-nav a")
            self.assertGreaterEqual(links.count(), 6)
            for link in links.all():
                target = link.get_attribute("href")
                self.assertTrue(target.startswith("#block-title-"))
                self.assertEqual(page.locator(target).count(), 1)
        finally:
            context.close()

    def test_shell_width_can_be_adapted_without_overriding_component_css(self):
        page = self.browser.new_page(viewport={"width": 1000, "height": 700})
        try:
            css = (ROOT / "dist/syntyr.core.css").read_text()
            page.set_content(f"""<style>body {{ margin: 0; }} {css}</style>
              <div class="syn-root">
                <main class="syn-shell" style="--syn-shell-max: 60rem; --syn-shell-inline-inset: 4rem">
                  Content
                </main>
              </div>""")
            shell = page.locator(".syn-shell").bounding_box()
            self.assertAlmostEqual(shell["width"], 936, delta=1)
            self.assertAlmostEqual(shell["x"], 32, delta=1)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
