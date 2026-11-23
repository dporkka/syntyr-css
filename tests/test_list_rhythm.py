"""Regression contracts for native, scoped, dependency-free list presentation."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ListMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lists = []

    def handle_starttag(self, tag, attrs):
        if tag in ("ul", "ol"):
            self.lists.append((tag, dict(attrs)))


class ListRhythmContract(unittest.TestCase):
    def css_between(self, css, start, end):
        start_index = css.find(start)
        end_index = css.find(end)
        self.assertNotEqual(start_index, -1, f"Missing CSS start anchor: {start!r}")
        self.assertNotEqual(end_index, -1, f"Missing CSS end anchor: {end!r}")
        self.assertGreater(end_index, start_index, f"CSS end anchor {end!r} must follow {start!r}")
        return css[start_index:end_index]

    def test_opt_in_core_list_preserves_native_markers_and_uses_logical_indent(self):
        css = source("src/components/typography.css")
        self.assertIn("&.syn-list {", css)
        self.assertIn("padding-inline-start: 1.5rem;", css)
        self.assertIn("&.syn-list > li", css)
        self.assertNotIn("&.syn-list { list-style: none", css)

    def test_opt_in_list_supports_compact_and_accent_styles_without_js(self):
        css = source("src/components/typography.css")
        self.assertIn(".syn-list--compact", css)
        self.assertIn(".syn-list--accent > li::marker", css)
        self.assertIn("var(--syn-accent)", css)
        self.assertIn("var(--syn-list-item-gap", css)

    def test_semantic_lists_define_nested_rhythm_without_resetting_markers(self):
        css = source("src/semantic.css")
        self.assertIn("ul:not([class])", css)
        self.assertIn("ol:not([class])", css)
        self.assertIn("padding-inline-start: 1.5rem", css)
        self.assertIn("Nested lists", css)
        list_css = self.css_between(css, "/* Ordinary document content", "dl:not([class])")
        self.assertNotIn("list-style: none", list_css)

    def test_feature_list_uses_readable_foreground_and_custom_gap(self):
        css = source("src/components/patterns.css")
        self.assertIn("--syn-feature-list-gap", css)
        feature_css = self.css_between(css, "&.syn-feature-list {", "&.syn-feature-list li::marker")
        self.assertIn("color: var(--syn-text)", feature_css)

    def test_grouped_rows_can_override_density_without_new_component(self):
        css = source("src/components/patterns.css")
        self.assertIn("--syn-list-row-padding", css)
        self.assertIn("&.syn-list-group", css)

    def test_example_lists_keep_native_structure_and_a11y_role_when_markerless(self):
        demo = source("examples/common-ui.html")
        parsed = ListMarkup()
        parsed.feed(demo)
        groups = [attrs for _, attrs in parsed.lists if "syn-list-group" in attrs.get("class", "").split()]
        self.assertTrue(groups)
        self.assertTrue(all(attrs.get("role") == "list" for attrs in groups))
        assert any("syn-list--accent" in attrs.get("class", "") for _, attrs in parsed.lists)
        assert any("syn-list--compact" in attrs.get("class", "") for _, attrs in parsed.lists)
        self.assertNotIn("<script", demo.lower())

    def test_markerless_collections_and_stepper_snippets_preserve_list_roles(self):
        for path in ("examples/app-team.html", "examples/native-choice-filter-list.html",
                     "blocks/snippets/docs-layout.html", "blocks/snippets/milestone-timeline.html"):
            with self.subTest(path=path):
                parsed = ListMarkup()
                parsed.feed(source(path))
                items = [attrs for _, attrs in parsed.lists
                         if any(name in attrs.get("class", "").split()
                                for name in ("syn-list-group", "syn-steps"))]
                self.assertTrue(items)
                self.assertTrue(all(item.get("role") == "list" for item in items))

    def test_native_demo_contains_nested_mixed_ol_ul(self):
        html = source("examples/native-elements.html")
        self.assertIn("Nested list", html)
        self.assertIn("<ul><li>", html)
        self.assertIn("<ol><li>", html)

    def test_docs_explain_core_list_and_safari_markerless_list_semantics(self):
        docs = source("docs/components.md")
        self.assertIn(".syn-list", docs)
        self.assertIn("role=\"list\"", docs)
        self.assertIn("--syn-list-row-padding", docs)


if __name__ == "__main__":
    unittest.main()
