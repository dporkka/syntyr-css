"""Stable native CSS patterns: contrast, typography, tokens, and composition."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def source(path):
    return (ROOT / path).read_text(encoding="utf-8")

class NativeCSSDesignContract(unittest.TestCase):
    def test_primary_hover_uses_explicit_accessible_color_contract(self):
        tokens = source("src/tokens.css")
        buttons = source("src/components/buttons.css")
        self.assertIn("--syn-primary-hover-bg: var(--syn-accent);", tokens)
        self.assertIn("background: var(--syn-button-hover-bg, var(--syn-primary-hover-bg));", buttons)
        self.assertIn("border-color: var(--syn-button-hover-border-color, var(--syn-on-accent));", buttons)
        self.assertNotIn("white 10%", buttons)

    def test_platform_controls_font_rendering(self):
        self.assertNotIn("-webkit-font-smoothing", source("src/base.css"))

    def test_semantic_elevation_and_motion_tokens_are_consumed(self):
        tokens = source("src/tokens.css")
        self.assertIn("--syn-shadow-raised:", tokens)
        self.assertIn("--syn-shadow-overlay:", tokens)
        self.assertIn("--syn-duration-standard:", tokens)
        self.assertIn("--syn-ease-enter:", tokens)
        self.assertIn("box-shadow: var(--syn-shadow-overlay);", source("src/components/overlays.css"))
        self.assertIn("box-shadow: var(--syn-shadow-raised);", source("src/components/layout.css"))
        self.assertIn("var(--syn-ease-enter)", source("src/recipes.css"))

    def test_short_headings_use_balanced_wrapping(self):
        typographic = source("src/components/typography.css")
        self.assertIn("text-wrap: balance;", typographic)
        self.assertRegex(typographic, r"(?s)&\.syn-(?:title|display).*?text-wrap: balance;")
        self.assertRegex(typographic, r"(?s)&\.syn-section-heading.*?text-wrap: balance;")

    def test_high_contrast_preferences_cover_nested_themes_and_intensity(self):
        tokens = source("src/tokens.css")
        self.assertIn("@media (prefers-contrast: more)", tokens)
        contrast = tokens.split("@media (prefers-contrast: more)", 1)[1]
        self.assertIn(".syn-root [data-syn-theme]", contrast)
        self.assertIn(".syn-root [data-syn-intensity]", contrast)
        self.assertIn("--syn-border-subtle: var(--syn-frame-strong);", contrast)
        self.assertIn("--syn-grid-alpha: 0%;", contrast)
        self.assertIn("--syn-glow-alpha: 0%;", contrast)

    def test_native_flow_blockifies_inline_children_without_overriding_component_display(self):
        recipes = source("src/recipes.css")
        self.assertIn("&.syn-flow {", recipes)
        self.assertIn("display: flex;", recipes)
        self.assertIn("flex-direction: column;", recipes)
        self.assertIn("gap: var(--syn-flow-gap, var(--syn-space-3));", recipes)

    def test_high_contrast_clears_horizon_background_gradients(self):
        effects = source("src/effects.css")
        self.assertIn("@media (prefers-contrast: more)", effects)
        rule = effects.split("@media (prefers-contrast: more)", 1)[1]
        self.assertIn("&.syn-horizon { background-image: none; }", rule)

    def test_optional_flow_composition_uses_configurable_logical_gap(self):
        recipes = source("src/recipes.css")
        self.assertIn("&.syn-flow {", recipes)
        self.assertIn("gap: var(--syn-flow-gap, var(--syn-space-3));", recipes)
        self.assertNotIn(".syn-flow", source("src/components/layout.css"))

if __name__ == "__main__":
    unittest.main()
