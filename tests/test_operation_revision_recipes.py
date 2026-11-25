"""Contract for optional operation feedback and change-comparison recipes."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ExampleMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.classes = []
        self.ids = set()
        self.labels = []
        self.states = []
        self.scripts = 0
        self.buttons = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append(tag)
        self.classes.extend(attributes.get("class", "").split())
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        if attributes.get("aria-labelledby"):
            self.labels.extend(attributes["aria-labelledby"].split())
        if attributes.get("data-syn-state"):
            self.states.append(attributes["data-syn-state"])
        if tag == "script":
            self.scripts += 1
        if tag == "button":
            self.buttons.append(attributes)
        if tag == "a":
            self.links.append(attributes.get("href", ""))


class OperationRevisionRecipes(unittest.TestCase):
    def test_optional_css_reuses_existing_record_fields(self):
        source = read("src/recipes.css")
        self.assertIn("&.syn-operation-feedback", source)
        self.assertIn("&.syn-change-pair", source)
        self.assertIn("&.syn-change-before", source)
        self.assertIn("&.syn-change-after", source)
        self.assertIn("&.syn-record-fields", source)
        self.assertNotIn(".syn-change-list", source, "Do not fork the existing definition-list layout")
        self.assertNotIn(".syn-operation-feedback", read("dist/syntyr.core.css"))
        for state in ("pending", "saved", "failed", "conflict", "unsaved"):
            with self.subTest(state=state):
                self.assertIn(f'&.syn-operation-feedback[data-syn-state="{state}"]', source)
        self.assertIn("@media (forced-colors: active)", source)
        self.assertIn("overflow-wrap: anywhere;", source)

    def test_generated_optional_bundle_contains_both_primitives(self):
        css = read("dist/syntyr.recipes.css")
        self.assertIn("&.syn-operation-feedback", css)
        self.assertIn("&.syn-change-pair", css)

    def test_demo_uses_semantic_native_markup_without_simulated_actions(self):
        html = read("examples/operation-revisions.html")
        parser = ExampleMarkup()
        parser.feed(html)
        self.assertEqual(parser.scripts, 0)
        self.assertIn("syn-record-fields", parser.classes)
        self.assertIn("syn-change-pair", parser.classes)
        self.assertIn("syn-change-before", parser.classes)
        self.assertIn("syn-change-after", parser.classes)
        self.assertIn("syn-operation-feedback", parser.classes)
        for tag in ("dl", "dt", "dd", "del", "ins", "time", "main"):
            self.assertIn(tag, parser.tags)
        self.assertEqual(len(parser.buttons), 0, "No fake save/retry button without a backend")
        self.assertTrue({"pending", "saved", "failed", "conflict", "unsaved"} <= set(parser.states))
        self.assertTrue(set(parser.labels) <= parser.ids, "Labelled regions must reference real headings")
        self.assertIn("illustrative", html.lower())
        self.assertIn("not connected to a server", html.lower())
        self.assertIn("../dist/syntyr.core.css", html)
        self.assertIn("../dist/syntyr.recipes.css", html)

    def test_example_is_in_browser_reflow_and_axe_audit_matrices(self):
        for path in ('tests/browser_matrix.py', 'tests/reflow_test.py', 'tests/axe_audit.py'):
            with self.subTest(path=path):
                self.assertIn('"examples/operation-revisions.html"', read(path))

    def test_text_overflow_guards_and_optional_browser_regression(self):
        css = read("src/recipes.css")
        for name in ("syn-app-card", "syn-page-header"):
            with self.subTest(name=name):
                selector = f"&.{name} {{"
                self.assertIn(selector, css)
                rule = css.split(selector, 1)[1].split("}", 1)[0]
                self.assertIn("overflow-wrap: anywhere", rule)
        browser = read("tests/operation_revisions_browser.js")
        self.assertIn("textScale", browser)
        self.assertIn("[320, 4]", browser)
        self.assertIn("forcedColors", browser)
        self.assertIn("playwright", browser)
        self.assertIn("operation_revisions_browser.js", read("docs/recipes.md"))

    def test_docs_publishing_and_api_discovery(self):
        docs = read("docs/recipes.md")
        self.assertIn("operation-revisions.html", docs)
        self.assertIn("syn-change-pair", docs)
        self.assertIn("syn-operation-feedback", docs)
        self.assertIn("host", docs.lower())
        self.assertIn("operation-revisions.html", read("scripts/build_cloudflare_site.py"))
        self.assertIn("operation-revisions.html", read("docs/index.html"))
        self.assertIn("operation-revisions.html", read("README.md"))
        metadata = read("metadata/syntyr-api.json")
        self.assertIn('"name": "syn-operation-feedback"', metadata)
        self.assertIn('"name": "syn-change-pair"', metadata)


if __name__ == "__main__":
    unittest.main()
