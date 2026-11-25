"""An optional docs-only theme tool must not alter the CSS runtime contract."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EditorMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
        self.ids = set()
        self.color_controls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'link'):
            self.assets.append(attrs.get('src', attrs.get('href', '')))
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'input' and attrs.get('type') == 'color':
            self.color_controls.append(attrs)


class ThemeEditorContract(unittest.TestCase):
    def test_editor_is_self_contained_and_browser_optional(self):
        page = (ROOT / 'docs/theme-editor.html').read_text()
        parsed = EditorMarkup()
        parsed.feed(page)
        for item in ('theme', 'accent', 'on-accent', 'preview', 'contrast-result', 'generated-css', 'reset-theme'):
            self.assertIn(item, parsed.ids)
        self.assertEqual(len(parsed.color_controls), 6)
        self.assertIn('theme-editor.js', parsed.assets)
        self.assertIn('../dist/syntyr.core.css', parsed.assets)
        self.assertTrue(all(not x.startswith(('https:', 'http:', '//')) for x in parsed.assets))
        self.assertIn('aria-live="polite"', page)
        self.assertIn('theme-editor.html', (ROOT / 'docs/index.html').read_text())
        self.assertIn('theme-editor.html', (ROOT / 'README.md').read_text())

    def test_editor_checks_contrast_and_never_modifies_distribution(self):
        js = (ROOT / 'docs/theme-editor.js').read_text()
        for fragment in ('4.5', 'addEventListener', 'getComputedStyle', 'textContent',
                         'removeProperty', 'setProperty', 'data-syn-theme'):
            self.assertIn(fragment, js)
        self.assertNotIn('fetch(', js)
        self.assertNotIn('localStorage', js)
        for name in ('syntyr.core.css', 'syntyr.all.css'):
            self.assertNotIn('theme-editor.js', (ROOT / 'dist' / name).read_text())


    def test_soft_accent_is_derived_from_overridden_accent_in_each_theme(self):
        tokens = (ROOT / 'src/tokens.css').read_text()
        # A user-supplied primary color must not retain the original palette's hover tint.
        # Every shipped theme must provide a tint derived from its active accent.
        themes = set(re.findall(r'data-syn-theme="([^"]+)"', tokens))
        named_themes = themes - {"auto"}  # auto derives its tint through light-dark()
        self.assertEqual(
            tokens.count('--syn-accent-soft: color-mix(in srgb, var(--syn-accent)'),
            len(named_themes),
        )
        self.assertGreaterEqual(len(themes), 7)
        self.assertNotIn('--syn-accent-soft: rgb(', tokens)

    def test_editor_offers_all_seven_shipped_palettes(self):
        page = (ROOT / 'docs/theme-editor.html').read_text()
        for name in ('grid', 'noir', 'studio', 'industrial', 'terminal', 'corporate', 'minimal'):
            with self.subTest(theme=name):
                self.assertIn(f'<option value="{name}">', page)

    def test_exported_palette_supports_embedded_theme_scopes(self):
        js = (ROOT / 'docs/theme-editor.js').read_text()
        # The preview is a nested data-syn-theme element; generated overrides must work there.
        self.assertIn('.syn-root [data-syn-theme=', js)

    def test_editor_exports_composable_preset_with_density_and_radius(self):
        html = (ROOT / 'docs/theme-editor.html').read_text()
        js = (ROOT / 'docs/theme-editor.js').read_text()
        parser = EditorMarkup()
        parser.feed(html)
        for key in ('density', 'radius', 'generated-preset', 'copy-preset', 'preset-feedback'):
            self.assertIn(key, parser.ids)
        for name in ('compact', 'comfortable', 'spacious'):
            self.assertIn(f'<option value="{name}"', html)
        self.assertIn('data-syn-density', js)
        for key in ('typography','spacing','page-bg','surface','body-text','muted-text',
                    'contrast-background-result','contrast-surface-result','contrast-muted-result'):
            self.assertIn(key, parser.ids)
        self.assertIn('--syn-radius', js)
        self.assertIn('JSON.stringify', js)
        self.assertIn('navigator.clipboard', js)
        self.assertNotIn('eval(', js)


if __name__ == '__main__':
    unittest.main()
