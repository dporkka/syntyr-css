"""Semantic HTML additions must remain opt-in, script-free, and published."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.elements.append(tag)
        self.attrs.append((tag, dict(attrs)))


class SemanticCompositions(unittest.TestCase):
    def test_new_selectors_preserve_semantic_scope_and_native_markup(self):
        css = (ROOT / 'src/semantic.css').read_text()
        for tag in ('tfoot',):
            with self.subTest(tag=tag):
                self.assertIn(f'{tag}:not([class])', css)
                self.assertIn(f'{tag}[data-syn-semantic]', css)
        self.assertIn('blockquote:not([class]) > footer:not([class])', css)
        # Ruby annotation layout and typography remain browser-owned.
        self.assertNotIn('ruby:not([class])', css)
        self.assertNotIn('rt:not([class])', css)
        self.assertIn(':is(.syn-root.syn-semantic, .syn-root .syn-semantic)', css)
        self.assertNotIn('appearance: none', css)
        self.assertNotIn('@import', css)

    def test_live_gallery_demonstrates_semantic_compositions(self):
        html = (ROOT / 'examples/semantic-compositions.html').read_text()
        parser = Markup()
        parser.feed(html)
        required = ('main', 'article', 'header', 'footer', 'time', 'nav', 'ol',
                    'dl', 'dt', 'dd', 'data', 'figure', 'blockquote', 'figcaption',
                    'cite', 'ins', 'del', 'ruby', 'rt', 'rp', 'bdi', 'bdo',
                    'table', 'caption', 'thead', 'tbody', 'tfoot', 'th', 'td', 'aside')
        for tag in required:
            with self.subTest(tag=tag):
                self.assertIn(tag, parser.elements)
        self.assertNotIn('script', parser.elements)
        self.assertIn('syn-root syn-page syn-semantic', html)
        self.assertIn('syntyr.semantic.css', html)
        self.assertIn('syntyr.core.css', html)
        self.assertIn('aria-label="Breadcrumb"', html)
        self.assertIn('scope="col"', html)
        self.assertIn('scope="row"', html)
        self.assertIn('datetime=', html)
        self.assertIn('dir="rtl"', html)

    def test_docs_include_copyable_html_and_browser_ownership_notes(self):
        docs = (ROOT / 'docs/semantic-components.md').read_text()
        self.assertGreaterEqual(docs.count('~~~html'), 5)
        for word in ('ruby', 'rt', 'tfoot', 'bdi', 'cite', 'blockquote', 'datetime', 'syn-semantic'):
            self.assertIn(word, docs)
        self.assertIn('no JavaScript', docs)
        self.assertIn('server', docs.lower())

    def test_website_links_and_allowlist_publish_pages(self):
        from scripts.build_cloudflare_site import source_files
        paths = source_files()
        self.assertIn('examples/semantic-compositions.html', paths)
        self.assertIn('docs/semantic-components.md', paths)
        self.assertIn('docs/semantic-components.html', paths)
        self.assertIn('href="../examples/semantic-compositions.html"', (ROOT / 'docs/index.html').read_text())
        self.assertIn('href="docs/semantic-components.html"', (ROOT / 'index.html').read_text())
        self.assertIn('semantic-components.html', (ROOT / 'docs/reference.html').read_text())


if __name__ == '__main__':
    unittest.main()
