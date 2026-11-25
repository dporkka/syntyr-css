"""Native, dependency-free developer-console navigation contract."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "examples/operations-console.html"
CSS = ROOT / "examples/operations-console.css"


class ControlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.popovers = set()
        self.triggers = []
        self.fragment_links = []
        self.scripts = []
        self.buttons = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        identifier = attributes.get("id")
        if identifier:
            self.ids.append(identifier)
            if "popover" in attributes:
                self.popovers.add(identifier)
        if tag == "button":
            self.buttons.append(attributes)
            if "popovertarget" in attributes:
                self.triggers.append(attributes)
        if tag == "a" and attributes.get("href", "").startswith("#"):
            self.fragment_links.append(attributes["href"][1:])
        if tag == "script":
            self.scripts.append(attributes)


class NativeConsolePatternsTest(unittest.TestCase):
    def setUp(self):
        self.html = PAGE.read_text(encoding="utf-8")
        self.parser = ControlParser()
        self.parser.feed(self.html)

    def test_native_action_palette_has_reachable_targets(self):
        self.assertIn("ops-quick-actions", self.parser.popovers)
        self.assertIn("ops-resource-peek", self.parser.popovers)
        targets = [button["popovertarget"] for button in self.parser.triggers]
        self.assertIn("ops-quick-actions", targets)
        self.assertIn("ops-resource-peek", targets)
        self.assertTrue(set(targets) <= self.parser.popovers)
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))
        self.assertTrue(set(self.parser.fragment_links) <= set(self.parser.ids))

    def test_action_compositions_are_useful_without_javascript(self):
        self.assertIn('aria-label="Quick navigation"', self.html)
        self.assertIn('aria-label="Gateway API resource details"', self.html)
        self.assertIn('href="#deployments"', self.html)
        self.assertIn('href="#diagnostics"', self.html)
        self.assertIn("Sample resource", self.html)
        self.assertIn("No live actions", self.html)
        self.assertIn("Popover API", self.html)
        self.assertIn('popover role="dialog" aria-label="Quick navigation"', self.html)
        self.assertEqual(self.parser.scripts, [])
        self.assertNotIn("onclick=", self.html.lower())

    def test_native_popovers_are_styled_and_fallback_is_navigable(self):
        css = CSS.read_text(encoding="utf-8")
        self.assertIn(".ops-action-popover", css)
        self.assertIn(".ops-action-link:focus-visible", css)
        self.assertIn("@media (forced-colors: active)", css)
        self.assertIn('href="#deployments"', self.html)
        self.assertIn('href="#activity"', self.html)

    def test_workspace_selector_is_native_and_does_not_claim_to_switch_identity(self):
        self.assertIn('popovertarget="ops-workspaces"', self.html)
        self.assertIn('aria-label="Choose example workspace: Northstar infrastructure"', self.html)
        self.assertIn('id="ops-workspaces"', self.html)
        self.assertIn('aria-label="Example workspaces"', self.html)
        self.assertIn('aria-current="true"', self.html)
        self.assertIn('aria-label="Close workspace choices"', self.html)
        self.assertIn('href="#integration"', self.html)
        self.assertIn("server-side membership", self.html)
        self.assertNotIn('data-tenant-id=', self.html)

    def test_release_registry_keeps_example_public(self):
        self.assertIn('"operations-console.html"', (ROOT / "scripts/build_cloudflare_site.py").read_text())
        for name in ("README.md", "docs/index.html"):
            self.assertIn("operations-console.html", (ROOT / name).read_text())


if __name__ == "__main__":
    unittest.main()
