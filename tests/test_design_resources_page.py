"""Contract for a maintained, publishable, accessible Syntyr design directory."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import re
import tempfile
import xml.etree.ElementTree as ET
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resource_count = 0
        self.resource_links = []
        self.ids = set()
        self.category_links = []
        self.in_resource = False
        self.cards = []
        self.descriptions = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "article" and "data-resource" in attrs:
            self.resource_count += 1
            self.in_resource = True
            self.cards.append({"links": [], "descriptions": 0})
        if tag == "a" and attrs.get("class") == "resource-category-link":
            self.category_links.append(attrs.get("href", ""))
        if tag == "a" and self.in_resource and attrs.get("href"):
            self.resource_links.append(attrs["href"])
            self.cards[-1]["links"].append(attrs["href"])
        if tag == "p" and self.in_resource and attrs.get("class") == "resource-description":
            self.descriptions += 1
            self.cards[-1]["descriptions"] += 1

    def handle_endtag(self, tag):
        if tag == "article":
            self.in_resource = False


class DesignResourcePageTests(unittest.TestCase):
    def test_directory_is_curated_and_navigable_without_scripts(self):
        page = ROOT / "docs/design-resources.html"
        html = page.read_text(encoding="utf-8")
        parser = ResourceParser()
        parser.feed(html)
        self.assertGreaterEqual(parser.resource_count, 50)
        self.assertEqual(parser.resource_count, parser.descriptions)
        self.assertEqual(parser.resource_count, len(parser.resource_links))
        self.assertTrue(all(card["descriptions"] == 1 and len(card["links"]) == 1 for card in parser.cards))
        priorities = re.findall(r'<li class="resource-priority">.*?</li>', html, re.DOTALL)
        self.assertEqual(len(priorities), 8)
        for block in priorities:
            reference_urls = re.findall(r'<a href="([^"]+)"', block)
            self.assertEqual(len(reference_urls), 2)
            self.assertTrue(all(urlsplit(url).scheme == "https" and urlsplit(url).hostname for url in reference_urls))
        self.assertEqual(len(set(parser.resource_links)), len(parser.resource_links))
        self.assertGreaterEqual(len(parser.category_links), 8)
        self.assertTrue(all(link.startswith("#") and link[1:] in parser.ids for link in parser.category_links))
        self.assertTrue(all(urlsplit(url).scheme == "https" for url in parser.resource_links))
        self.assertIn('<main id="main"', html)
        self.assertIn('href="#main"', html)
        self.assertNotIn('<script', html.lower())
        self.assertIn('prefers-reduced-motion', html)

    def test_directory_is_built_indexable_and_linked_from_home(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "public"
            result = subprocess.run(
                [sys.executable, "scripts/build_cloudflare_site.py", "--output", str(out)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            page = out / "docs/design-resources.html"
            self.assertTrue(page.is_file())
            self.assertIn('href="docs/design-resources.html"', (out / "index.html").read_text())
            tree = ET.parse(out / "sitemap.xml")
            locations = [node.text for node in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
            self.assertIn("https://syntyr-css.pages.dev/docs/design-resources", locations)
            self.assertNotIn("https://syntyr-css.pages.dev/docs/design-resources.html", locations)
            self.assertIn('rel="canonical" href="https://syntyr-css.pages.dev/docs/design-resources"', page.read_text())


if __name__ == "__main__":
    unittest.main()
