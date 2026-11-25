"""Source-derived Figma handoff must not guess browser-computed styles."""
import json
from pathlib import Path
import unittest

from scripts.export_figma_handoff import build_handoff, outputs

ROOT = Path(__file__).resolve().parents[1]


class FigmaHandoffTests(unittest.TestCase):
    def test_foundation_dimensions_are_derived_from_css_source(self):
        handoff = build_handoff()
        self.assertEqual(handoff["schema_version"], 1)
        self.assertEqual(handoff["root_font_px_assumption"], 16)
        tokens = {entry["css_variable"]: entry for entry in handoff["foundations"]}
        self.assertEqual(tokens["--syn-space-1"]["figma_px"], 6)
        self.assertEqual(tokens["--syn-space-5"]["figma_px"], 40)
        self.assertEqual(tokens["--syn-control-height"]["figma_px"], 44)
        self.assertEqual(tokens["--syn-radius"]["figma_px"], 4)
        self.assertEqual(tokens["--syn-type-sm"]["figma_px"], 14)
        self.assertIsNone(tokens["--syn-type-heading"]["figma_px"])
        self.assertTrue(tokens["--syn-type-heading"]["requires_browser_validation"])

    def test_css_comments_cannot_override_real_source_values(self):
        from scripts.export_figma_handoff import scoped_declarations
        source = """:where(.syn-root) {
          --syn-space-2: .75rem;
          /* Draft override that must not become a Figma variable:
             --syn-space-2: 99rem;
          */
        }"""
        self.assertEqual(
            scoped_declarations(source, ":where(.syn-root)")["--syn-space-2"],
            ".75rem",
        )

    def test_density_states_are_source_derived_and_not_font_rescales(self):
        handoff = build_handoff()
        densities = handoff["density"]
        for name, height in (("compact", 36), ("comfortable", 44), ("spacious", 52)):
            self.assertEqual(densities[name]["--syn-control-height"]["figma_px"], height)
        self.assertNotIn("--syn-type-sm", densities["compact"])

    def test_handoff_flags_incomplete_figma_kit_and_real_component_selectors(self):
        handoff = build_handoff()
        self.assertEqual(len(handoff["palette_tokens"]), 13)
        self.assertEqual(handoff["figma_pilot"]["verified_color_tokens_per_theme"], None)
        self.assertIn("not-verified", handoff["figma_pilot"]["parity_status"])
        for name, expected in (("button", "syn-button--primary"), ("input", "syn-input")):
            self.assertIn(expected, handoff["components"][name]["css_classes"])
        self.assertIn("not a Figma file inspection", handoff["limitations"])

    def test_generated_handoff_is_current(self):
        for path, expected in outputs().items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
