"""Native business workflows must remain semantic, server-ready, and script-free."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class NativeWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "examples/native-workflows.html").read_text()
        cls.tags = Tags()
        cls.tags.feed(cls.html)

    def test_opt_in_css_hooks_and_fallbacks_are_shipped(self):
        source = (ROOT / "src/recipes.css").read_text()
        built = (ROOT / "dist/syntyr.recipes.css").read_text()
        for name in ("syn-upload-field", "syn-form-actions",
                     "syn-form-actions__buttons"):
            self.assertIn("&." + name, source)
            self.assertIn("&." + name, built)
        self.assertIn("padding: min(var(--syn-space-3), 2vw)", source)
        self.assertIn("padding-inline-start: min(1.25rem, 3vw)", source)
        self.assertIn("inset-block-end: 0", source)
        self.assertIn("padding-inline-start:", source)
        self.assertIn("@media (forced-colors: active)", source)

    def test_server_ready_multi_action_file_form(self):
        tags = self.tags.items
        forms = [a for t, a in tags if t == "form" and a.get("id") == "resource-editor"]
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0].get("enctype"), "multipart/form-data")
        self.assertEqual(forms[0].get("method"), "post")
        file_input = next(a for t, a in tags if t == "input" and a.get("type") == "file")
        self.assertEqual(file_input.get("name"), "attachments")
        self.assertIn("multiple", file_input)
        self.assertIn("accept", file_input)
        self.assertIn("upload-help", file_input.get("aria-describedby", ""))
        self.assertTrue(any(t == "label" and a.get("for") == file_input["id"] for t, a in tags))
        actions = [a for t, a in tags if t == "button" and a.get("form") == "resource-editor"]
        self.assertEqual({a.get("value") for a in actions}, {"save", "save-close"})
        self.assertTrue(all(a.get("name") == "intent" and "disabled" in a for a in actions))
        self.assertFalse(any(t == "script" for t, _ in tags))

    def test_nested_form_action_footer_does_not_claim_prohibited_aria_name(self):
        # This <footer> is not a contentinfo landmark and cannot use
        # aria-label without a valid role; the visible buttons name themselves.
        actions = [(tag, attrs) for tag, attrs in self.tags.items
                   if "syn-form-actions" in attrs.get("class", "").split()]
        self.assertEqual(len(actions), 1)
        tag, attrs = actions[0]
        self.assertEqual(tag, "footer")
        self.assertNotIn("aria-label", attrs)

    def test_linked_explorer_uses_disclosure_not_fake_treeview(self):
        tags = self.tags.items
        self.assertTrue(any(t == "nav" and a.get("aria-label") == "Browse resources" for t, a in tags))
        self.assertGreaterEqual(sum(t == "details" for t, _ in tags), 2)
        self.assertGreaterEqual(sum(t == "summary" for t, _ in tags), 2)
        self.assertFalse(any("role" in a and a["role"] in ("tree", "treeitem") for _, a in tags))
        ids = [a["id"] for _, a in tags if "id" in a]
        self.assertEqual(len(ids), len(set(ids)))
        links = [a["href"][1:] for t, a in tags if t == "a" and a.get("href", "").startswith("#")]
        self.assertTrue({"record-rs204", "record-rs088"}.issubset(set(links)))
        self.assertTrue(set(links).issubset(set(ids)))
        self.assertIn("syn-detail-layout", self.html)
        self.assertIn("syn-detail-main", self.html)
        self.assertIn("syn-detail-aside", self.html)

    def test_public_example_is_part_of_accessibility_audit(self):
        import ast
        tree = ast.parse((ROOT / "tests/axe_audit.py").read_text())
        pages = next(ast.literal_eval(node.value) for node in tree.body
                     if isinstance(node, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "PAGES"
                             for t in node.targets))
        self.assertIn("examples/native-workflows.html", pages)

    def test_docs_explain_backend_behavior_not_fake_js(self):
        docs = (ROOT / "docs/native-workflows.md").read_text()
        for phrase in ("CSRF", "authorization", "file size", "HTML", "server", "keyboard"):
            self.assertIn(phrase, docs)
        self.assertIn("examples/native-workflows.html", (ROOT / "llms.txt").read_text())


if __name__ == "__main__":
    unittest.main()
