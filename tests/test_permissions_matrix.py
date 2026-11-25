"""A11y and distribution contracts for the copy-owned role/permission example."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MatrixHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.labels = set()
        self.roles = []
        self.row_headers = 0
        self.checkboxes = []
        self.forms = 0
        self.scripts = 0
        self.captions = 0
        self.regions = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            assert attrs["id"] not in self.ids, f"duplicate id: {attrs['id']}"
            self.ids.add(attrs["id"])
        if tag == "label" and attrs.get("for"):
            self.labels.add(attrs["for"])
        if tag == "th" and attrs.get("data-role"):
            self.roles.append(attrs["data-role"])
            assert attrs.get("scope") == "col"
        if tag == "th" and attrs.get("data-capability"):
            self.row_headers += 1
            assert attrs.get("scope") == "row"
        if tag == "input" and attrs.get("type") == "checkbox":
            self.checkboxes.append(attrs)
        if tag == "form":
            self.forms += 1
        if tag == "script":
            self.scripts += 1
        if tag == "caption":
            self.captions += 1
        if attrs.get("role") == "region":
            self.regions += 1


class PermissionMatrixContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "examples/permission-matrix.html").read_text()
        cls.css = (ROOT / "examples/permission-matrix.css").read_text()
        cls.parser = MatrixHTML()
        cls.parser.feed(cls.page)

    def test_native_accessible_matrix(self):
        m = self.parser
        self.assertEqual(m.roles, ["Viewer", "Editor", "Administrator"])
        self.assertGreaterEqual(m.row_headers, 6)
        self.assertEqual(len(m.checkboxes), m.row_headers * len(m.roles))
        self.assertEqual(len({c["id"] for c in m.checkboxes}), len(m.checkboxes))
        self.assertTrue({c["id"] for c in m.checkboxes} <= m.labels)
        self.assertEqual(m.captions, 1)
        self.assertEqual(m.regions, 1)
        self.assertIn('tabindex="0"', self.page)

    def test_demo_cannot_claim_or_submit_authorization(self):
        self.assertEqual(self.parser.scripts, 0)
        self.assertEqual(self.parser.forms, 0)
        self.assertIn("not saved", self.page.lower())
        self.assertIn("server", self.page.lower())
        self.assertIn("authentication", self.page.lower())
        self.assertTrue(all("disabled" in c and "checked" in c
                            for c in self.parser.checkboxes if c["name"].startswith("admin.")))
        self.assertTrue(any("checked" not in c for c in self.parser.checkboxes
                            if c["name"].startswith("viewer.")))

    def test_local_styles_and_no_distribution_changes(self):
        self.assertIn('href="../dist/syntyr.core.css"', self.page)
        self.assertIn('href="../dist/syntyr.recipes.css"', self.page)
        self.assertIn('href="permission-matrix.css"', self.page)
        self.assertNotIn("@import", self.css)
        self.assertNotIn("!important", self.css)
        self.assertIn("overflow", self.css)
        # Screen-reader-only text must be positioned relative to each label,
        # otherwise it can leak page-level horizontal scroll outside the grid.
        self.assertRegex(self.css, r"\.matrix-choice\s*\{[^}]*position:\s*relative")
        self.assertIn("permission-matrix.html", (ROOT / "README.md").read_text())
        self.assertIn("permission-matrix.html", (ROOT / "docs/index.html").read_text())
        self.assertIn("permission-matrix.html", (ROOT / "scripts/build_cloudflare_site.py").read_text())
        self.assertIn("permission-matrix.css", (ROOT / "scripts/build_cloudflare_site.py").read_text())
        self.assertIn("Permission matrix", (ROOT / "docs/recipes.md").read_text())
        self.assertIn("examples/permission-matrix.html", (ROOT / "llms.txt").read_text())


if __name__ == "__main__":
    unittest.main()
