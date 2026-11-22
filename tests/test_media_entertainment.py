"""Contracts for the opt-in Media & Entertainment recipes and static example."""

import json
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.nodes.append((tag, dict(attrs)))


class MediaEntertainmentTests(unittest.TestCase):
    def test_module_is_opt_in_and_package_exported(self):
        from sys import path as sys_path
        sys_path.insert(0, str(ROOT / 'scripts'))
        from build import distributions

        css = distributions()
        self.assertEqual(css['syntyr.media.css'], ('media.css',))
        self.assertNotIn('media.css', css['syntyr.core.css'])
        self.assertNotIn('media.css', css['syntyr.all.css'])
        exports = json.loads((ROOT / 'package.json').read_text())['exports']
        self.assertEqual(exports['./media.css'], './dist/syntyr.media.css')
        self.assertEqual((ROOT / 'dist/syntyr.media.css').read_text(),
                         (ROOT / 'src/media.css').read_text().strip() + '\n')

    def test_primitive_classes_and_accessibility_states(self):
        css = (ROOT / 'src/media.css').read_text()
        for selector in (
            '.syn-media-shell', '.syn-media-navigation',
            '.syn-media-navigation__desktop', '.syn-media-navigation__mobile',
            '.syn-media-hero', '.syn-media-hero__content',
            '.syn-media-card', '.syn-media-card__visual',
            '.syn-media-card__link', '.syn-media-rail',
            '.syn-media-section', '.syn-media-search',
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, css)
        for marker in (
            '@layer syn.recipes',
            ':focus-visible', '[aria-current="page"]',
            'prefers-reduced-motion: reduce', 'forced-colors: active',
            'env(safe-area-inset-bottom, 0px)', 'scroll-snap-type',
            '--syn-media-card-ratio', '--syn-media-hero-image',
            'max-width: 48rem', '.syn-root',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, css)
        self.assertNotIn('@import', css)
        self.assertNotIn('http://', css)
        self.assertNotIn('https://', css)

    def test_demo_is_semantic_zero_js_with_no_remote_assets(self):
        html = (ROOT / 'examples/media-entertainment.html').read_text()
        parsed = Markup()
        parsed.feed(html)
        self.assertNotIn('script', parsed.tags)
        self.assertIn('main', parsed.tags)
        self.assertIn('h1', parsed.tags)
        self.assertIn('label', parsed.tags)
        self.assertIn('input', parsed.tags)
        self.assertIn('article', parsed.tags)
        self.assertIn('svg', parsed.tags)
        self.assertNotIn('https://', html)
        self.assertNotIn('http://', html)
        self.assertNotIn('user-scalable=no', html)
        self.assertIn('../dist/syntyr.media.css', html)
        self.assertIn('class="syn-media-hero', html)
        self.assertTrue(any('syn-media-rail' in attrs.get('class', '').split()
                            for _, attrs in parsed.nodes))

        headings = {attrs['id'] for tag, attrs in parsed.nodes if 'id' in attrs}
        self.assertEqual(len(headings), sum(1 for tag, attrs in parsed.nodes if 'id' in attrs))
        self.assertTrue({attrs['aria-labelledby'] for tag, attrs in parsed.nodes
                         if attrs.get('aria-labelledby')} <= headings)
        navs = [attrs for tag, attrs in parsed.nodes if tag == 'nav']
        self.assertGreaterEqual(len(navs), 2)
        self.assertTrue(all(attrs.get('aria-label') for attrs in navs))
        rails = [attrs for tag, attrs in parsed.nodes
                 if 'syn-media-rail' in attrs.get('class', '').split()]
        self.assertGreaterEqual(len(rails), 1)
        self.assertTrue(all(attrs.get('tabindex') == '0' and
                            attrs.get('role') == 'region' and
                            attrs.get('aria-label') for attrs in rails))
        anchors = [attrs for tag, attrs in parsed.nodes if tag == 'a']
        self.assertTrue(all(attrs.get('href') for attrs in anchors))
        search = [attrs for tag, attrs in parsed.nodes if tag == 'input' and
                  attrs.get('type') == 'search']
        self.assertEqual(len(search), 1)
        self.assertTrue(search[0].get('name'))

    def test_public_example_and_usage_docs_are_allowlisted(self):
        cloudflare = (ROOT / 'scripts/build_cloudflare_site.py').read_text()
        self.assertIn('"media-entertainment.html"', cloudflare)
        self.assertIn('"media-entertainment.md"', cloudflare)
        guide = (ROOT / 'docs/media-entertainment.md').read_text()
        for phrase in ('syntyr.media.css', 'Keyboard', 'reduced motion',
                       'framework', 'real images'):
            self.assertIn(phrase, guide)


class MediaStandaloneDefaultsTests(unittest.TestCase):
    def test_rail_and_card_defaults_work_without_shell(self):
        css = (ROOT / 'src/media.css').read_text()
        self.assertIn('gap: var(--syn-media-gap, clamp(.75rem, 1.8vw, 1.25rem))', css)
        self.assertIn('var(--syn-media-rail-item-size, clamp(10rem, 18vw, 14.5rem))', css)
        self.assertIn('aspect-ratio: var(--syn-media-card-ratio, 2 / 3)', css)


if __name__ == '__main__':
    unittest.main()
