"""Contracts for the static, source-only settings and billing showcase."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples/settings-billing.html"
CSS = ROOT / "examples/settings-billing.css"

class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

class SettingsBillingShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.html = HTML.read_text(encoding="utf-8")
        self.css = CSS.read_text(encoding="utf-8")
        parser = Elements()
        parser.feed(self.html)
        self.elements = parser.elements

    def test_uses_existing_syntyr_composition_without_runtime(self):
        for part in ("syn-root", "syn-app-shell", "syn-app-rail", "syn-app-nav",
                     "syn-workspace", "syn-nav-tabs", "syn-pricing", "syn-price-card",
                     "syn-app-card"):
            self.assertIn(part, self.html)
        self.assertNotIn("<script", self.html)
        self.assertNotIn("syntyr.all.css", self.html)
        self.assertIn("syntyr.core.css", self.html)
        self.assertIn("syntyr.recipes.css", self.html)
        self.assertIn("settings-billing.css", self.html)
        self.assertIn('data-syn-density="compact"', self.html)

    def test_billing_navigation_targets_real_sections(self):
        ids = [attrs["id"] for _, attrs in self.elements if attrs.get("id")]
        self.assertEqual(len(ids), len(set(ids)))
        for tag, attrs in self.elements:
            href = attrs.get("href", "")
            if href.startswith("#"):
                self.assertIn(href[1:], ids, f"Missing internal destination {href}")
            self.assertNotEqual(href, "#")
            self.assertNotIn("javascript:", href.lower())
        for target in ("plans", "usage", "invoices", "team", "account", "communication"):
            self.assertIn(target, ids)
        self.assertTrue(any(tag == "main" for tag, _ in self.elements))

    def test_three_plans_have_unambiguous_current_subscription_and_annual_costs(self):
        self.assertEqual(self.html.count('class="syn-price-card'), 3)
        self.assertIn("Current plan", self.html)
        self.assertIn("20% compared with monthly billing", self.html)
        for annual in ("$240", "$720", "$1440"):
            self.assertIn(annual, self.html)
        self.assertIn("per member", self.html.lower())
        self.assertIn("illustrative", self.html.lower())
        self.assertIn("payment processing", self.html.lower())
        self.assertIn('role="group" aria-label="Illustrative developer plans"', self.html)

    def test_billing_cycle_is_a_native_radio_group_with_visible_price_state(self):
        radios = [(tag, attrs) for tag, attrs in self.elements if tag == "input"
                  and attrs.get("name") == "billing-cycle"]
        self.assertEqual([attrs.get("value") for _, attrs in radios], ["monthly", "yearly"])
        self.assertEqual(sum("checked" in attrs for _, attrs in radios), 1)
        self.assertIn(":has(#cycle-yearly:checked)", self.css)
        self.assertIn(":has(#cycle-monthly:checked)", self.css)
        self.assertIn(".settings-price--yearly", self.css)
        self.assertIn(".settings-price--monthly", self.css)

    def test_no_live_commerce_actions_or_external_assets(self):
        for tag, attrs in self.elements:
            if tag == "form":
                self.fail("Static showcase should not submit any forms")
            if tag in ("link", "script", "img"):
                src = attrs.get("href", attrs.get("src", ""))
                self.assertFalse(src.startswith(("http:", "https:", "//")), src)
            if tag == "button" and attrs.get("type") == "submit":
                self.fail("No demo checkout or persistence actions allowed")
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn("forced-colors", self.css)
        self.assertIn("min-width", self.css)

    def test_sticky_global_navigation_starts_at_two_column_shell_breakpoint(self):
        recipes = (ROOT / "src/recipes.css").read_text(encoding="utf-8")
        shell_breakpoint = re.search(
            r"@media \(min-width: ([\d.]+rem)\) \{\s*&\.syn-app-shell \{ grid-template-columns:",
            recipes,
        )
        sticky_breakpoint = re.search(
            r"@media \(min-width: ([\d.]+rem)\) \{\s*\.settings-global-rail \{ position: sticky;",
            self.css,
        )
        self.assertIsNotNone(shell_breakpoint, "App shell's two-column breakpoint not found")
        self.assertIsNotNone(sticky_breakpoint, "Settings rail sticky breakpoint not found")
        self.assertEqual(sticky_breakpoint.group(1), shell_breakpoint.group(1))

    def test_public_example_is_explicitly_allowlisted_and_discoverable(self):
        site = (ROOT / "scripts/build_cloudflare_site.py").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn('"settings-billing.html"', site)
        self.assertIn('"settings-billing.css"', site)
        self.assertIn('"examples/settings-billing.html"', site)
        self.assertIn("examples/settings-billing.html", readme)
        self.assertIn("settings-billing.html", (ROOT / "docs/index.html").read_text())
        self.assertTrue((ROOT / "tests/settings_billing_browser.cjs").is_file())

if __name__ == "__main__":
    unittest.main()
