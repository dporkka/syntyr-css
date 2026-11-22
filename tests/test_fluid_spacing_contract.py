"""Opt-in fluid spacing must not change Syntyr's stable fixed spacing scale."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FluidSpacingContract(unittest.TestCase):
    def test_fluid_tokens_ship_in_core_without_overriding_fixed_spacing(self):
        source = (ROOT / "src/tokens.css").read_text(encoding="utf-8")
        for index in range(1, 5):
            self.assertIn(f"--syn-space-fluid-{index}: clamp(", source)
        for index, rem in enumerate((".375", ".75", "1.125", "1.75", "2.5"), 1):
            self.assertIn(f"--syn-space-{index}: {rem}rem;", source)
        self.assertIn("@supports (width: 1vi)", source)
        self.assertIn("--syn-space-fluid-1: var(--syn-space-1);", source)
        self.assertNotIn("@import", source)

    def test_fluid_tokens_are_in_generated_core_stylesheet(self):
        generated = (ROOT / "dist/syntyr.core.css").read_text(encoding="utf-8")
        for index in range(1, 5):
            self.assertIn(f"--syn-space-fluid-{index}:", generated)

    def test_layout_guide_uses_real_core_components_and_preserves_module_boundaries(self):
        guide = (ROOT / "docs/composition-adoption.md").read_text(encoding="utf-8")
        for item in ("--syn-space-fluid-1", "--syn-space-fluid-4",
                     "syn-stack", "syn-inline", "syn-sidecar", "syn-grid",
                     "syntyr.core.css", "syntyr.recipes.css"):
            with self.subTest(item=item):
                self.assertIn(item, guide)
        self.assertIn("unreleased alpha.5", guide)
        self.assertIn("no JavaScript", guide)

    def test_tokens_are_documented_in_canonical_component_reference(self):
        reference = (ROOT / "docs/components.md").read_text(encoding="utf-8")
        self.assertIn("--syn-space-fluid-1", reference)
        self.assertIn("--syn-space-fluid-4", reference)


if __name__ == "__main__":
    unittest.main()
