"""Rendered spacing, density, and 320px reflow checks for Syntyr themes.

Run after ``python3 scripts/build.py`` with a developer Playwright install:
    python tests/theme_layout_browser.py
"""
from pathlib import Path
import os
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class ThemeLayoutBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = getattr(cls.playwright, os.environ.get("SYNTYR_TEST_BROWSER", "chromium")).launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 375, "height": 900})
        self.page.goto((ROOT / "examples/themes.html").as_uri())

    def tearDown(self):
        self.page.close()

    def test_stack_gap_does_not_accumulate_heading_and_paragraph_margins(self):
        result = self.page.evaluate("""() => {
          const root = document.createElement('section');
          root.innerHTML = `
            <div class="syn-stack" id="contract-stack">
              <h2 class="syn-heading">Section heading</h2><p>Supporting copy</p>
            </div>
            <div class="syn-u-stack" id="contract-utility-stack">
              <h2 class="syn-section-heading">Section heading</h2><p>Supporting copy</p>
            </div>
            <div class="syn-u-stack" id="contract-explicit-stack">
              <h2 class="syn-heading">Heading</h2><p class="syn-u-mt-3">Intentional separation</p>
            </div>
            <div class="syn-prose" id="contract-prose">
              <p>First paragraph</p><p>Second paragraph</p>
            </div>`;
          document.body.append(root);
          function gap(id) {
            const box = document.getElementById(id);
            const [heading, para] = box.children;
            return {
              gap: parseFloat(getComputedStyle(box).rowGap),
              separation: para.getBoundingClientRect().top - heading.getBoundingClientRect().bottom,
              headingMargin: parseFloat(getComputedStyle(heading).marginBlockEnd),
              paragraphMargin: parseFloat(getComputedStyle(para).marginBlockStart),
            };
          }
          return {stack: gap('contract-stack'), utility: gap('contract-utility-stack'),
                  explicit: gap('contract-explicit-stack'), prose: gap('contract-prose')};
        }""")
        for name in ("stack", "utility"):
            with self.subTest(layout=name):
                self.assertAlmostEqual(result[name]["separation"], result[name]["gap"], delta=1)
                self.assertEqual(result[name]["headingMargin"], 0)
        self.assertAlmostEqual(result["explicit"]["separation"],
                               result["explicit"]["gap"] + 18, delta=1)
        self.assertGreater(result["prose"]["separation"], 0)

    def test_layout_roles_remain_customizable_and_scoped(self):
        self.page.set_viewport_size({"width": 768, "height": 900})
        result = self.page.evaluate("""() => {
          document.body.style.setProperty('--syn-page-gutter', '2rem');
          document.body.style.setProperty('--syn-content-max', '20rem');
          document.body.style.setProperty('--syn-content-gap', '2rem');
          const region = document.createElement('div');
          region.innerHTML = `<div class="syn-grid" id="contract-grid"><div>A</div><div>B</div></div>
            <div class="syn-layout" id="contract-layout"><div>A</div><div>B</div></div>`;
          document.body.append(region);
          const shell = document.querySelector('.syn-shell').getBoundingClientRect();
          return {shellWidth: shell.width, gridGap: getComputedStyle(region.querySelector('.syn-grid')).gap,
                  layoutGap: getComputedStyle(region.querySelector('.syn-layout')).gap};
        }""")
        self.assertAlmostEqual(result["shellWidth"], 320, delta=1)
        self.assertEqual(result["gridGap"], "32px")
        self.assertEqual(result["layoutGap"], "32px")
        self.page.set_viewport_size({"width": 375, "height": 900})
        narrow_width = self.page.locator('.syn-shell').evaluate('(element) => element.getBoundingClientRect().width')
        self.assertAlmostEqual(narrow_width, 311, delta=1)

    def test_panel_padding_inherits_host_override_across_density_scopes(self):
        padding = self.page.evaluate("""() => {
          document.documentElement.style.setProperty('--syn-panel-padding', '23px');
          const wrapper = document.createElement('div');
          wrapper.innerHTML = '<article class="syn-panel">Regular</article><section data-syn-density="compact"><article class="syn-panel">Compact</article></section>';
          document.body.append(wrapper);
          return Array.from(wrapper.querySelectorAll('.syn-panel'), el => getComputedStyle(el).paddingBlockStart);
        }""")
        self.assertEqual(padding, ["23px", "23px"])

    def test_panel_padding_responds_to_nested_density_and_resets(self):
        paddings = self.page.evaluate("""() => {
          const el = document.createElement('div');
          el.innerHTML = `<article class="syn-panel" id="panel-regular">Regular</article>
            <section data-syn-density="compact"><article class="syn-panel" id="panel-compact">Compact</article>
              <section data-syn-density="comfortable"><article class="syn-panel" id="panel-reset">Reset</article></section>
            </section>
            <section data-syn-density="spacious"><article class="syn-panel" id="panel-spacious">Spacious</article></section>`;
          document.body.append(el);
          return Object.fromEntries(['regular','compact','reset','spacious'].map(name =>
            [name, parseFloat(getComputedStyle(document.getElementById('panel-'+name)).paddingBlockStart)]));
        }""")
        self.assertLess(paddings["compact"], paddings["regular"])
        self.assertAlmostEqual(paddings["reset"], paddings["regular"], delta=.1)
        self.assertGreater(paddings["spacious"], paddings["regular"])

    def test_theme_gallery_previews_real_controls_with_semantic_labels(self):
        previews = self.page.evaluate("""() => Array.from(document.querySelectorAll('.theme-tile')).map(tile => {
          const field = tile.querySelector('.theme-sample .syn-input');
          const label = field && tile.querySelector('label[for="' + field.id + '"]');
          return {theme: tile.dataset.synTheme, readonly: field?.readOnly, labeled: !!label,
                  badge: !!tile.querySelector('.theme-sample .syn-badge')};
        })""")
        self.assertEqual(len(previews), 7)
        for preview in previews:
            with self.subTest(theme=preview['theme']):
                self.assertTrue(preview['readonly'])
                self.assertTrue(preview['labeled'])
                self.assertTrue(preview['badge'])

    def test_flagship_heroes_have_mobile_rhythm_without_horizontal_overflow(self):
        self.page.set_viewport_size({"width": 320, "height": 900})
        for theme in ('studio', 'noir', 'grid'):
            with self.subTest(theme=theme):
                self.page.goto((ROOT / f"examples/flagship-{theme}.html").as_uri())
                metrics = self.page.evaluate("""() => ({
                  pad: parseFloat(getComputedStyle(document.querySelector('.flagship-hero')).paddingBlockStart),
                  page: document.documentElement.scrollWidth,
                  viewport: document.documentElement.clientWidth,
                })""")
                self.assertLessEqual(metrics['pad'], 40)
                self.assertLessEqual(metrics['page'], metrics['viewport'] + 1)

    def test_theme_gallery_reflows_with_larger_text_and_rtl(self):
        self.page.set_viewport_size({"width": 320, "height": 900})
        self.page.evaluate("""() => {
          document.documentElement.style.fontSize = '32px';
          document.body.dir = 'rtl';
        }""")
        widths = self.page.evaluate("""() => ({
          page: document.documentElement.scrollWidth,
          viewport: document.documentElement.clientWidth,
        })""")
        self.assertLessEqual(widths["page"], widths["viewport"] + 1)

    def test_all_seven_theme_tiles_reflow_without_page_overflow(self):
        for width in (320, 375, 768, 1280):
            with self.subTest(viewport=width):
                self.page.set_viewport_size({"width": width, "height": 900})
                measurements = self.page.evaluate("""() => ({
                  pageWidth: document.documentElement.scrollWidth,
                  viewport: document.documentElement.clientWidth,
                  tiles: document.querySelectorAll('.theme-tile').length
                })""")
                self.assertEqual(measurements["tiles"], 7)
                self.assertLessEqual(measurements["pageWidth"], measurements["viewport"] + 1)


if __name__ == "__main__":
    unittest.main()
