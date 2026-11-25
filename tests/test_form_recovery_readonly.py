"""Contracts for semantic server-error recovery and readonly native controls."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class FormRecoveryReadonlyTests(unittest.TestCase):
    def test_readonly_is_visibly_distinct_in_classed_and_semantic_forms(self):
        forms = (ROOT / "src/components/forms.css").read_text()
        semantic = (ROOT / "src/semantic.css").read_text()
        self.assertIn("&.syn-input[readonly], &.syn-textarea[readonly]", forms)
        self.assertIn("border-style: dashed", forms)
        self.assertIn('input[data-syn-semantic][readonly]', semantic)
        self.assertIn('textarea[data-syn-semantic][readonly]', semantic)
        # Readonly fields remain selectable, focusable, and successful form controls.
        self.assertNotIn("pointer-events: none", forms)

    def test_error_recovery_recipe_has_real_links_and_preserves_input(self):
        docs = (ROOT / "docs/component-recipes.md").read_text()
        section = docs.split("## 5. Server-rendered error recovery", 1)[1]
        markup = re.search(r"```html\n(.*?)\n```", section, re.S)
        self.assertIsNotNone(markup)
        parser = Elements()
        parser.feed(markup.group(1))
        ids = {attrs["id"] for _, attrs in parser.elements if "id" in attrs}
        links = {attrs["href"] for tag, attrs in parser.elements
                 if tag == "a" and attrs.get("href", "").startswith("#")}
        self.assertIn("#account-email", links)
        self.assertIn("form-errors", ids)
        self.assertIn("account-email-error", ids)
        summary = next(attrs for _, attrs in parser.elements if attrs.get("id") == "form-errors")
        self.assertEqual(summary.get("role"), "region")
        self.assertEqual(summary.get("tabindex"), "-1")
        field = next(attrs for tag, attrs in parser.elements
                     if tag == "input" and attrs.get("id") == "account-email")
        self.assertEqual(field.get("aria-invalid"), "true")
        self.assertEqual(field.get("name"), "email")
        self.assertTrue(field.get("value"), "input must retain a submitted value")
        self.assertIn("account-email-error", field.get("aria-describedby", "").split())
        self.assertIn("account-email-hint", field.get("aria-describedby", "").split())
        self.assertTrue(any(tag == "form" and attrs.get("method") == "post"
                            and attrs.get("action") for tag, attrs in parser.elements))
        self.assertIn("syntyr.recipes.css", section)

    def test_demo_readonly_field_remains_real_native_input(self):
        markup = (ROOT / "examples/form-composition.html").read_text()
        parser = Elements()
        parser.feed(markup)
        readonly = [a for tag, a in parser.elements if tag == "input" and "readonly" in a]
        self.assertTrue(readonly)
        field = next(a for a in readonly if a.get("id") == "workspace-id")
        self.assertTrue(field.get("name"))
        self.assertTrue(field.get("value"))
        self.assertNotIn("disabled", field)
        self.assertTrue(any(tag == "label" and attrs.get("for") == "workspace-id"
                            for tag, attrs in parser.elements))


if __name__ == "__main__":
    unittest.main()
