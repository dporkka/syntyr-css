"""Verify Free's docs-only guided starter remains discoverable and publishable."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StarterWizardTests(unittest.TestCase):
    def test_starter_is_discoverable_and_uses_a_separate_optional_module(self):
        page = (ROOT / "docs/starter-wizard.html").read_text()
        index = (ROOT / "docs/index.html").read_text()
        self.assertIn('href="starter-wizard.html"', index)
        for label in ("Project type", "Theme", "Integration", "Generate starter"):
            self.assertIn(label, page)
        self.assertIn('id="starter-result"', page)
        self.assertIn('id="starter-copy"', page)
        self.assertIn('src="starter-wizard.mjs"', page)
        self.assertIn("Published alpha.4", page)
        self.assertNotIn("https://cdn.", page)

    def test_mobile_navigation_keeps_all_starter_destinations_available(self):
        page = (ROOT / "docs/starter-wizard.html").read_text()
        self.assertIn('class="site-mobile-menu"', page)
        self.assertIn('aria-label="Mobile navigation"', page)
        self.assertIn('<summary', page)
        for link in ('index.html', 'blocks.html', 'playground.html', 'guides.html'):
            self.assertGreaterEqual(page.count(f'href="{link}"'), 2, link)

    def test_starter_is_in_explicit_site_allowlist(self):
        from scripts.build_cloudflare_site import PUBLIC_DOCS, source_files
        self.assertIn("starter-wizard.html", PUBLIC_DOCS)
        self.assertIn("starter-wizard.mjs", PUBLIC_DOCS)
        files = source_files()
        self.assertIn("docs/starter-wizard.html", files)
        self.assertIn("docs/starter-wizard.mjs", files)


if __name__ == "__main__":
    unittest.main()
