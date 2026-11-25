"""SEO contract for platform-specific, crawlable, usable setup guides."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import unittest

from scripts.build_cloudflare_site import SITE_URL, source_files

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = (
    "wordpress", "shopify", "wix", "webflow", "framer",
    "squarespace", "ghost", "hubspot", "drupal", "joomla",
    "carrd", "duda", "tilda",
)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.titles = []
        self.h1s = []
        self.meta = {}
        self.canonicals = []
        self.links = []
        self.schemas = []
        self.current = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {"title", "h1"}:
            self.current = tag
            self.parts = []
        if tag == "meta":
            self.meta[a.get("name") or a.get("property")] = a.get("content")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a.get("href"))
        if tag == "a":
            self.links.append(a.get("href", ""))
        if tag == "script" and a.get("type") == "application/ld+json":
            self.current = "schema"
            self.parts = []

    def handle_data(self, data):
        if self.current:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.current != tag and not (tag == "script" and self.current == "schema"):
            return
        content = "".join(self.parts).strip()
        if tag == "title":
            self.titles.append(content)
        elif tag == "h1":
            self.h1s.append(content)
        elif tag == "script":
            self.schemas.append(json.loads(content))
        self.current = None
        self.parts = []


class PlatformLandingSEOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = source_files()

    def test_all_platforms_have_crawlable_unique_landing_pages(self):
        seen_titles, seen_descriptions = set(), set()
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                filename = f"docs/{platform}.html"
                self.assertIn(filename, self.files)
                self.assertIn(f"docs/{platform}.md", self.files)
                page = PageParser()
                page.feed(self.files[filename].decode())
                self.assertEqual(len(page.titles), 1)
                self.assertEqual(len(page.h1s), 1)
                self.assertLessEqual(len(page.titles[0]), 67)
                self.assertIn(platform.lower(), page.titles[0].lower())
                self.assertIn(platform.lower(), page.h1s[0].lower())
                self.assertNotIn(page.titles[0], seen_titles)
                seen_titles.add(page.titles[0])
                description = page.meta.get("description", "")
                self.assertGreaterEqual(len(description), 90)
                self.assertLessEqual(len(description), 165)
                self.assertIn(platform.lower(), description.lower())
                self.assertNotIn(description, seen_descriptions)
                seen_descriptions.add(description)
                self.assertEqual(page.canonicals, [f"{SITE_URL}/docs/{platform}"])
                self.assertEqual(page.meta.get("og:url"), page.canonicals[0])
                self.assertEqual(page.meta.get("og:description"), description)
                self.assertEqual(page.meta.get("og:image"), f"{SITE_URL}/assets/og-syntyr.png")
                self.assertEqual(page.meta.get("twitter:card"), "summary_large_image")
                self.assertNotIn("noindex", page.meta.get("robots", ""))
                self.assertTrue(any(s.get("@type") == "BreadcrumbList" for s in page.schemas))
                self.assertIn("site-builders.html", page.links)
                self.assertIn("distribution.html", page.links)

    def test_platform_pages_have_real_distinct_installation_content(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                text = self.files[f"docs/{platform}.md"].decode("utf-8")
                self.assertIn("## Why use Syntyr", text)
                self.assertIn("## How to install", text)
                self.assertIn("## Limitations", text)
                self.assertIn("## Verify", text)
                self.assertIn("https://", text, "Official platform reference")
                self.assertIn("syntyr.embed.css", text)
                self.assertIn("alpha.5", text)
                self.assertIn("alpha.4", text)
                self.assertGreaterEqual(len(re.findall(r"\b[\w-]+\b", text)), 220)

    def test_joomla_guide_activates_registered_css_asset(self):
        guide = (ROOT / "docs/joomla.md").read_text(encoding="utf-8")
        self.assertIn("Web Asset Manager", guide)
        self.assertIn("joomla.asset.json", guide)
        self.assertIn("useStyle(", guide)
        self.assertIn("registerAndUseStyle", guide)

    def test_index_sitemap_and_discoverability(self):
        sitemap = self.files["sitemap.xml"].decode()
        hub = self.files["docs/site-builders.html"].decode()
        index = self.files["docs/reference.html"].decode()
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                self.assertIn(f"<loc>{SITE_URL}/docs/{platform}</loc>", sitemap)
                self.assertIn(f"{platform}.html", hub)
                self.assertIn(f"{platform}.html", index)
        self.assertNotIn(".html</loc>", sitemap)


if __name__ == "__main__":
    unittest.main()
