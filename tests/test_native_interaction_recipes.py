"""The standard interaction recipes are browser-owned, copyable and script-free."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RecipeDOM(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = []
        self.scripts = []
        self.event_handlers = []
        self.details_groups = {}
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'script':
            self.scripts.append(attrs)
        if tag == 'a':
            self.anchors.append(attrs.get('href', ''))
        if tag == 'details' and attrs.get('name'):
            self.details_groups.setdefault(attrs['name'], []).append(attrs)
        self.event_handlers.extend(k for k in attrs if k.lower().startswith('on'))

    def elements(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


class NativeInteractionRecipes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "examples/native-interactions.html"
        cls.html = cls.path.read_text(encoding="utf-8") if cls.path.exists() else ""
        cls.page = RecipeDOM()
        cls.page.feed(cls.html)

    def test_real_native_elements_and_no_inline_application_js(self):
        self.assertEqual(self.page.scripts, [])
        self.assertEqual(self.page.event_handlers, [])
        self.assertEqual(len(self.page.ids), len(set(self.page.ids)))
        self.assertTrue(self.page.elements('main'))
        for tag in ('details', 'summary', 'search', 'form', 'dialog',
                    'datalist', 'option', 'output', 'meter', 'label'):
            with self.subTest(tag=tag):
                self.assertGreater(len(self.page.elements(tag)), 0)
        for word in ('static', 'server', 'no JavaScript', 'not submit a destructive action'):
            self.assertIn(word, self.html)

    def test_accordion_uses_native_exclusive_disclosure(self):
        group = self.page.details_groups.get('native-interaction-faq', [])
        self.assertGreaterEqual(len(group), 3)
        self.assertEqual(sum('open' in item for item in group), 1)
        for tag in self.page.elements('summary'):
            self.assertNotIn('role', tag)
            self.assertNotIn('tabindex', tag)

    def test_search_is_get_form_with_associated_label(self):
        self.assertTrue(self.page.elements('search'))
        forms = self.page.elements('form')
        self.assertTrue(any(f.get('method') == 'get' and
                            f.get('action') == 'native-interactions.html' for f in forms))
        fields = [i for i in self.page.elements('input') if i.get('type') == 'search']
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0].get('name'), 'q')
        self.assertIn('required', fields[0])
        self.assertTrue(any(label.get('for') == fields[0].get('id') for label in self.page.elements('label')))

    def test_dialog_is_native_modal_with_nonmutating_choice(self):
        dialogs = self.page.elements('dialog')
        self.assertEqual(len(dialogs), 1)
        target = dialogs[0].get('id')
        self.assertTrue(any(b.get('commandfor') == target and
                            b.get('command') == 'show-modal' for b in self.page.elements('button')))
        self.assertTrue(any(f.get('method') == 'dialog' for f in self.page.elements('form')))
        self.assertTrue(any(b.get('value') == 'cancel' for b in self.page.elements('button')))
        self.assertTrue(any(b.get('value') == 'confirm' for b in self.page.elements('button')))
        self.assertIn('aria-labelledby', dialogs[0])

    def test_datalist_and_metrics_are_semantic_not_custom_widgets(self):
        lists = self.page.elements('datalist')
        self.assertEqual(len(lists), 1)
        inputs = self.page.elements('input')
        self.assertTrue(any(i.get('list') == lists[0].get('id') for i in inputs))
        self.assertGreaterEqual(len(self.page.elements('option')), 3)
        self.assertTrue(any(m.get('low') is not None and m.get('high') is not None and
                            m.get('optimum') is not None for m in self.page.elements('meter')))
        self.assertEqual(len(self.page.elements('output')), 1)
        self.assertNotIn('role="combobox"', self.html)
        self.assertNotIn('role="dialog"', self.html)

    def test_docs_catalog_and_distribution_expose_the_recipes(self):
        docs = (ROOT / 'docs/native-patterns.md').read_text(encoding='utf-8')
        catalog = (ROOT / 'docs/catalog.html').read_text(encoding='utf-8')
        site = (ROOT / 'scripts/build_cloudflare_site.py').read_text(encoding='utf-8')
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('"native-interactions.html"', site)
        self.assertIn('native-interactions.html', docs)
        self.assertIn('native-interactions.html', readme)
        self.assertIn('Native interaction recipes', docs)
        self.assertIn('Application-owned behavior', docs)
        card_count = catalog.count('class="catalog-card syn-panel"')
        self.assertGreaterEqual(card_count, 16)
        self.assertIn(f'{card_count} examples available.', catalog)
        for name in ('Exclusive accordion', 'GET search form', 'Confirmation dialog',
                     'Datalist suggestions', 'Meter and output'):
            with self.subTest(name=name):
                self.assertIn(name, catalog)
        self.assertIn('syntyr.native-recipes.css', docs)

    def test_classed_overlays_reflow_without_new_components(self):
        css = (ROOT / 'src/components/overlays.css').read_text(encoding='utf-8')
        # Physical viewport axes must remain physical under vertical writing modes.
        self.assertIn('max-width: calc(100vw - 2rem)', css)
        self.assertIn('max-height: min(80vh, 40rem)', css)
        self.assertIn('max-height: min(80dvh, 40rem)', css)
        self.assertIn('calc(100dvh - 1.75rem)', css)
        self.assertNotIn('max-inline-size: calc(100vw - 2rem)', css)
        self.assertIn('overflow: auto', css)
        self.assertIn('box-sizing: border-box', css)
        self.assertIn('max-height: min(80dvh, 40rem)', (ROOT / 'dist/syntyr.core.css').read_text())
        self.assertNotIn('.syn-confirmation-dialog', css)
        self.assertNotIn('.syn-accordion', css)


if __name__ == '__main__':
    unittest.main()
