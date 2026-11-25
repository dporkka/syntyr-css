"""Buyer-facing Premium discovery must be clear without enabling a store."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class PremiumBuyerJourneyTests(unittest.TestCase):
    def test_feature_comparison_is_accessible_and_honest(self):
        page = (ROOT / "docs/products.html").read_text()
        self.assertIn('id="offer-feature-matrix"', page)
        self.assertIn('<caption>', page)
        self.assertIn('scope="col"', page)
        self.assertIn('scope="row"', page)
        self.assertIn('aria-label="Compare Premium features"', page)
        self.assertIn('Not for sale', page)
        self.assertIn('Server-rendered resource workflow', page)
        self.assertIn('Reference only', page)
        self.assertIn("Pricing is proposed", page)
        self.assertNotIn('href="/checkout"', page)

    def test_theme_previews_are_selectable_without_javascript(self):
        page = (ROOT / "docs/console-kit.html").read_text()
        for theme in ("studio", "grid", "noir"):
            self.assertIn(f'id="kit-theme-{theme}"', page)
        self.assertIn('class="kit-theme-group"', page)
        self.assertIn('<summary>', page)
        self.assertIn('aria-label="Preview themes"', page)
        self.assertNotIn('<script', page.lower())
        scan = Scan()
        scan.feed(page)
        images = [attrs for tag, attrs in scan.tags if tag == "img" and attrs.get("src", "").startswith("previews/")]
        self.assertEqual(len(images), 8)
        self.assertEqual(len(set(img["src"] for img in images)), 8)
        self.assertEqual(sum(tag == "details" and attrs.get("class") == "kit-theme-group" for tag, attrs in scan.tags), 3)

    def test_reference_app_is_distinguished_from_paid_runtime(self):
        page = (ROOT / "docs/products.html").read_text()
        self.assertIn("local-only Go", page)
        self.assertIn("no authentication", page.lower())
        self.assertIn("not hosted", page.lower())


if __name__ == "__main__":
    unittest.main()
