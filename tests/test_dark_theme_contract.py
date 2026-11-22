"""Contract for conventional, accessible Syntyr dark SaaS palettes."""
from pathlib import Path
import unittest

from scripts.design_conformance import audit
from scripts.export_ecosystem_adapters import read_palettes

ROOT = Path(__file__).resolve().parents[1]
DARK = ("graphite", "midnight", "dim", "obsidian", "amethyst")


class DarkSaaSPalettes(unittest.TestCase):
    def test_dark_palettes_have_complete_scoped_tokens_and_safe_colors(self):
        css = (ROOT / "src/tokens.css").read_text(encoding="utf-8")
        palettes = read_palettes(css)
        report = audit(css)
        for name in DARK:
            with self.subTest(name=name):
                self.assertIn(name, palettes)
                self.assertIn(f'.syn-root [data-syn-theme="{name}"]', css)
                self.assertIn(f'color-scheme: dark;', css.split(f'.syn-root[data-syn-theme="{name}"]', 1)[1].split('}', 1)[0])
                self.assertTrue(all(c["ok"] for c in report["palettes"][name]["checks"]))

    def test_auto_uses_neutral_graphite_in_dark_mode(self):
        css = (ROOT / "src/tokens.css").read_text(encoding="utf-8")
        palettes = read_palettes(css)
        auto = css.split('/* Opt-in system palette:', 1)[1].split('/* Experimental perceptual mixing:', 1)[0]
        for role in ("bg", "surface", "surface-hi", "text", "muted", "accent", "on-accent", "frame"):
            with self.subTest(role=role):
                light = palettes["studio"][f"--syn-{role}"]
                dark = palettes["graphite"][f"--syn-{role}"]
                self.assertIn(f"--syn-{role}: light-dark({light}, {dark});", auto)
        self.assertIn('color-scheme: light dark;', auto)

    def test_gallery_and_editor_expose_all_new_palettes(self):
        gallery = (ROOT / "examples/themes.html").read_text()
        editor = (ROOT / "docs/theme-editor.html").read_text()
        guide = (ROOT / "docs/theme-customization.md").read_text()
        for name in DARK:
            with self.subTest(name=name):
                self.assertIn(f'data-syn-theme="{name}"', gallery)
                self.assertIn(f'<option value="{name}">', editor)
                self.assertIn(f'data-syn-theme="{name}"', guide)
        # Full-component visual comparison, not accent-only swatches.
        for component in ("syn-panel", "syn-button", "syn-input", "syn-table", "syn-badge"):
            self.assertIn(component, gallery)


if __name__ == "__main__":
    unittest.main()
