"""Independent editorial sections extracted without changing existing canonical blocks."""
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EDITORIAL = {
    'article-detail', 'article-featured', 'article-grid',
    'author-profile', 'case-study-preview',
}


class ContentTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = set()
        self.labels = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        values = dict(attrs)
        if values.get('id'):
            self.ids.add(values['id'])
        if values.get('aria-labelledby'):
            self.labels.append(values['aria-labelledby'])
        if tag == 'a':
            self.links.append(values.get('href'))


class EditorialSectionsTests(unittest.TestCase):
    def test_five_editorial_blocks_preserve_first_extraction(self):
        blocks = json.loads((ROOT / 'blocks/manifest.json').read_text())['blocks']
        ids = {block['id'] for block in blocks}
        self.assertEqual(len(ids), len(blocks))
        self.assertEqual(len(blocks), 62)
        self.assertTrue(EDITORIAL <= ids)
        for original in ('logo-wall', 'services-grid', 'portfolio-grid',
                         'resource-workspace', 'crm-workspace', 'billing-workspace'):
            self.assertIn(original, ids)
        for block in blocks:
            if block['id'] in EDITORIAL:
                self.assertEqual(block['modules'], ['core'])
                self.assertIn(block['category'], {'Editorial', 'Portfolio'})

    def test_editorial_content_uses_semantic_native_markup(self):
        for ident in EDITORIAL:
            with self.subTest(ident=ident):
                source = (ROOT / 'blocks/snippets' / f'{ident}.html').read_text()
                parsed = ContentTags()
                parsed.feed(source)
                self.assertIn('h2', parsed.tags)
                self.assertTrue(parsed.labels)
                self.assertTrue(set(parsed.labels) <= parsed.ids)
                self.assertTrue(parsed.links)
                self.assertTrue(all(link and link.startswith('/') for link in parsed.links))
                self.assertNotIn('<script', source)
        self.assertIn('<time datetime=', (ROOT / 'blocks/snippets/article-grid.html').read_text())
        self.assertIn('<time datetime=', (ROOT / 'blocks/snippets/article-detail.html').read_text())

    def test_block_guide_counts_match_canonical_manifest(self):
        blocks = json.loads((ROOT / 'blocks/manifest.json').read_text())['blocks']
        count = len(blocks)
        guide = (ROOT / 'docs/blocks-guide.md').read_text()
        for expected in (f'Browse {count} blocks', f'The {count} copy-owned',
                         f'all {count} static previews', f'contains the {count} MIT',
                         f'same {count} MIT blocks'):
            with self.subTest(expected=expected):
                self.assertIn(expected, guide)

    def test_every_new_editorial_block_is_copyable_and_filterable(self):
        html = (ROOT / 'docs/blocks.html').read_text()
        for ident in EDITORIAL:
            with self.subTest(ident=ident):
                self.assertEqual(html.count(f'data-block-id="{ident}"'), 1)
                self.assertIn(f'block-title-{ident}', html)
        self.assertIn('<option value="Editorial">Editorial</option>', html)


if __name__ == '__main__':
    unittest.main()
