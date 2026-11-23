"""Publishing/commerce sections remain source-owned and browser-native."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
ADDITIONS={'docs-layout','content-collection','product-collection','category-showcase'}

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags=[]
        self.ids=set()
        self.labelled=[]
        self.links=[]
        self.named_inputs=[]
    def handle_starttag(self,tag,attrs):
        self.tags.append(tag)
        a=dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if a.get('aria-labelledby'):
            self.labelled.append(a['aria-labelledby'])
        if tag == 'a':
            self.links.append(a.get('href'))
        if tag in ('input','select') and a.get('name'):
            self.named_inputs.append(a['name'])

class PublishingCommerceTests(unittest.TestCase):
    def test_only_four_unique_blocks_added_without_removing_existing_blocks(self):
        manifest=json.loads((ROOT/'blocks/manifest.json').read_text())['blocks']
        ids=[x['id'] for x in manifest]
        self.assertEqual(len(ids),91)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(ADDITIONS <= set(ids))
        self.assertTrue({'site-header','site-footer','mega-navigation',
                         'article-detail','article-grid','contact-quote',
                         'resource-workspace','crm-workspace','billing-workspace'} <= set(ids))
        for block in manifest:
            if block['id'] in ADDITIONS:
                self.assertIn(block['category'],('Technical','Publishing','Commerce'))
                self.assertIn('core',block['modules'])

    def test_semantic_markup_and_accessible_names(self):
        for ident in ADDITIONS:
            with self.subTest(block=ident):
                source=(ROOT/'blocks/snippets'/f'{ident}.html').read_text()
                parser=Audit();parser.feed(source)
                self.assertIn('h2',parser.tags)
                self.assertTrue(parser.labelled)
                self.assertTrue(set(parser.labelled) <= parser.ids)
                self.assertNotIn('script',parser.tags)
                self.assertTrue(all(url and url.startswith('/') for url in parser.links))
        source=(ROOT/'blocks/snippets/content-collection.html').read_text()
        parsed=Audit();parsed.feed(source)
        self.assertEqual(sorted(parsed.named_inputs),['category','q'])
        self.assertIn('form',parsed.tags)
        self.assertIn('nav',parsed.tags)
        self.assertIn('time',parsed.tags)
        commerce=(ROOT/'blocks/snippets/product-collection.html').read_text()
        self.assertIn('Fictional products and prices',commerce)

    def test_documentation_sidecar_places_article_in_main_track(self):
        # Syntyr's .syn-sidecar explicitly assigns first child to the wide
        # main track and last child to the narrow optional aside.
        source = (ROOT / 'blocks/snippets/docs-layout.html').read_text()
        self.assertRegex(source, r'(?s)<div class="syn-sidecar">\s*<article>')
        self.assertRegex(source, r'(?s)</article>\s*<nav class="syn-panel"')

    def test_gallery_preserves_copy_owned_source_and_inert_form_preview(self):
        page=(ROOT/'docs/blocks.html').read_text()
        for ident in ADDITIONS:
            with self.subTest(block=ident):
                marker=f'data-block-id="{ident}"'
                self.assertEqual(page.count(marker),1)
                card=page.split(marker,1)[1].split('      </article>',1)[0]
                preview=card.split('<div class="blocks-preview">',1)[1].split('<details class="blocks-details">',1)[0]
                self.assertNotIn('href=',preview)
                self.assertIn('blocks-source',card)
        collection=page.split('data-block-id="content-collection"',1)[1].split('      </article>',1)[0]
        self.assertIn('fieldset class="blocks-preview-disabled" disabled',collection)
        self.assertIn('action=&quot;/journal&quot;',collection)
        self.assertIn('<option value="Publishing">Publishing</option>',page)
        self.assertIn('<option value="Commerce">Commerce</option>',page)

    def test_guide_counts_match_manifest_after_final_extraction(self):
        count=len(json.loads((ROOT/'blocks/manifest.json').read_text())['blocks'])
        guide=(ROOT/'docs/blocks-guide.md').read_text()
        for phrase in (f'Browse {count} blocks',f'all {count} static previews',
                       f'contains the {count} MIT',f'same {count} MIT blocks'):
            with self.subTest(phrase=phrase):self.assertIn(phrase,guide)

if __name__=='__main__':unittest.main()
