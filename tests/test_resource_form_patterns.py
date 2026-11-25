"""CSS-first collection and form-recovery contracts, without a JS runtime."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class ResourceFormPatternsTests(unittest.TestCase):
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
        self.assertIn("examples/resource-workspace.html", pages)

    def test_recipes_extend_opt_in_root_without_runtime(self):
        css = (ROOT / "src/recipes.css").read_text()
        for selector in ("&.syn-collection-toolbar", "&.syn-collection-actions",
                         "&.syn-table--compact", "&.syn-bulk-actions",
                         "&.syn-result-state", "&.syn-error-summary"):
            self.assertIn(selector, css)
        self.assertIn("@media (forced-colors: active)", css)
        self.assertNotIn("javascript:", css.lower())

    def test_public_resource_workspace_is_discoverable_from_agent_index(self):
        index = (ROOT / "llms.txt").read_text()
        self.assertIn("https://syntyr-css.pages.dev/examples/resource-workspace.html", index)

    def test_example_forms_link_to_field_errors_and_preserve_names(self):
        markup = (ROOT / "examples/resource-workspace.html").read_text()
        parser = Markup()
        parser.feed(markup)
        ids = {attrs["id"] for _, attrs in parser.tags if "id" in attrs}
        self.assertIn("form-errors", ids)
        self.assertIn("resource-name", ids)
        self.assertIn("resource-name-error", ids)
        invalid = [attrs for tag, attrs in parser.tags if tag == "input" and attrs.get("id") == "resource-name"]
        self.assertEqual(invalid[0].get("aria-invalid"), "true")
        self.assertIn("resource-name-error", invalid[0].get("aria-describedby", "").split())
        self.assertEqual(len([tag for tag, _ in parser.tags if tag == "script"]), 0)
        self.assertTrue(any(tag == "a" and attrs.get("href") == "#resource-name" for tag, attrs in parser.tags))
        self.assertTrue(any(tag == "table" for tag, _ in parser.tags))
        self.assertTrue(any(tag == "caption" for tag, _ in parser.tags))
        self.assertTrue(any(tag == "form" and attrs.get("method") == "get" for tag, attrs in parser.tags))
        self.assertTrue(any(tag == "input" and attrs.get("name") == "q" and "disabled" in attrs for tag, attrs in parser.tags))
        self.assertTrue(any(tag == "button" and attrs.get("type") == "submit" and "disabled" in attrs for tag, attrs in parser.tags))
        self.assertIn("server implementation required", markup.lower())


if __name__ == "__main__":
    unittest.main()
