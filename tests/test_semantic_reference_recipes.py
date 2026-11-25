"""Semantic editorial and reference compositions preserve real HTML behavior."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.ids = set()
        self.duplicates = []
    def handle_starttag(self, tag, raw_attrs):
        attrs = dict(raw_attrs)
        self.items.append((tag, attrs))
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.duplicates.append(attrs["id"])
            self.ids.add(attrs["id"])
    def by_tag(self, tag):
        return [attrs for name, attrs in self.items if name == tag]


class SemanticReferenceRecipes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gallery = (ROOT / "examples/semantic-compositions.html").read_text()
        cls.document = Inspector()
        cls.document.feed(cls.gallery)
        cls.guide = (ROOT / "docs/semantic-components.md").read_text()

    def test_native_datalist_has_label_options_and_real_search_target(self):
        datalists = [v for v in self.document.by_tag("datalist") if v.get("id") == "reference-topic-suggestions"]
        self.assertEqual(len(datalists), 1)
        inputs = [v for v in self.document.by_tag("input") if v.get("list") == "reference-topic-suggestions"]
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0].get("name"), "q")
        self.assertEqual(inputs[0].get("type"), "search")
        self.assertTrue(inputs[0].get("id"))
        self.assertTrue(any(v.get("for") == inputs[0]["id"] for v in self.document.by_tag("label")))
        self.assertGreaterEqual(len(self.document.by_tag("datalist")), 1)
        self.assertIn('action="https://github.com/dporkka/syntyr-css/issues"', self.gallery)

    def test_editorial_markup_has_real_glossary_and_highlights(self):
        tags = {name for name, _ in self.document.items}
        for tag in ("dfn", "abbr", "mark", "q", "cite", "dl", "dt", "dd"):
            with self.subTest(tag=tag):
                self.assertIn(tag, tags)
        self.assertIn('title="Accessible Rich Internet Applications"', self.gallery)
        self.assertIn('id="glossary-heading"', self.gallery)
        self.assertIn('id="excerpt-heading"', self.gallery)

    def test_ordered_release_list_preserves_list_and_machine_readable_dates(self):
        ordered = [attrs for attrs in self.document.by_tag("ol") if "reversed" in attrs]
        self.assertTrue(any(o.get("start") == "3" for o in ordered))
        dates = [attrs["datetime"] for attrs in self.document.by_tag("time") if "datetime" in attrs]
        for date in ("2026-11-14", "2026-11-15", "2026-11-16"):
            self.assertIn(date, dates)
        self.assertIn("Illustrative release steps", self.gallery)

    def test_mathml_is_real_math_with_readable_explanation(self):
        tags = {name for name, _ in self.document.items}
        for tag in ("math", "mrow", "mi", "mn", "mo", "msup", "semantics", "annotation"):
            with self.subTest(tag=tag):
                self.assertIn(tag, tags)
        self.assertIn('encoding="application/x-tex"', self.gallery)
        self.assertIn("a squared plus b squared equals c squared", self.gallery)
        # Mathematical rendering belongs to the browser, not the optional CSS skin.
        semantic_css = (ROOT / "src/semantic.css").read_text()
        self.assertNotIn("math:not([class])", semantic_css)
        self.assertNotIn("datalist:not([class])", semantic_css)

    def test_resource_menu_is_real_links_not_fake_aria_menu(self):
        self.assertIn("<menu>", self.gallery)
        self.assertNotIn('role="menu"', self.gallery)
        self.assertNotIn('href="#"', self.gallery)
        self.assertIn('href="../docs/semantic-components.html"', self.gallery)
        self.assertFalse(self.document.by_tag("script"))
        self.assertFalse(self.document.duplicates)

    def test_gallery_links_and_copyable_guide_are_kept_in_sync(self):
        ids = self.document.ids
        for attrs in self.document.by_tag("a"):
            if attrs.get("href", "").startswith("#"):
                self.assertIn(attrs["href"][1:], ids)
        for title in ("## Native suggestions with datalist", "## Glossary and abbreviations",
                      "## Highlighted excerpts and quotations", "## Chronological ordered list",
                      "## Mathematical notation with MathML", "## Resource command list"):
            with self.subTest(title=title):
                self.assertIn(title, self.guide)
        self.assertGreaterEqual(self.guide.count("~~~html"), 20)
        self.assertIn("No JavaScript", self.guide)
        self.assertIn('href="examples/semantic-compositions.html"', (ROOT / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
