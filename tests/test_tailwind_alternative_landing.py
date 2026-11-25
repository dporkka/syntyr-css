"""Contract for the public, decision-oriented Tailwind alternative page."""
from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from scripts.build_cloudflare_site import SITE_URL, source_files


ROOT = Path(__file__).resolve().parents[1]
PAGE = "docs/tailwind-alternative.html"


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []
        self.h1 = 0
        self.scripts = 0
        self.tables = 0
        self.headers: list[str] = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "a" and "href" in data:
            self.hrefs.append(data["href"])
        if tag == "h1":
            self.h1 += 1
        if tag == "script":
            self.scripts += 1
        if tag == "table":
            self.tables += 1
        if tag == "th":
            self.headers.append(data.get("scope", ""))


class TailwindAlternativeLandingTests(unittest.TestCase):
    def test_public_indexable_landing_page_is_allowlisted(self):
        files = source_files()
        self.assertTrue(PAGE in files, PAGE)
        html = files[PAGE].decode()
        self.assertIn(f'<link rel="canonical" href="{SITE_URL}/docs/tailwind-alternative">', html)
        self.assertNotIn('name="robots" content="noindex', html)
        xml = ElementTree.fromstring(files["sitemap.xml"])
        urls = {node.text for node in xml.findall("{*}url/{*}loc")}
        self.assertIn(f"{SITE_URL}/docs/tailwind-alternative", urls)

    def test_comparison_is_accessible_and_balanced(self):
        html = (ROOT / PAGE).read_text()
        dom = PageLinks()
        dom.feed(html)
        self.assertEqual(dom.h1, 1)
        self.assertEqual(dom.scripts, 0)
        self.assertGreaterEqual(dom.tables, 1)
        self.assertIn("col", dom.headers)
        self.assertIn("Tailwind", html)
        self.assertIn("plain CSS", html)
        self.assertIn("When Tailwind is a better choice", html)
        self.assertIn("When plain CSS is enough", html)
        self.assertIn("unreleased alpha.5", html)
        self.assertIn("no runtime JavaScript", html)
        self.assertIn("https://github.com/dporkka/syntyr-css/issues/3", html)

    def test_relevant_free_demos_and_readiness_are_linked(self):
        html = (ROOT / PAGE).read_text()
        dom = PageLinks()
        dom.feed(html)
        for href in (
            "../examples/operations-console.html",
            "../examples/semantic-starter.html",
            "../examples/saas-workflows.html",
            "distribution.html",
            "framework-integrations.html",
            "tailwind-research.html",
            "products.html",
        ):
            self.assertIn(href, dom.hrefs)
            self.assertTrue((ROOT / "docs" / href).is_file(), href)

    def test_agent_index_discovers_comparison(self):
        index = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("https://syntyr-css.pages.dev/docs/tailwind-alternative.html", index)

    def test_marketing_surfaces_link_to_comparison(self):
        self.assertIn('href="docs/tailwind-alternative.html"', (ROOT / "index.html").read_text())
        self.assertIn('href="tailwind-alternative.html"', (ROOT / "docs/guides.html").read_text())


if __name__ == "__main__":
    unittest.main()
