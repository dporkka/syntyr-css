"""Syntyr developer-workspace composition: accessible, portable, script-free."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples/developer-workspace.html"
CSS = ROOT / "examples/developer-workspace.css"


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = []

    def handle_starttag(self, name, attrs):
        self.nodes.append((name, dict(attrs)))


class DeveloperWorkspaceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = HTML.read_text(encoding="utf-8")
        parser = Tags()
        parser.feed(cls.raw)
        cls.nodes = parser.nodes

    def test_semantic_landmarks_and_navigation(self):
        self.assertEqual(sum(tag == "main" for tag, _ in self.nodes), 1)
        self.assertEqual(sum(tag == "h1" for tag, _ in self.nodes), 1)
        self.assertEqual(sum(tag == "script" for tag, _ in self.nodes), 0)
        self.assertTrue(any(tag == "nav" and a.get("aria-label") == "Workspace sections"
                            for tag, a in self.nodes))
        self.assertTrue(any(tag == "nav" and a.get("aria-label") == "Project files"
                            for tag, a in self.nodes))
        self.assertTrue(any(tag == "details" for tag, _ in self.nodes))
        self.assertTrue(any(tag == "pre" and a.get("tabindex") == "0"
                            for tag, a in self.nodes))
        self.assertIn('data-syn-theme="studio"', self.raw)
        self.assertIn('syn-app-shell', self.raw)
        self.assertIn('syn-app-rail', self.raw)

    def test_links_are_working_local_destinations(self):
        ids = [a["id"] for _, a in self.nodes if a.get("id")]
        self.assertEqual(len(ids), len(set(ids)))
        for tag, a in self.nodes:
            if tag not in ("a", "link"):
                continue
            url = a.get("href", "")
            self.assertFalse(url.startswith(("http:", "https:", "//", "javascript:", "data:")))
            if url.startswith("#"):
                self.assertIn(url[1:], ids)
            elif url:
                self.assertTrue((HTML.parent / unquote(urlsplit(url).path)).exists(), url)
        self.assertTrue(any(tag == "a" and a.get("href") == "#preview" for tag, a in self.nodes))
        self.assertTrue(any(tag == "a" and a.get("href") == "#logs" for tag, a in self.nodes))

    def test_no_fake_app_actions_or_synthetic_live_status(self):
        self.assertFalse(any(tag in ("button", "form", "input") for tag, _ in self.nodes))
        self.assertIn("illustrative", self.raw.lower())
        self.assertIn("no live deployment", self.raw.lower())
        self.assertNotIn("aria-live=", self.raw)
        self.assertNotIn('role="tree"', self.raw)
        self.assertNotIn('role="tablist"', self.raw)

    def test_styles_isolated_responsive_and_accessible(self):
        css = CSS.read_text(encoding="utf-8")
        self.assertIn(".dev-workspace", css)
        self.assertIn("var(--syn-", css)
        self.assertIn("@media (max-width:", css)
        self.assertIn("@media (forced-colors: active)", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn(":focus-visible", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)
        self.assertIn('developer-workspace.css', self.raw)

    def test_is_published_and_discoverable(self):
        allowlist = (ROOT / "scripts/build_cloudflare_site.py").read_text()
        gallery = (ROOT / "docs/index.html").read_text()
        readme = (ROOT / "README.md").read_text()
        for filename in ("developer-workspace.html", "developer-workspace.css"):
            self.assertIn('"' + filename + '"', allowlist)
        self.assertIn("examples/developer-workspace.html", readme)
        self.assertIn("developer-workspace.html", gallery)
        for test in ("reflow_test.py", "browser_matrix.py", "axe_audit.py"):
            self.assertIn('"examples/developer-workspace.html"', (ROOT / "tests" / test).read_text())


if __name__ == "__main__":
    unittest.main()
