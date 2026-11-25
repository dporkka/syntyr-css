"""Opt-in browser proof for unlayered CMS theme coexistence.

Run with Python Playwright installed:
  python tests/platform_embed_browser.py
Browser packages are maintainer-only; Syntyr's runtime remains CSS-only.
"""
from pathlib import Path
from html import escape
import unittest

from playwright.sync_api import sync_playwright, Error as PlaywrightError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/platform-embed.html"
LINK = '<link rel="stylesheet" href="../dist/syntyr.embed.css">'


def html_with(css):
    fixture = FIXTURE.read_text(encoding="utf-8")
    assert LINK in fixture
    return fixture.replace(LINK, "<style>" + css + "</style>")


def background(page, selector):
    return page.locator(selector).evaluate(
        "(element) => getComputedStyle(element).backgroundColor")


class PlatformEmbedBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()

    @classmethod
    def tearDownClass(cls):
        cls.playwright.stop()

    def test_embed_overrides_unlayered_host_button_rule_without_leaking(self):
        embedded = (ROOT / "dist/syntyr.embed.css").read_text()
        layered = (ROOT / "dist/syntyr.core.css").read_text()
        for engine in ("chromium", "firefox"):
            with self.subTest(engine=engine):
                browser = getattr(self.playwright, engine).launch(headless=True)
                try:
                    page = browser.new_page(viewport={"width": 1024, "height": 768})
                    page.set_content(html_with(layered), wait_until="load")
                    # This is the real cascade-layer compatibility failure:
                    # host unlayered styles beat the layered component.
                    self.assertEqual(background(page, "#cms-syntyr-control"),
                                     "rgb(116, 58, 32)")
                    page.set_content(html_with(embedded), wait_until="load")
                    self.assertEqual(background(page, "#cms-syntyr-control"),
                                     "rgb(36, 88, 198)")
                    self.assertEqual(background(page, "#cms-host-control"),
                                     "rgb(116, 58, 32)")
                    self.assertEqual(
                        page.locator(".syn-root").evaluate(
                            "(e) => getComputedStyle(e).getPropertyValue('--syn-accent').trim()"),
                        "#2458c6")
                    self.assertEqual(
                        page.locator("#cms-more").evaluate("(e) => e.tagName"),
                        "DETAILS")
                    page.close()
                finally:
                    browser.close()

    def test_site_builder_iframe_styles_do_not_cross_documents(self):
        # Models the iframe boundary of Wix HTML Embed and isolated embeds.
        css = (ROOT / "dist/syntyr.embed.css").read_text()
        browser = self.playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            embedded_html = (
                '<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<style>' + css + '</style></head><body>'
                '<section class="syn-root" data-syn-theme="studio">'
                '<button id="iframe-button" class="syn-button syn-button--primary">'
                'Inside embed</button></section></body></html>'
            )
            host_html = (
                '<!doctype html><html><head><style>'
                'button{background:#743a20;color:white}</style></head><body>'
                '<button id="outside-button">Host button</button>'
                '<iframe title="Syntyr embedded widget" sandbox="allow-same-origin"'
                ' srcdoc="' + escape(embedded_html, quote=True) + '"></iframe>'
                '</body></html>'
            )
            page.set_content(host_html, wait_until="load")
            self.assertEqual(background(page, "#outside-button"), "rgb(116, 58, 32)")
            self.assertEqual(page.frame_locator('iframe').locator('#iframe-button').evaluate(
                "(element) => getComputedStyle(element).backgroundColor"), "rgb(36, 88, 198)")
            page.evaluate(
                '() => { const button = document.createElement("button");'
                'button.id = "outside-syntyr";'
                'button.className = "syn-button syn-button--primary";'
                'document.body.appendChild(button); }'
            )
            self.assertEqual(background(page, "#outside-syntyr"), "rgb(116, 58, 32)")
        finally:
            browser.close()

    def test_webkit_embed_if_system_dependencies_available(self):
        try:
            browser = self.playwright.webkit.launch(headless=True)
        except PlaywrightError as error:
            if "libevent-2.1.so.7" in str(error):
                self.skipTest("WebKit runtime missing OS libevent-2.1.so.7 on Gertrude")
            raise
        try:
            page = browser.new_page()
            page.set_content(
                html_with((ROOT / "dist/syntyr.embed.css").read_text()),
                wait_until="load")
            self.assertEqual(background(page, "#cms-syntyr-control"), "rgb(36, 88, 198)")
            self.assertEqual(background(page, "#cms-host-control"), "rgb(116, 58, 32)")
        finally:
            browser.close()

    def test_narrow_embed_is_visible_and_not_horizontally_clipped(self):
        browser = self.playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 320, "height": 640})
            page.set_content(
                html_with((ROOT / "dist/syntyr.embed.css").read_text()),
                wait_until="load")
            region = page.locator(".syn-root")
            self.assertTrue(region.is_visible())
            self.assertLessEqual(
                region.evaluate("(e) => e.getBoundingClientRect().right"), 321)
            self.assertLessEqual(
                page.evaluate("document.documentElement.scrollWidth"), 321)
        finally:
            browser.close()


if __name__ == "__main__":
    unittest.main()
