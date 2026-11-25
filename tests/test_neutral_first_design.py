"""Neutral-first design contracts, including explicit opt-in technical styling."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class NeutralFirstDesign(unittest.TestCase):
    def test_implicit_theme_is_studio_but_grid_is_explicit(self):
        tokens = source("src/tokens.css")
        self.assertIn(':where(.syn-root, .syn-root[data-syn-theme="studio"]', tokens)
        self.assertIn(':where(.syn-root[data-syn-theme="grid"]', tokens)
        # The neutral default must precede explicit named themes in the cascade.
        self.assertLess(tokens.index(':where(.syn-root, .syn-root[data-syn-theme="studio"]'),
                        tokens.index(':where(.syn-root[data-syn-theme="grid"]'))
        self.assertNotIn('.syn-root:not([data-syn-theme])', tokens)

    def test_ordinary_panels_and_stages_have_no_forced_cinematic_decoration(self):
        layout = source("src/components/layout.css")
        panel = re.search(r"\.syn-panel\s*\{([^}]+)\}", layout).group(1)
        stage = re.search(r"\.syn-stage\s*\{([^}]+)\}", layout).group(1)
        self.assertIn("background: var(--syn-panel-bg, var(--syn-surface))", panel)
        self.assertIn("background: var(--syn-bg)", stage)
        self.assertNotIn("linear-gradient", panel)
        self.assertNotIn("radial-gradient", stage)
        self.assertNotIn(".syn-stage::before", layout)
        # Explicit industrial/precision/gradient styling stays available.
        self.assertIn(".syn-surface--accent", source("src/recipes.css"))
        self.assertIn(".syn-gradient-wash", source("src/effects.css"))

    def test_badge_does_not_imply_status_dot(self):
        typography = source("src/components/typography.css")
        self.assertNotIn(".syn-badge::before", typography)
        self.assertIn(".syn-status::before", source("src/components/data.css"))

    def test_section_heading_fills_gap_between_body_and_display(self):
        self.assertIn("--syn-type-section:", source("src/tokens.css"))
        self.assertIn(".syn-section-heading", source("src/components/typography.css"))
        self.assertIn("var(--syn-type-section)", source("src/components/typography.css"))
        self.assertIn("syn-section-heading", source("examples/business.html"))

    def test_long_table_text_can_wrap_without_changing_other_cells(self):
        data = source("src/components/data.css")
        self.assertIn(".syn-cell--wrap", data)
        self.assertRegex(data, r"\.syn-cell--wrap[^\{]*\{[^}]*white-space:\s*normal")
        self.assertIn("overflow-wrap: anywhere", data)
        self.assertIn('tr[data-syn-state="selected"] > :first-child', data)
        example = source("examples/saas-workflows.html")
        self.assertIn("syn-cell--wrap", example)
        self.assertIn("syn-cell--numeric", example)


if __name__ == "__main__":
    unittest.main()
