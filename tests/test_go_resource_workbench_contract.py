"""Contract checks for the optional Go SSR resource-workbench example."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "go-resource-workbench"


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class GoResourceWorkbenchContract(unittest.TestCase):
    def test_no_runtime_dependency_added_to_syntyr_css(self):
        self.assertIn("go 1.24", (DEMO / "go.mod").read_text())
        self.assertNotIn("require ", (DEMO / "go.mod").read_text())
        self.assertTrue((DEMO / "main_test.go").exists())

    def test_semantic_markup_and_no_script(self):
        p = Markup()
        p.feed((DEMO / "templates/page.html").read_text())
        tags = p.tags
        self.assertFalse(any(tag == "script" for tag, _ in tags))
        self.assertTrue(any(tag == "search" for tag, _ in tags))
        self.assertTrue(any(tag == "table" for tag, _ in tags))
        self.assertTrue(any(tag == "caption" for tag, _ in tags))
        self.assertTrue(any(tag == "aside" for tag, _ in tags))
        self.assertTrue(any(tag == "form" and attrs.get("method") == "get" for tag, attrs in tags))
        post_forms = [attrs for tag, attrs in tags if tag == "form" and attrs.get("method") == "post"]
        self.assertEqual(len(post_forms), 1, "only the local resource edit form may POST")
        self.assertEqual(post_forms[0].get("action"), "/resource/edit")
        self.assertTrue(any(tag == "input" and attrs.get("type") == "hidden"
                            and attrs.get("name") == "csrf_token" for tag, attrs in tags))
        self.assertEqual(
            ["ids"],
            sorted(set(attrs.get("name") for tag, attrs in tags
                       if tag == "input" and attrs.get("type") == "checkbox" and attrs.get("name") == "ids"))
        )
        self.assertTrue(any(tag == "a" and attrs.get("href") == "#main" for tag, attrs in tags))

    def test_public_docs_explain_server_owned_selection(self):
        docs = (DEMO / "README.md").read_text()
        self.assertIn("Preview all matching", docs)
        self.assertIn("tenant", docs.lower())
        self.assertIn("CSRF", docs)
        self.assertIn("go-resource-workbench", (ROOT / "docs/recipes.md").read_text())


if __name__ == "__main__":
    unittest.main()
