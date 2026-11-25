"""Native table enhancement contracts: no fake grids, JS, or global style leaks."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.captions = 0
        self.headers = []
        self.region = None
        self.ids = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set(a.get("class", "").split())
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "table":
            self.tables.append(a)
        if tag == "caption":
            self.captions += 1
        if tag == "th":
            self.headers.append(a)
        if "syn-table-wrap--scroll" in classes:
            self.region = a

class EnterpriseDataTables(unittest.TestCase):
    def test_a11y_audit_includes_this_public_example(self):
        import ast
        tree = ast.parse((ROOT / "tests/axe_audit.py").read_text())
        pages = next(
            ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "PAGES"
                for target in node.targets
            )
        )
        self.assertIn("examples/data-tables.html", pages)

    def test_opt_in_native_table_styles_are_scoped(self):
        css = (ROOT / "src/components/data.css").read_text()
        for name in (".syn-table-wrap--scroll", ".syn-table--sticky", ".syn-table--striped", ".syn-table-sort"):
            self.assertIn(name, css)
        self.assertIn('aria-sort="ascending"', css)
        self.assertIn('aria-sort="descending"', css)
        self.assertIn("inset-block-start:", css)
        self.assertIn("overflow: auto", css)
        self.assertIn("forced-colors: active", css)
        self.assertIn(":where(.syn-root, .syn-root *)", css)
        self.assertNotIn("!important", css)

    def test_static_demo_exposes_real_table_semantics_without_fake_actions(self):
        html = (ROOT / "examples/data-tables.html").read_text()
        parsed = TableParser()
        parsed.feed(html)
        self.assertEqual(len(parsed.tables), 1)
        self.assertIn("syn-table", parsed.tables[0]["class"])
        self.assertEqual(parsed.captions, 1)
        self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
        self.assertIsNotNone(parsed.region)
        self.assertEqual(parsed.region.get("role"), "region")
        self.assertEqual(parsed.region.get("tabindex"), "0")
        self.assertTrue(parsed.region.get("aria-label"))
        self.assertEqual(sum(h.get("scope") == "col" for h in parsed.headers), 3)
        self.assertGreaterEqual(sum(h.get("scope") == "row" for h in parsed.headers), 12)
        self.assertTrue(all(h.get("scope") in ("row", "col") for h in parsed.headers))
        self.assertEqual([h.get("aria-sort") for h in parsed.headers].count("ascending"), 1)
        self.assertNotIn('role="grid"', html)
        self.assertNotIn("<script", html.lower())

    def test_docs_clarify_server_owned_sorting_and_license(self):
        guide = (ROOT / "docs/data-tables.md").read_text()
        for term in ("aria-sort", "GET", "server", "forced-colors", "MIT", "no JavaScript"):
            self.assertIn(term, guide)
        self.assertIn('"data-tables.md"', (ROOT / "scripts/build_cloudflare_site.py").read_text())
        self.assertIn("data-tables.html", (ROOT / "docs/components.md").read_text())
        self.assertIn("data-tables.html", (ROOT / "README.md").read_text())
        self.assertIn('"data-tables"', (ROOT / "scripts/build_doc_pages.py").read_text())

    def test_public_guide_is_indexed_for_agents(self):
        self.assertIn("https://syntyr-css.pages.dev/docs/data-tables.md",
                      (ROOT / "llms.txt").read_text())

    def test_print_scroll_cap_resets_and_sort_arrows_remain_vertical_in_rtl(self):
        print_css = (ROOT / "src/print.css").read_text()
        self.assertIn("max-block-size: none", print_css)
        css = (ROOT / "src/components/data.css").read_text()
        self.assertIn("border-right: 2px solid currentColor", css)
        self.assertIn("border-bottom: 2px solid currentColor", css)
        self.assertNotIn("border-inline-end: 2px solid currentColor", css)

    def test_generated_core_contains_opt_in_styles(self):
        css = (ROOT / "dist/syntyr.core.css").read_text()
        self.assertIn(".syn-table-wrap--scroll", css)
        self.assertIn(".syn-table--sticky", css)

if __name__ == "__main__":
    unittest.main()
