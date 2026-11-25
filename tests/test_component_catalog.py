"""Developer-facing component catalog is build-free and progressively enhanced."""
from html.parser import HTMLParser
from html import unescape
import re
from pathlib import Path
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


class CatalogHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.ids = []
        self.copy_buttons = 0
        self.inline_scripts = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'article' and 'catalog-card' in a.get('class', '').split():
            self.items.append(a)
        if tag == 'button' and 'data-catalog-copy' in a:
            self.copy_buttons += 1
        if tag == 'script' and 'src' not in a:
            self.inline_scripts += 1


class CatalogTests(unittest.TestCase):
    def test_catalog_is_static_without_javascript(self):
        page = (ROOT / 'docs/catalog.html').read_text()
        parsed = CatalogHTML()
        parsed.feed(page)
        self.assertGreaterEqual(len(parsed.items), 8)
        self.assertEqual(len(parsed.items), parsed.copy_buttons)
        self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
        self.assertEqual(parsed.inline_scripts, 0)
        self.assertIn('id="catalog-search"', page)
        self.assertIn('id="catalog-results"', page)
        for card in parsed.items:
            self.assertTrue(card.get('data-catalog-keywords'))
        self.assertIn('hidden data-catalog-copy', page)  # Copy enhanced only when JS is present
        self.assertIn('class="catalog-preview"', page)  # Live examples remain visible without JS
        self.assertIn('class="catalog-source"', page)  # Copyable snippets remain visible without JS
        pairs = re.findall(
            r'<div class="catalog-preview">\n(.*?)\n          </div>\n          <details class="catalog-code-details">.*?<pre class="catalog-source"><code>(.*?)</code></pre>',
            page, re.S)
        self.assertEqual(len(pairs), len(parsed.items))
        for preview_html, escaped_source in pairs:
            self.assertEqual(preview_html.strip(), unescape(escaped_source).strip())


    def test_optional_module_examples_are_discoverable_without_javascript(self):
        page = (ROOT / 'docs/catalog.html').read_text()
        parsed = CatalogHTML()
        parsed.feed(page)
        self.assertGreaterEqual(len(parsed.items), 32)
        expected = {
            'catalog-input-group-title': 'forms',
            'catalog-crm-filters-title': 'forms',
            'catalog-recovery-state-title': 'interactive',
            'catalog-geometry-frame-title': 'layout',
            'catalog-viz-bars-title': 'data',
        }
        for heading, category in expected.items():
            with self.subTest(heading=heading):
                self.assertEqual(
                    sum(card.get('aria-labelledby') == heading and
                        card.get('data-catalog-category') == category
                        for card in parsed.items), 1)
        for module in ('syntyr.recipes.css', 'syntyr.geometry.css', 'syntyr.viz.css'):
            self.assertIn(module, page)
        self.assertIn(f'{len(parsed.items)} examples available.', page)
        agent_index = (ROOT / 'llms.txt').read_text()
        self.assertIn(f'{len(parsed.items)}-example native HTML component catalog', agent_index)
        self.assertIn('optional recipes, geometry', agent_index)

    def test_search_and_copy_behaviour_is_documentation_only(self):
        js = (ROOT / 'docs/catalog.js').read_text()
        self.assertIn('addEventListener("input"', js)
        self.assertIn('navigator.clipboard.writeText', js)
        self.assertIn('card.hidden =', js)
        self.assertIn('textContent', js)
        self.assertNotIn('innerHTML =', js)
        self.assertTrue((ROOT / 'docs/catalog.css').is_file())
        self.assertIn('catalog.html', (ROOT / 'docs/index.html').read_text())
        self.assertIn('catalog.html', (ROOT / 'README.md').read_text())
        script = (ROOT / 'scripts/build_cloudflare_site.py').read_text()
        for asset in ('catalog.html', 'catalog.css', 'catalog.js'):
            self.assertIn('"' + asset + '"', script)

    def test_cloudflare_build_includes_catalog(self):
        # Each invocation needs its own output. A fixed shared /tmp path can
        # collide with concurrent CI or local test runs during site cleanup.
        with TemporaryDirectory(prefix='syntyr-catalog-contract-') as temp:
            output = Path(temp) / 'publish'
            p = subprocess.run([sys.executable, 'scripts/build_cloudflare_site.py',
                                '--output', str(output)],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            for asset in ('catalog.html', 'catalog.css', 'catalog.js'):
                self.assertTrue((output / 'docs' / asset).is_file())


if __name__ == '__main__':
    unittest.main()
