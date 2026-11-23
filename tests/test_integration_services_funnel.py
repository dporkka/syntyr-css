"""A quote-based integration path must be real, reachable and not pretend kits are on sale."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import unittest

from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.append(dict(attrs).get("href", ""))


class IntegrationServicesFunnelTests(unittest.TestCase):
    def test_service_offer_is_accessible_and_quote_based(self):
        page = (ROOT / "docs/integration-services.html").read_text(encoding="utf-8")
        self.assertIn('<main id="main">', page)
        self.assertIn('href="#main"', page)
        self.assertIn('id="services-title"', page)
        self.assertIn('https://syntyr-css.pages.dev/docs/integration-services.html', page)
        for phrase in ("HTML", "CSS", "Syntyr Core", "quote", "not a hosted", "privacy",
                       "authentication", "acceptance"):
            self.assertIn(phrase.lower(), page.lower())
        self.assertNotIn('href="/checkout"', page)
        self.assertNotIn("<form", page.lower())
        self.assertNotIn("<script", page.lower())
        links = Links()
        links.feed(page)
        inquiries = [urlsplit(link) for link in links.hrefs if link.startswith("mailto:")]
        self.assertTrue(inquiries, "Service inquiry needs a real private contact route")
        self.assertTrue(any(link.path == "davidporkka@gmail.com" and
                            "Syntyr" in parse_qs(link.query).get("subject", [""])[0]
                            for link in inquiries))
        self.assertIn('href="distribution.html"', page)
        self.assertIn('href="products.html"', page)
        self.assertIn('class="site-mobile-menu"', page)
        self.assertIn('aria-label="Mobile services navigation"', page)

    def test_services_have_contextual_discovery_links(self):
        for page_name, expected in (
            ("docs/products.html", 'href="integration-services.html"'),
            ("docs/pro.html", 'href="integration-services.html"'),
            ("docs/studio.html", 'href="integration-services.html"'),
            ("index.html", 'href="docs/integration-services.html"'),
        ):
            with self.subTest(page=page_name):
                self.assertIn(expected, (ROOT / page_name).read_text(encoding="utf-8"))

    def test_public_build_exposes_service_page_not_private_source(self):
        files = source_files()
        name = "docs/integration-services.html"
        self.assertIn(name, files)
        self.assertIn(b"QUOTE-BASED", files[name].upper())
        self.assertNotIn("business/commercial-launch-gates.md", files)
        self.assertNotIn("business/premium-license-draft.md", files)
        self.assertFalse(any(path.startswith("products/") or path.endswith(".zip")
                             and "premium" in path for path in files))


if __name__ == "__main__":
    unittest.main()
