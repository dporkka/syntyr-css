"""Dropdowns remain native by default and enhanced menus stay opt-in."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Demo(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.targets = []
        self.labels = []
        self.scripts = []
        self.popovers = 0
        self.selects = 0
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data:
            self.ids.add(data["id"])
        if "popovertarget" in data:
            self.targets.append(data["popovertarget"])
        if tag == "script":
            self.scripts.append(data)
        if tag == "select":
            self.selects += 1
        if tag == "label":
            self.labels.append(data)
        if "popover" in data:
            self.popovers += 1

class DropdownContract(unittest.TestCase):
    def test_compact_popover_menu_styles_with_native_fallbacks(self):
        css = (ROOT / "src/components/overlays.css").read_text()
        for piece in (".syn-dropdown", ".syn-dropdown__item", ".syn-dropdown__group-label",
                      ".syn-dropdown__separator", ".syn-dropdown__shortcut",
                      "max-block-size:", "overflow-y: auto", "min-block-size:",
                      "aria-current", "aria-disabled", "forced-colors: active"):
            with self.subTest(piece=piece):
                self.assertIn(piece, css)
        self.assertIn(".syn-popover.syn-popover--anchored", css)
        self.assertIn(".syn-dialog", css)

    def test_select_customization_does_not_replace_native_control(self):
        css = (ROOT / "src/components/forms.css").read_text()
        self.assertIn("@supports (appearance: base-select)", css)
        self.assertIn(".syn-select--enhanced", css)
        self.assertIn("::picker(select)", css)
        self.assertNotIn("appearance: none", css)

    def test_demo_uses_native_elements_without_javascript(self):
        html = (ROOT / "examples/dropdowns.html").read_text()
        demo = Demo()
        demo.feed(html)
        self.assertFalse(demo.scripts, "Basic dropdown example must remain scriptless")
        self.assertGreaterEqual(demo.selects, 1)
        self.assertGreaterEqual(demo.popovers, 1)
        self.assertTrue(set(demo.targets) <= demo.ids)
        self.assertIn("syn-dropdown__item", html)
        self.assertNotIn('role="menu"', html, "Tab-navigation action panels must not impersonate ARIA menus")

    def test_optional_menu_esm_is_not_a_core_dependency(self):
        js = (ROOT / "integrations/dropdown/menu.mjs").read_text()
        self.assertIn("export function enhanceMenu", js)
        self.assertNotIn("document.addEventListener", js, "Import must not auto-initialize")
        pkg = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(pkg["exports"]["./menu.mjs"], "./integrations/dropdown/menu.mjs")
        self.assertIn("integrations/dropdown/", pkg["files"])
        self.assertNotIn("menu.mjs", (ROOT / "dist/syntyr.core.css").read_text())

    def test_native_multiple_select_remains_preferred(self):
        guide = (ROOT / "docs/dropdowns.md").read_text()
        self.assertIn('<select class="syn-select" multiple', guide)
        self.assertIn('Autocomplete or hierarchical menu', guide)

    def test_dropdown_guide_and_demo_are_in_public_site_allowlist(self):
        site = (ROOT / "scripts/build_cloudflare_site.py").read_text()
        self.assertIn('"dropdowns.md"', site)
        self.assertIn('"dropdowns.html"', site)

    def test_guidance_distinguishes_action_panel_and_aria_menu(self):
        guide = (ROOT / "docs/dropdowns.md").read_text()
        for phrase in ("native", "Tab", "Escape", "role=\"menu\"", "ArrowDown",
                       "aria-disabled", "typeahead", "base-select", "screen reader"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)
        self.assertIn("docs/dropdowns.md", (ROOT / "README.md").read_text())

if __name__ == "__main__":
    unittest.main()
