"""Homepage conversion and public-release onboarding contracts."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
PINNED_VERSION = "0.3.0-alpha.4"
PINNED_CSS = f"https://syntyr-css.pages.dev/v/{PINNED_VERSION}/syntyr.core.css"


class HomeAttributes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class SiteOnboardingTests(unittest.TestCase):
    def setUp(self):
        self.markup = HOME.read_text(encoding="utf-8")
        parser = HomeAttributes()
        parser.feed(self.markup)
        self.elements = parser.elements

    def test_primary_ctas_reach_in_page_quickstart(self):
        self.assertTrue(any(attrs.get("id") == "quickstart"
                            for _, attrs in self.elements))
        self.assertGreaterEqual(sum(
            tag == "a" and attrs.get("href") == "#quickstart"
            for tag, attrs in self.elements
        ), 3)
        self.assertIn("docs/#install", self.markup)

    def test_install_example_references_downloadable_frozen_release(self):
        self.assertIn(PINNED_CSS, self.markup)
        self.assertIn("curl -fsSLo syntyr.core.css", self.markup)
        self.assertIn('&lt;link rel="stylesheet" href="./syntyr.core.css"&gt;',
                      self.markup)
        self.assertIn('class="syn-root" data-syn-theme="studio"', self.markup)
        self.assertTrue((ROOT / "site-releases" / PINNED_VERSION /
                         "syntyr.core.css").is_file())

    def test_alpha4_and_alpha5_status_is_explicit_at_installation(self):
        quickstart = self.markup.split('id="quickstart"', 1)[1].split("</section>", 1)[0]
        self.assertIn("alpha.4", quickstart)
        self.assertIn("alpha.5", quickstart)
        self.assertIn("unreleased", quickstart.lower())
        self.assertIn("self-host", quickstart.lower())

    def test_hero_discloses_published_version_before_primary_cta(self):
        hero = self.markup.split('<section class="site-hero"', 1)[1]
        above_cta = hero.split('<div class="syn-actions">', 1)[0]
        self.assertIn("alpha.4", above_cta)
        self.assertIn("alpha.5", above_cta)
        self.assertIn("unreleased", above_cta.lower())
        self.assertIn(PINNED_CSS, above_cta)
        self.assertNotIn("/dist/syntyr.", above_cta)

    def test_homepage_has_unambiguous_canonical_social_url(self):
        self.assertTrue(any(tag == "link" and attrs.get("rel") == "canonical"
                            and attrs.get("href") == "https://syntyr-css.pages.dev/"
                            for tag, attrs in self.elements))
        self.assertTrue(any(tag == "meta" and attrs.get("property") == "og:url"
                            and attrs.get("content") == "https://syntyr-css.pages.dev/"
                            for tag, attrs in self.elements))


if __name__ == "__main__":
    unittest.main()
