"""Humans get canonical HTML guides; AI clients keep the public Markdown sources."""
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

from scripts.build_cloudflare_site import SITE_URL, canonical_path, source_files

ROOT = Path(__file__).resolve().parents[1]


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))


class DocumentationDeliveryTests(unittest.TestCase):
    def test_every_public_markdown_guide_has_a_human_html_counterpart(self):
        files = source_files()
        guides = sorted(name for name in files if name.startswith('docs/') and name.endswith('.md'))
        self.assertGreater(len(guides), 30)
        directory = files['docs/reference.html'].decode()
        for guide in guides:
            html = guide.removesuffix('.md') + '.html'
            self.assertIn(html, files, guide)
            page = files[html].decode()
            self.assertIn('<html lang="en">', page)
            self.assertIn('<main id="doc-main"', page)
            self.assertIn('<h1', page)
            self.assertIn(f'href="{Path(guide).name}"', page)
            self.assertIn(f'href="{SITE_URL}{canonical_path(html)}"', page)
            self.assertIn(f'href="{Path(html).name}"', directory)
            digest = hashlib.sha256(files[guide]).hexdigest()
            self.assertIn(f'content="{digest}"', page, html)
            self.assertEqual(
                re.findall(r'<script\b[^>]*>', page, re.I),
                ['<script type="application/ld+json">'],
                "Only non-executable JSON-LD metadata may be embedded in docs"
            )

    def test_release_readiness_summary_is_public_and_discoverable(self):
        files = source_files()
        self.assertIn('docs/launch-status.md', files)
        self.assertIn('docs/launch-status.html', files)
        self.assertIn(b'href="launch-status.html"', files['docs/reference.html'])
        page = files['docs/launch-status.html']
        self.assertIn(b'Published GitHub prerelease</a> with an immutable CDN snapshot', page)
        self.assertIn(b'https://syntyr-css.pages.dev/docs/launch-status.md', files['llms.txt'])

    def test_framework_compatibility_matrix_keeps_evidence_boundaries_public(self):
        files = source_files()
        page = files["docs/framework-integrations.html"].decode()
        self.assertIn('id="compatibility-matrix-and-evidence"', page)
        self.assertIn("45c86cf58bd0fb1decaaf391ba4dba69b00cefc8", page)
        self.assertIn("Blocked: browser launch failed; zero cases executed", page)
        self.assertIn("No framework or browser support floor has", page)
        self.assertIn("no native component compatibility claim", page)
        self.assertIn("framework-integrations.md", files["llms.txt"].decode())
        self.assertIn("Version-aware compatibility matrix", files["llms.txt"].decode())

    def test_markdown_table_code_and_links_are_real_html(self):
        files = source_files()
        page = files['docs/components.html'].decode()
        self.assertIn('<table>', page)
        self.assertIn('<pre tabindex="0"><code', page)
        self.assertIn('href="visual-intensity.html"', page)
        self.assertNotIn('href="visual-intensity.md"', page)
        self.assertIn('id="loading-and-scoping"', page)
        self.assertIn('&lt;button', page)

    def test_human_navigation_targets_html_and_agent_sources_are_preserved(self):
        files = source_files()
        for name in ('docs/index.html', 'docs/guides.html', 'docs/reference.html'):
            self.assertIn(name, files)
            links = Anchors()
            links.feed(files[name].decode())
            self.assertFalse([url for url in links.links if re.search(r'\.md(?:$|[#?])', url)], name)
        self.assertIn(b'href="reference.html"', files['docs/guides.html'])
        self.assertIn(b'href="reference.html"', files['docs/index.html'])
        self.assertIn(b'docs/ai-quickstart.md', files['llms.txt'])
        self.assertIn('docs/ai-quickstart.md', files)
        self.assertIn('llms-full.txt', files)

    def test_indexing_and_content_discovery_favor_html_without_blocking_agents(self):
        files = source_files()
        headers = files['_headers'].decode()
        self.assertIn('/docs/*.md\n  X-Robots-Tag: noindex', headers)
        self.assertIn('/README.md\n  X-Robots-Tag: noindex', headers)
        # These paths must not match duplicate Content-Type rules.
        self.assertNotIn("\n/*.md\n", headers)
        self.assertIn('Sitemap: https://syntyr-css.pages.dev/sitemap.xml', files['robots.txt'].decode())
        sitemap = files['sitemap.xml'].decode()
        self.assertIn('https://syntyr-css.pages.dev/docs/components', sitemap)
        self.assertNotIn('https://syntyr-css.pages.dev/docs/components.md', sitemap)
        self.assertIn('https://syntyr-css.pages.dev/docs/reference', sitemap)


if __name__ == '__main__':
    unittest.main()
