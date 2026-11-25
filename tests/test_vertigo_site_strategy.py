"""Tests for an opt-in Vertigo skin and an isolated Hugo docs preview."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DemoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.stylesheets = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.stylesheets.append(attributes["href"])


class OptInWebsiteContractTests(unittest.TestCase):
    def test_vertigo_admin_skin_is_opt_in_and_local(self):
        skin = (ROOT / "integrations/vertigo/admin.css").read_text()
        for selector in (".syn-vertigo-admin", ".cards", ".card",
                         ".row", ".tablewrap", ".notice", ".field-error",
                         ".button"):
            self.assertIn(selector, skin)
        self.assertNotIn("@import", skin)
        self.assertNotIn("http://", skin)
        self.assertNotIn("https://", skin)
        self.assertIn("forced-colors: active", skin)

    def test_vertigo_demo_matches_native_admin_structure(self):
        demo = (ROOT / "examples/vertigo-admin.html").read_text()
        parser = DemoParser()
        parser.feed(demo)
        self.assertEqual(parser.stylesheets, [
            "../dist/syntyr.core.css", "../integrations/vertigo/admin.css"
        ])
        self.assertIn('class="syn-root syn-page syn-vertigo-admin"', demo)
        self.assertIn('data-syn-theme="studio"', demo)
        for tag in ("main", "nav", "table", "form", "label", "input", "button"):
            self.assertIn(tag, [name for name, _ in parser.tags])
        self.assertIn('scope="col"', demo)
        self.assertIn("Fictional", demo)
        self.assertNotIn("<script", demo.lower())

    def test_hugo_proof_of_concept_keeps_source_site_untouched(self):
        root = ROOT / "experiments/hugo"
        config = (root / "hugo.toml").read_text()
        self.assertIn("content/guide", config)
        self.assertIn("../../docs", config)
        self.assertIn("../../dist", config)
        self.assertIn("../../examples", config)
        self.assertIn("0.170.0", (root / "README.md").read_text())
        self.assertTrue((root / "layouts/baseof.html").exists())
        self.assertTrue((root / "layouts/page.html").exists())
        self.assertTrue((root / "layouts/home.html").exists())
        self.assertTrue((root / "layouts/_markup/render-link.html").exists())
        self.assertTrue((ROOT / "index.html").exists())
        self.assertTrue((ROOT / "docs/index.html").exists())
        self.assertTrue((ROOT / "scripts/verify_hugo_preview.py").exists())

    def test_component_gallery_links_to_vertigo_preview(self):
        page = (ROOT / "docs/index.html").read_text()
        self.assertIn('href="../examples/vertigo-admin.html"', page)

    def test_agent_index_discloses_vertigo_integration_evidence_boundary(self):
        index = (ROOT / "llms.txt").read_text()
        self.assertIn("https://syntyr-css.pages.dev/docs/vertigo-integration.md", index)
        self.assertIn("private", index.lower())
        self.assertIn("static public", index.lower())

    def test_docs_set_realistic_migration_threshold(self):
        strategy = (ROOT / "docs/site-generator-decision.md").read_text()
        for fragment in ("Hugo", "Zola", "GitHub Pages", "Vertigo",
                         "no migration", "manual", "Markdown"):
            self.assertIn(fragment.lower(), strategy.lower())
        integration = (ROOT / "docs/vertigo-integration.md").read_text()
        self.assertIn("pageShell", integration)
        self.assertIn("syn-vertigo-admin", integration)
        self.assertIn("MIT", integration)
        self.assertIn("do not", integration.lower())


if __name__ == "__main__":
    unittest.main()
