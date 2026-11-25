"""SEO landing page contracts for discoverable, accurate static content."""
from html.parser import HTMLParser
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit
import re
import unittest

from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://syntyr-css.pages.dev"
PAGES = (
    "faq", "compare", "compare-tailwind", "compare-bootstrap",
    "compare-shadcn", "compare-daisyui", "compare-pico", "compare-native-css",
)


class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.links = {}
        self.h1 = 0
        self.h2 = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "meta":
            key = values.get("name") or values.get("property")
            if key:
                self.meta[key] = values.get("content", "")
        if tag == "link":
            self.links[values.get("rel", "")] = values.get("href", "")
        if tag == "h1":
            self.h1 += 1
        if tag == "h2":
            self.h2 += 1


class SeoPagesTests(unittest.TestCase):
    def test_new_landing_pages_are_published_with_unique_metadata(self):
        files = source_files()
        sitemap = files["sitemap.xml"].decode("utf-8")
        descriptions = set()
        titles = set()
        for slug in PAGES:
            path = f"docs/{slug}.html"
            with self.subTest(path=path):
                self.assertIn(path, files)
                self.assertIn(f"docs/{slug}.md", files)
                self.assertIn(f"{SITE}/docs/{slug}</loc>", sitemap)
                html = files[path].decode("utf-8")
                parser = Meta()
                parser.feed(html)
                description = parser.meta["description"]
                title = unescape(re.search(r"<title>([^<]+)</title>", html).group(1))
                self.assertTrue(90 <= len(description) <= 170, slug)
                self.assertNotIn(description, descriptions)
                descriptions.add(description)
                self.assertNotIn(title, titles)
                titles.add(title)
                self.assertEqual(parser.links["canonical"], f"{SITE}/docs/{slug}")
                self.assertEqual(parser.meta["og:url"], f"{SITE}/docs/{slug}")
                self.assertEqual(parser.meta["og:title"], title)
                self.assertEqual(parser.meta["twitter:card"], "summary_large_image")
                self.assertEqual(parser.meta["og:image"], f"{SITE}/assets/og-syntyr.png")
                self.assertEqual(parser.h1, 1)
                self.assertGreaterEqual(parser.h2, 2)
                self.assertNotRegex(html.lower(), r"<script(?!\s+type=\"application/ld\+json\")")
                self.assertIn('\"@type\":\"BreadcrumbList\"', html)

    def test_homepage_has_semantic_faq_and_discovery_links(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="faq"', html)
        self.assertGreaterEqual(html.count("<details"), 6)
        self.assertIn('href="docs/faq.html"', html)
        self.assertIn('href="docs/compare.html"', html)
        self.assertIn('href="docs/compare-tailwind.html"', html)

    def test_all_comparisons_are_indexed_and_cross_linked(self):
        files = source_files()
        index = files["docs/compare.html"].decode()
        directory = files["docs/reference.html"].decode()
        for slug in PAGES[2:]:
            with self.subTest(slug=slug):
                self.assertIn(f'{slug}.html', index)
                self.assertIn(f'{slug}.html', directory)
                page = files[f"docs/{slug}.html"].decode()
                self.assertIn("compare.html", page)
                self.assertIn("faq.html", page)
                self.assertIn("distribution.html", page)
                self.assertIn("alpha.4", page)
                self.assertIn("alpha.5", page)
                self.assertRegex(page, r"https://(?:tailwindcss.com|ui.shadcn.com|daisyui.com|picocss.com|getbootstrap.com|developer.mozilla.org)/")

    def test_daisyui_comparison_documents_no_build_distribution(self):
        source = (ROOT / "docs/compare-daisyui.md").read_text(encoding="utf-8")
        html = source_files()["docs/compare-daisyui.html"].decode("utf-8")
        self.assertIn("standalone prebuilt CSS", source)
        self.assertIn("without Tailwind", source)
        self.assertIn("standalone prebuilt CSS", html)
        self.assertIn("daisyui.com/docs/v5/", source)

    def test_docs_nav_provides_faq_and_comparisons(self):
        html = (ROOT / "docs/guides.html").read_text(encoding="utf-8")
        self.assertIn('href="faq.html"', html)
        self.assertIn('href="compare.html"', html)


if __name__ == "__main__":
    unittest.main()
