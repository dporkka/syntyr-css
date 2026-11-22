"""Native navigation sections stay semantic, inert in demos and copy-owned."""
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
IDS = {'site-header', 'site-footer', 'mega-navigation'}


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))


class NavigationSectionsTests(unittest.TestCase):
    def test_three_distinct_blocks_extend_editorial_and_existing_workflows(self):
        blocks = json.loads((ROOT / 'blocks/manifest.json').read_text())['blocks']
        ids = [item['id'] for item in blocks]
        self.assertEqual(len(ids), 74)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(IDS <= set(ids))
        self.assertTrue({'site-header', 'site-footer', 'mega-navigation',
                         'article-detail', 'case-study-preview', 'contact-quote',
                         'resource-workspace', 'crm-workspace', 'billing-workspace'} <= set(ids))
        for block in blocks:
            if block['id'] in IDS:
                self.assertEqual(block['category'], 'Navigation')
                self.assertIn('core', block['modules'])

    def test_navigation_stays_native_keyboard_friendly(self):
        for ident in IDS:
            with self.subTest(block=ident):
                source = (ROOT / 'blocks/snippets' / f'{ident}.html').read_text()
                parsed = Tags()
                parsed.feed(source)
                self.assertIn('nav', parsed.tags)
                self.assertGreaterEqual(len([1 for tag, attrs in parsed.attrs
                                             if tag == 'nav' and attrs.get('aria-label')]), 1)
                self.assertNotIn('script', parsed.tags)
                for tag, attrs in parsed.attrs:
                    if tag == 'a':
                        self.assertTrue(attrs.get('href', '').startswith('/'))
        mega = Tags()
        mega.feed((ROOT / 'blocks/snippets/mega-navigation.html').read_text())
        self.assertEqual(mega.tags.count('details'), 1)
        self.assertEqual(mega.tags.count('summary'), 1)
        self.assertIn('open', dict(next(attrs for tag, attrs in mega.attrs if tag == 'details')))

    def test_navigation_guide_counts_match_manifest(self):
        count = len(json.loads((ROOT / 'blocks/manifest.json').read_text())['blocks'])
        guide = (ROOT / 'docs/blocks-guide.md').read_text()
        for phrase in (f'Browse {count} blocks', f'all {count} static previews',
                       f'contains the {count} MIT', f'same {count} MIT blocks'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)

    def test_gallery_preview_has_inert_links_and_filterable_navigation_category(self):
        html = (ROOT / 'docs/blocks.html').read_text()
        for ident in IDS:
            with self.subTest(block=ident):
                label = f'data-block-id="{ident}"'
                self.assertEqual(html.count(label), 1)
                card = html.split(label, 1)[1].split('      </article>', 1)[0]
                preview = card.split('<div class="blocks-preview">', 1)[1].split('<details class="blocks-details">', 1)[0]
                self.assertNotIn('href=', preview)
                self.assertIn('blocks-source', card)
        self.assertTrue('<option value="Navigation">Navigation</option>' in html)


if __name__ == '__main__':
    unittest.main()
