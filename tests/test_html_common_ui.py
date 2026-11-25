"""Additional native elements and CSS-first UI recipes: source contracts."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.classes = set()
        self.js = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        self.classes.update(attrs.get('class','').split())
        if tag == 'script' or any(key.startswith('on') for key in attrs):
            self.js.append((tag, attrs))


class HtmlCommonUiContract(unittest.TestCase):
    def test_remaining_presentation_worthy_elements_are_opt_in(self):
        css = (ROOT / 'src/semantic.css').read_text()
        for tag in ('hgroup', 'time', 'data', 'cite', 'dfn', 'var', 'q',
                    'ins', 'del', 'picture', 'iframe', 'canvas', 'svg'):
            with self.subTest(tag=tag):
                self.assertIn(f'{tag}:not([class])', css)
                self.assertIn(f'{tag}[data-syn-semantic]', css)
        self.assertIn('select[multiple]:not([class])', css)
        self.assertIn('select[multiple][data-syn-semantic]', css)
        self.assertIn('textarea:not([rows]):not([class])', css)
        self.assertIn('textarea:not([rows])[data-syn-semantic]', css)

    def test_preserve_critical_native_browser_semantics(self):
        css = (ROOT / 'src/semantic.css').read_text()
        self.assertNotIn('appearance: none', css)
        self.assertNotIn('pointer-events: none', css)
        self.assertNotIn('display: none', css)
        self.assertNotIn('outline: none', css)
        self.assertIn('max-inline-size: 100%', css)
        self.assertIn('@media (forced-colors: active)', css)
        # Deliberately not replacing UA styles for replaced & specialized elements.
        for tag in ('bdi', 'bdo', 'ruby', 'rt', 'rp', 'wbr', 'template', 'slot', 'datalist'):
            self.assertNotIn(f'{tag}:not([class])', css)

    def test_common_ui_components_use_existing_core_scope_and_tokens(self):
        css = (ROOT / 'src/components/patterns.css').read_text()
        for selector in ('.syn-avatar', '.syn-avatar--sm', '.syn-avatar--lg',
                         '.syn-avatar-stack', '.syn-chip', '.syn-nav-tabs',
                         '.syn-nav-tabs [aria-current="page"]', '.syn-list-group',
                         '.syn-list-row', '.syn-list-row[aria-current="page"]',
                         '.syn-button-group', '.syn-divider-label'):
            with self.subTest(selector=selector):
                self.assertIn(selector, css)
        self.assertIn(':where(.syn-root, .syn-root *)', css)
        self.assertIn('@media (forced-colors: active)', css)
        # Navigation is just native links, not fake JavaScript-driven ARIA tabs.
        self.assertNotIn('[role="tab"]', css)
        self.assertNotIn('cursor: pointer; /* fabricated tab */', css)

    def test_alert_variants_extend_existing_alert_instead_of_duplicate_component(self):
        css = (ROOT / 'src/components/typography.css').read_text()
        self.assertIn('.syn-alert--success', css)
        self.assertIn('.syn-alert--warning', css)
        self.assertIn('.syn-alert--danger', css)

    def test_gallery_uses_native_controls_and_production_css(self):
        html = (ROOT / 'examples/common-ui.html').read_text()
        parsed = Elements()
        parsed.feed(html)
        self.assertFalse(parsed.js)
        for tag in ('nav', 'ul', 'li', 'a', 'button', 'label', 'select', 'textarea',
                    'time', 'data', 'q', 'ins', 'del', 'hgroup', 'iframe'):
            with self.subTest(tag=tag):
                self.assertIn(tag, {t for t, _ in parsed.tags})
        for css_class in ('syn-nav-tabs', 'syn-list-group', 'syn-list-row',
                          'syn-avatar', 'syn-chip', 'syn-button-group', 'syn-divider-label',
                          'syn-alert--warning', 'syn-alert--success'):
            with self.subTest(css_class=css_class):
                self.assertIn(css_class, parsed.classes)
        self.assertIn('../dist/syntyr.core.css', html)
        self.assertIn('../dist/syntyr.semantic.css', html)

    def test_core_and_presets_ship_components_without_runtime_javascript(self):
        from scripts.build import distributions, assemble
        for bundle in ('syntyr.core.css', 'syntyr.all.css', 'presets/minimal.css',
                       'presets/saas.css', 'presets/cinematic.css'):
            with self.subTest(bundle=bundle):
                css = assemble(distributions()[bundle])
                self.assertIn('.syn-nav-tabs', css)
                self.assertIn('.syn-avatar-stack', css)
        self.assertNotIn('.syn-nav-tabs', assemble(distributions()['syntyr.semantic.css']))

if __name__ == '__main__':
    unittest.main()
