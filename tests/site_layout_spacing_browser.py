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

    def test_long_documentation_tables_scroll_internally_at_large_text(self):
        page = self.page_at("docs/components.html", 320)
        try:
            page.evaluate("document.documentElement.style.fontSize = '32px'")
            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 321)
            link = page.get_by_role("link", name="email components").first
            table = link.locator("xpath=ancestor::table").first
            self.assertEqual(table.evaluate("e => getComputedStyle(e).overflowX"), "auto")
            table.evaluate("e => e.scrollLeft = 0")
            link.focus()
            self.assertGreater(table.evaluate("e => e.scrollLeft"), 0)
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

    def test_marketing_menu_wraps_at_enlarged_text_sizes(self):
        for width, scale in ((320, 1.5), (320, 2), (390, 2)):
            with self.subTest(width=width, scale=scale):
                page = self.page_at("index.html", width)
                try:
                    page.evaluate("(size) => document.documentElement.style.fontSize = size + 'px'", 16 * scale)
                    button = page.locator(".site-mobile-menu summary").bounding_box()
                    self.assertLessEqual(button["x"] + button["width"], width + 1)
                    self.assertGreaterEqual(button["x"], -1)
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width + 1)
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
            self.assertEqual(previews.count(), 85)
            self.assertEqual(page.locator(".blocks-preview-disclosure[open]").count(), 2)
            compact_height = page.evaluate("document.documentElement.scrollHeight")
            button = page.locator("#blocks-preview-toggle")
            self.assertTrue(button.is_visible())
            button.click()
            self.assertEqual(page.locator(".blocks-preview-disclosure[open]").count(), 85)
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
            self.assertEqual(desktop.locator(".blocks-preview-disclosure[open]").count(), 85)
            self.assertFalse(desktop.locator("#blocks-preview-toggle").is_visible())
        finally:
            desktop.close()
        context = self.browser.new_context(viewport={"width": 390, "height": 844},
                                           java_script_enabled=False)
        page = context.new_page()
        try:
            page.goto((ROOT / "docs/blocks.html").as_uri(), wait_until="load")
            self.assertEqual(page.locator(".blocks-preview-disclosure[open]").count(), 85)
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

    def test_closed_block_preview_can_reopen_after_resizing_without_javascript(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844},
                                           java_script_enabled=False)
        page = context.new_page()
        try:
            page.goto((ROOT / "docs/blocks.html").as_uri(), wait_until="load")
            disclosure = page.locator(".blocks-preview-disclosure").nth(3)
            disclosure.locator("summary").click()
            self.assertFalse(disclosure.evaluate("e => e.open"))
            page.set_viewport_size({"width": 1280, "height": 900})
            self.assertTrue(disclosure.locator("summary").is_visible())
            disclosure.locator("summary").click()
            self.assertTrue(disclosure.evaluate("e => e.open"))
        finally:
            context.close()

    def test_block_category_links_restore_visibility_after_history_back(self):
        page = self.page_at("docs/blocks.html", 390)
        try:
            page.locator('[data-block-category-link="Marketing"]').click()
            self.assertEqual(page.locator("#blocks-category").input_value(), "Marketing")
            page.locator('[data-block-category-link="Applications"]').click()
            self.assertEqual(page.locator("#blocks-category").input_value(), "Applications")
            page.go_back()
            page.wait_for_function(
                "() => document.querySelector('#blocks-category').value === 'Marketing'"
            )
            self.assertEqual(page.locator("#blocks-category").input_value(), "Marketing")
            self.assertTrue(page.locator('[data-block-id="hero-product"]').is_visible())
            self.assertIn("block-title-hero-product", page.url)
        finally:
            page.close()

    def test_generated_docs_omit_empty_mobile_section_menu(self):
        page = self.page_at("docs/cms-integration.html", 390)
        try:
            self.assertEqual(page.locator(".docs-prose h2, .docs-prose h3").count(), 0)
            self.assertEqual(page.locator(".docs-article-toc-mobile").count(), 0)
            self.assertEqual(page.locator(".docs-article-toc-desktop").count(), 0)
        finally:
            page.close()

    def test_semantic_recipes_and_gallery_are_discoverable_on_desktop(self):
        page = self.page_at("index.html", 1440)
        try:
            for path in ("docs/semantic-components.html", "examples/semantic-compositions.html"):
                with self.subTest(path=path):
                    self.assertGreater(page.locator(f'a[href="{path}"]:visible').count(), 0)
        finally:
            page.close()

    def test_agent_index_documents_public_layout_customization(self):
        index = (ROOT / "llms.txt").read_text(encoding="utf-8")
        for token in ("--syn-shell-max", "--syn-shell-inline-inset",
                      "--syn-header-gap", "--syn-header-padding-block", "--syn-nav-gap"):
            with self.subTest(token=token):
                self.assertIn(token, index)

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
