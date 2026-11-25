"""Accessibility and publishing contract for composed AI/operations workflows.

These patterns must use existing source-candidate classes; they are not new
JS widgets or a new core CSS API.
"""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "examples/workflow-operations.html"


class Inspect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.ids = set()
        self.links = []
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.items.append((tag, attrs))
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "script":
            self.scripts += 1
        if tag in {"a", "link"}:
            self.links.append(attrs.get("href", ""))


class WorkflowOperationsContract(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PAGE.exists(), "The workflow demo must exist")
        self.page = PAGE.read_text(encoding="utf-8")
        self.html = Inspect()
        self.html.feed(self.page)

    def test_three_reusable_compositions_use_real_html_semantics(self):
        self.assertTrue({"progress", "activity", "decisions"} <= self.html.ids)
        self.assertEqual(len([1 for tag, attrs in self.html.items
                              if tag == "ol" and "syn-steps" in attrs.get("class", "")]), 1)
        self.assertEqual(len([1 for tag, attrs in self.html.items
                              if attrs.get("aria-current") == "step"]), 1)
        self.assertEqual(len([1 for tag, attrs in self.html.items
                              if tag == "ol" and "syn-activity-timeline" in attrs.get("class", "")]), 1)
        self.assertGreaterEqual(len([1 for tag, _ in self.html.items if tag == "details"]), 2)
        self.assertGreaterEqual(len([1 for tag, _ in self.html.items if tag == "time"]), 2)
        self.assertGreaterEqual(len([1 for tag, _ in self.html.items if tag == "summary"]), 2)
        for id_ in ("progress-heading", "activity-heading", "decisions-heading"):
            self.assertIn(id_, self.html.ids)

    def test_demo_does_not_pretend_to_approve_or_execute_live_jobs(self):
        self.assertEqual(self.html.scripts, 0)
        actions = [attrs for tag, attrs in self.html.items if tag == "button"]
        self.assertGreaterEqual(len(actions), 2)
        self.assertTrue(all("disabled" in attrs for attrs in actions),
                        "All demo mutation buttons must be disabled")
        self.assertIn("server", self.page.lower())
        self.assertIn("illustrative", self.page.lower())
        self.assertIn("csrf", self.page.lower())
        self.assertIn("authorization", self.page.lower())
        self.assertNotIn('aria-live="assertive"', self.page)
        self.assertNotIn('action="#"', self.page)

    def test_local_assets_and_adoption_links(self):
        self.assertTrue((ROOT / "examples/workflow-operations.css").is_file())
        self.assertIn('href="../dist/syntyr.core.css"', self.page)
        self.assertIn('href="../dist/syntyr.recipes.css"', self.page)
        self.assertIn('href="workflow-operations.css"', self.page)
        for href in self.html.links:
            if href.startswith("#") and len(href) > 1:
                self.assertIn(href[1:], self.html.ids)
        self.assertIn("examples/workflow-operations.html", (ROOT / "README.md").read_text())
        self.assertIn("workflow-operations.html", (ROOT / "docs/recipes.md").read_text())
        self.assertIn("examples/workflow-operations.html", (ROOT / "llms.txt").read_text())
        publisher = (ROOT / "scripts/build_cloudflare_site.py").read_text()
        for item in ("workflow-operations.html", "workflow-operations.css"):
            self.assertIn(item, publisher)


if __name__ == "__main__":
    unittest.main()
