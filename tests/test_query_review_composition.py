"""Contract for the copy-owned, server-rendered query/review composition."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/query-review.html"


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.inputs = []
        self.selects = []
        self.links = []
        self.headings = []
        self.descriptions = []
        self.scripts = []

    def handle_starttag(self, tag, raw_attrs):
        attrs = dict(raw_attrs)
        if tag == "form":
            self.forms.append(attrs)
        if tag == "input":
            self.inputs.append(attrs)
        if tag == "select":
            self.selects.append(attrs)
        if tag == "a":
            self.links.append(attrs)
        if tag in ("h1", "h2"):
            self.headings.append(attrs)
        if tag == "dl":
            self.descriptions.append(attrs)
        if tag == "script":
            self.scripts.append(attrs)


class QueryReviewComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = EXAMPLE.read_text(encoding="utf-8")
        cls.elements = Elements()
        cls.elements.feed(cls.html)

    def test_native_get_filters_and_explicit_server_contract(self):
        self.assertTrue(any(form.get("method") == "get" and
                            form.get("action") == "query-review.html"
                            for form in self.elements.forms))
        self.assertTrue(any(inp.get("name") == "query" and
                            inp.get("type") == "search"
                            for inp in self.elements.inputs))
        self.assertTrue({"status", "owner"}.issubset(
            {select.get("name") for select in self.elements.selects}))
        self.assertIn("syn-filter-bar", self.html)
        self.assertIn("server-rendered", self.html)
        self.assertFalse(self.elements.scripts)

    def test_removing_one_filter_preserves_other_filter_values(self):
        removals = {
            a["aria-label"]: a["href"] for a in self.elements.links
            if a.get("aria-label", "").startswith("Remove ")
        }
        self.assertEqual(set(removals), {
            "Remove status filter: Active",
            "Remove owner filter: Me",
        })
        status_url = urlsplit(removals["Remove status filter: Active"])
        owner_url = urlsplit(removals["Remove owner filter: Me"])
        self.assertEqual(status_url.path, "")
        self.assertEqual(owner_url.path, "")
        self.assertEqual(parse_qs(status_url.query), {
            "query": ["Central"], "owner": ["me"],
        })
        self.assertEqual(parse_qs(owner_url.query), {
            "query": ["Central"], "status": ["active"],
        })

    def test_review_uses_native_descriptions_and_real_edit_links(self):
        self.assertTrue(any("syn-record-fields" in d.get("class", "")
                            for d in self.elements.descriptions))
        self.assertIn("<dt>Inventory ID</dt>", self.html)
        self.assertIn("<dt>Status</dt>", self.html)
        self.assertIn("<dt>Owner</dt>", self.html)
        self.assertTrue(any(a.get("href", "").startswith("#edit-")
                            for a in self.elements.links))
        self.assertIn("syn-chip", self.html)
        self.assertIn("syn-filter-choices", self.html)
        self.assertIn('id="edit-status"', self.html)
        self.assertIn('id="edit-owner"', self.html)
        self.assertIn("<fieldset disabled>", self.html)
        self.assertIn('<details class="syn-details" open>', self.html)

    def test_no_missing_public_site_routes(self):
        for a in self.elements.links:
            self.assertFalse(a.get("href", "").startswith("/inventory"),
                             "static demo links must not point to unimplemented routes")

    def test_offline_recipe_guide_link_resolves_in_release_zip(self):
        from posixpath import normpath
        from scripts.package_release import FILES

        guidance = [link for link in self.elements.links
                    if "recipe" in link.get("href", "") and
                    link.get("href", "").startswith("../docs/")]
        self.assertEqual(len(guidance), 1)
        relative_target = normpath("examples/" + guidance[0]["href"])
        self.assertIn(relative_target, FILES)
        self.assertTrue((ROOT / relative_target).is_file())

    def test_documented_entry_point(self):
        docs = (ROOT / "docs/recipes.md").read_text(encoding="utf-8")
        self.assertIn("examples/query-review.html", docs)
        self.assertIn("does not filter", docs)


if __name__ == "__main__":
    unittest.main()
