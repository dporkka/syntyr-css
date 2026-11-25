"""Commercial research must offer useful private, tier-specific non-sale pathways."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.anchors.append(dict(attrs))


class ProStudioConversionTests(unittest.TestCase):
    def setUp(self):
        self.products = (ROOT / "docs/products.html").read_text(encoding="utf-8")
        self.home = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_pro_and_studio_have_distinct_private_research_inquiries(self):
        parser = Anchors()
        parser.feed(self.products)
        links = {a.get("data-research-tier"): a for a in parser.anchors if a.get("data-research-tier")}
        self.assertIn("pro", links)
        self.assertIn("studio", links)
        self.assertNotEqual(links["pro"]["href"], links["studio"]["href"])
        for tier in ("pro", "studio"):
            with self.subTest(tier=tier):
                url = urlsplit(links[tier]["href"])
                self.assertEqual(url.scheme, "mailto")
                self.assertTrue(url.path)
                subject = parse_qs(url.query).get("subject", [""])[0]
                body = parse_qs(url.query).get("body", [""])[0]
                self.assertIn("Syntyr " + tier.title(), subject)
                for prompt in ("Stack:", "Current project:", "Most valuable pages:", "Biggest blocker:"):
                    self.assertIn(prompt, body)
        self.assertIn("opens your email app", self.products.lower())
        self.assertIn("does not send any information to this site", self.products.lower())
        self.assertIn("GitHub issue is public", self.products)

    def test_tier_chooser_uses_jobs_not_just_component_counts(self):
        self.assertIn('id="which-premium"', self.products)
        self.assertIn("Choose Pro for", self.products)
        self.assertIn("Choose Studio for", self.products)
        self.assertIn("application", self.products.lower())
        self.assertIn("website", self.products.lower())
        self.assertIn("Studio theme is free", self.products)
        self.assertIn('href="#which-premium"', self.products)

    def test_homepage_reaches_pro_and_studio_research_without_checkout(self):
        self.assertIn('href="docs/products.html#which-premium"', self.home)
        self.assertIn('href="docs/products.html"', self.home)
        self.assertIn('href="docs/console-kit.html"', self.home)
        self.assertNotIn("BUY PRO", self.home)
        self.assertNotIn("BUY STUDIO", self.home)
        self.assertNotIn('href="/checkout"', self.products)


if __name__ == "__main__":
    unittest.main()
