"""Regression contracts for the second native semantic-content expansion."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.ids = set()
        self.links = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.links.append(attrs["href"][1:])
        if tag == "script" or any(attr.startswith("on") for attr in attrs):
            self.scripts.append((tag, attrs))


class SemanticContentPatterns(unittest.TestCase):
    def setUp(self):
        self.markup = (ROOT / "examples/semantic-compositions.html").read_text()
        self.dom = Document()
        self.dom.feed(self.markup)

    def test_opt_in_styles_only_where_native_presentation_is_useful(self):
        css = (ROOT / "src/semantic.css").read_text()
        for tag in ("s", "thead"):
            with self.subTest(tag=tag):
                self.assertIn(f"{tag}:not([class])", css)
                self.assertIn(f"{tag}[data-syn-semantic]", css)
        # These elements already have native user-agent semantics and behavior.
        for tag in ("ruby", "rt", "rp", "bdi", "bdo", "wbr", "sub", "sup", "datalist"):
            with self.subTest(native=tag):
                self.assertNotIn(f"{tag}:not([class])", css)
        self.assertIn("@media (forced-colors: active)", css)
        self.assertNotIn("appearance: none", css)
        self.assertNotIn("text-decoration: none", css)

    def test_gallery_has_additional_real_semantic_components_and_no_scripts(self):
        names = {tag for tag, _ in self.dom.tags}
        for tag in ("s", "sup", "sub", "wbr", "hgroup", "address",
                    "colgroup", "col", "thead", "tfoot", "samp", "kbd", "var"):
            with self.subTest(tag=tag):
                self.assertIn(tag, names)
        self.assertFalse(self.dom.scripts)
        self.assertIn("syntyr.semantic.css", self.markup)
        self.assertIn("syntyr.core.css", self.markup)
        self.assertIn('scope="colgroup"', self.markup)
        self.assertIn('scope="row"', self.markup)
        self.assertIn('datetime=', self.markup)

    def test_footnote_backlink_and_toc_targets_exist(self):
        self.assertIn("note-1", self.dom.ids)
        self.assertIn("note-ref-1", self.dom.ids)
        self.assertIn("note-1", self.dom.links)
        self.assertIn("note-ref-1", self.dom.links)
        self.assertIn('aria-label="On this page"', self.markup)
        self.assertTrue(all(target in self.dom.ids for target in self.dom.links),
                        "all in-page navigation targets must resolve")

    def test_reliable_pricing_notation_is_not_a_fake_change_record(self):
        self.assertIn("<s>", self.markup)
        self.assertIn("<data value=", self.markup)
        self.assertIn("Example price", self.markup)
        self.assertNotIn('href="#"', self.markup)

    def test_copyable_documentation_and_website_navigation(self):
        docs = (ROOT / "docs/semantic-components.md").read_text()
        for item in ("## Previous price versus revision", "## Footnotes",
                     "## Technical notation", "## Grouped table headings",
                     "## Contact details", "## In-page navigation"):
            with self.subTest(section=item):
                self.assertIn(item, docs)
        self.assertGreaterEqual(docs.count("~~~html"), 14)
        self.assertIn("native", docs.lower())
        self.assertIn("server", docs.lower())
        self.assertIn('href="examples/semantic-compositions.html"',
                      (ROOT / "index.html").read_text())
        self.assertIn('href="../examples/semantic-compositions.html"',
                      (ROOT / "docs/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
