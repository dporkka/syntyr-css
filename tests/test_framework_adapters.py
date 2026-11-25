"""Contracts for optional framework adapters, without external tools."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class FrameworkAdaptersTest(unittest.TestCase):
    def test_vertigo_shell_adapter_is_scoped_to_opt_in(self):
        css = (ROOT / "integrations/vertigo/shell.css").read_text()
        for selector in ("body.syn-root.syn-vertigo", ".syn-vertigo .vg-topbar", ".syn-vertigo .vg-button"):
            self.assertIn(selector, css)
        for variable in ("--vg-bg", "--vg-text", "--vg-primary", "--vg-focus"):
            self.assertIn(variable, css)
        self.assertIn(".syn-vertigo .vg-topbar-inner { flex-wrap: wrap; }", css)
        self.assertIn("overflow-wrap: anywhere;", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)

    def test_rust_catalog_adapter_is_scoped_to_opt_in(self):
        css = (ROOT / "integrations/rust-saas-foundation/catalog.css").read_text()
        for selector in (".syn-rust-foundation .wrap", ".syn-rust-foundation .items", ".syn-rust-foundation .item"):
            self.assertIn(selector, css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)

    def test_rust_catalog_skip_navigation_is_keyboard_visible_and_scoped(self):
        css = (ROOT / "integrations/rust-saas-foundation/catalog.css").read_text()
        self.assertIn(".syn-rust-foundation .syn-rust-skip {", css)
        self.assertIn(".syn-rust-foundation .syn-rust-skip:focus-visible", css)
        self.assertIn("transform: translateY(-150%);", css)
        self.assertIn("transform: translateY(.75rem);", css)
        self.assertIn("border-color: Highlight;", css)

if __name__ == "__main__":
    unittest.main()
