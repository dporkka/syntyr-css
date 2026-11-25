"""SaaS screen fragments must be framework neutral, accessible and registry-installable."""
import json
from pathlib import Path
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ("resource-workspace", "crm-workspace", "billing-workspace")


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.references = []
        self.tags = []
        self.forms = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.tags.append(tag)
        if "id" in data:
            if data["id"] in self.ids:
                raise AssertionError("Duplicate HTML ID: " + data["id"])
            self.ids.add(data["id"])
        if tag == "label" and data.get("for"):
            self.references.append(data["for"])
        if tag == "form":
            self.forms.append(data)


class SaaSWorkflowBlocks(unittest.TestCase):
    def test_three_complete_saas_workflows_have_native_behavior_and_semantics(self):
        manifest = {item["id"]: item for item in json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]}
        for name in WORKFLOWS:
            with self.subTest(name=name):
                self.assertIn(name, manifest)
                self.assertIn("core", manifest[name]["modules"])
                self.assertIn("recipes", manifest[name]["modules"])
                source = (ROOT / "blocks/snippets" / (name + ".html")).read_text()
                parser = Markup()
                parser.feed(source)
                self.assertIn('class="syn-root', source)
                self.assertIn("syn-panel", source)
                self.assertNotIn("<script", source)
                self.assertNotIn('href="#"', source)
                self.assertTrue(parser.forms, "Functional host form expected")
                self.assertTrue(all(f.get("action", "").startswith("/") for f in parser.forms))
                self.assertTrue(set(parser.references).issubset(parser.ids))
                self.assertIn("illustrative", source.lower())
        self.assertIn('method="get"', (ROOT / "blocks/snippets/resource-workspace.html").read_text())
        self.assertIn('<table', (ROOT / "blocks/snippets/resource-workspace.html").read_text())
        self.assertIn('class="syn-pipeline"', (ROOT / "blocks/snippets/crm-workspace.html").read_text())
        self.assertIn('tabindex="0"', (ROOT / "blocks/snippets/crm-workspace.html").read_text())
        self.assertIn('method="post"', (ROOT / "blocks/snippets/billing-workspace.html").read_text())
        self.assertIn("aria-describedby", (ROOT / "blocks/snippets/billing-workspace.html").read_text())

    def test_all_three_are_published_through_generated_static_registry(self):
        for name in WORKFLOWS:
            entry = json.loads((ROOT / "registry/r" / (name + ".json")).read_text())
            self.assertEqual(entry["name"], name)
            self.assertEqual(len(entry["registryDependencies"]), 2)
            self.assertFalse(entry["meta"]["runtimeJavaScript"])
            self.assertIn(name + ".html", entry["files"][0]["target"])


if __name__ == "__main__":
    unittest.main()
