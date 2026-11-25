"""Contracts for CSS-only enterprise collection, record sheet, and evidence recipes."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "examples/enterprise-compositions.html"


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.tags.append((tag, data))
        if data.get("id"):
            self.ids.add(data["id"])

    def matching(self, tag=None, css_class=None):
        return [
            a for t, a in self.tags
            if (tag is None or t == tag)
            and (css_class is None or css_class in a.get("class", "").split())
        ]


class EnterpriseCompositions(unittest.TestCase):
    def setUp(self):
        self.css = (ROOT / "src/recipes.css").read_text()
        self.html = PAGE.read_text()
        self.page = Elements()
        self.page.feed(self.html)

    def test_view_switcher_has_real_navigation_with_current_view(self):
        self.assertIn("&.syn-view-switcher", self.css)
        self.assertIn('[aria-current="page"]', self.css)
        navs = self.page.matching("nav", "syn-view-switcher")
        self.assertEqual(len(navs), 1)
        self.assertTrue(navs[0].get("aria-label"))
        anchors = self.page.matching("a", "syn-view-link")
        self.assertGreaterEqual(len(anchors), 2)
        self.assertEqual(sum(a.get("aria-current") == "page" for a in anchors), 1)
        self.assertTrue(all(a.get("href", "").startswith("?view=") for a in anchors))

    def test_native_sheet_is_progressively_enhanced_and_not_fake_modal(self):
        self.assertIn("&.syn-sheet", self.css)
        self.assertIn(":popover-open", self.css)
        self.assertIn("dialog[open]", self.css)
        self.assertIn("not(:popover-open)", self.css)
        self.assertIn("syn-sheet-body", self.css)
        sheets = self.page.matching(css_class="syn-sheet")
        self.assertEqual(len(sheets), 1)
        self.assertIn("popover", sheets[0])
        self.assertIn(sheets[0]["id"], self.page.ids)
        openers = [a for a in self.page.matching("button") if a.get("popovertarget") == sheets[0]["id"] and a.get("popovertargetaction", "show") == "show"]
        self.assertEqual(len(openers), 1)
        self.assertEqual(openers[0].get("type"), "button")
        self.assertFalse(any(a.get("aria-modal") == "true" for a in sheets))
        self.assertTrue(any(a.get("popovertargetaction") == "hide" for a in self.page.matching("button")))
        self.assertIn('href="#records"', self.html, "No-JS fallback must navigate to the record collection")

    def test_evidence_cards_use_real_figures_and_metadata(self):
        self.assertIn("&.syn-evidence-grid", self.css)
        self.assertIn("&.syn-evidence-card", self.css)
        self.assertIn("&.syn-evidence-media--placeholder", self.css)
        self.assertIn("&.syn-evidence-meta", self.css)
        self.assertGreaterEqual(len(self.page.matching("figure", "syn-evidence-card")), 2)
        self.assertGreaterEqual(len(self.page.matching("figcaption")), 2)
        self.assertGreaterEqual(len(self.page.matching("dl", "syn-evidence-meta")), 2)
        self.assertTrue(self.page.matching("time"))
        self.assertIn("Illustrative", self.html)

    def test_stays_opt_in_scoped_without_a_runtime(self):
        self.assertEqual(self.page.matching("script"), [])
        self.assertEqual(len(self.page.matching("main")), 1)
        self.assertTrue(self.page.matching(css_class="syn-root"))
        self.assertIn('href="../dist/syntyr.core.css"', self.html)
        self.assertIn('href="../dist/syntyr.recipes.css"', self.html)
        self.assertIn(":where(.syn-root, .syn-root *)", self.css)
        self.assertNotIn(".syn-view-switcher", (ROOT / "src/components/patterns.css").read_text())
        self.assertNotIn(".syn-sheet", (ROOT / "src/components/overlays.css").read_text())
        self.assertIn("@media (forced-colors: active)", self.css)
        self.assertIn("max-inline-size: 100%", self.css)

    def test_editor_metadata_describes_host_owned_behavior_and_sheet_width(self):
        import json
        api = json.loads((ROOT / "metadata/syntyr-api.json").read_text())
        classes = {entry["name"]: entry["description"] for entry in api["classes"]}
        self.assertIn("server", classes["syn-view-switcher"].lower())
        self.assertIn("popover", classes["syn-sheet"].lower())
        self.assertIn("presentation", classes["syn-evidence-card"].lower())
        tokens = {entry["name"]: entry["description"] for entry in api["tokens"]}
        self.assertIn("--syn-sheet-width", tokens)
        self.assertIn("width", tokens["--syn-sheet-width"].lower())

    def test_documented_and_available_in_public_gallery(self):
        self.assertIn("syn-view-switcher", (ROOT / "docs/recipes.md").read_text())
        self.assertIn("syn-evidence-grid", (ROOT / "docs/recipes.md").read_text())
        self.assertIn("enterprise-compositions.html", (ROOT / "README.md").read_text())
        self.assertIn("enterprise-compositions.html", (ROOT / "docs/index.html").read_text())
        self.assertIn("enterprise-compositions.html", (ROOT / "scripts/build_cloudflare_site.py").read_text())
        for script in ("browser_matrix.py", "axe_audit.py", "reflow_test.py"):
            self.assertIn("examples/enterprise-compositions.html", (ROOT / "tests" / script).read_text())


if __name__ == "__main__":
    unittest.main()
