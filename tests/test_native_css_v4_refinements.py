"""Tailwind v4-inspired improvements that preserve Syntyr's zero-build contract."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class NativeCSSV4Refinements(unittest.TestCase):
    def test_core_layouts_accept_local_tokens_without_new_utilities(self):
        css = source("src/components/layout.css")
        for value in (
            "var(--syn-grid-gap, 1rem)",
            "var(--syn-grid-min, 17rem)",
            "var(--syn-layout-gap, 1.25rem)",
            "var(--syn-layout-min, 21rem)",
            "var(--syn-stack-gap, var(--syn-space-3))",
            "var(--syn-inline-gap, var(--syn-space-2))",
        ):
            with self.subTest(value=value):
                self.assertIn(value, css)

    def test_business_compositions_accept_container_friendly_tokens(self):
        css = source("src/recipes.css")
        for value in (
            "var(--syn-kpi-min, 13rem)",
            "var(--syn-kpi-gap, var(--syn-space-2))",
            "var(--syn-filter-gap, var(--syn-space-2))",
            "var(--syn-filter-field-min, 11rem)",
            "var(--syn-filter-query-min, 18rem)",
            "var(--syn-detail-gap, var(--syn-space-3))",
            "var(--syn-detail-main-min, 22rem)",
            "var(--syn-detail-aside-min, 17rem)",
        ):
            with self.subTest(value=value):
                self.assertIn(value, css)

    def test_field_native_states_add_progressive_focus_and_error_indicators(self):
        css = source("src/components/form-composition.css")
        self.assertIn("&.syn-field:focus-within > .syn-label", css)
        self.assertIn("&.syn-field:has(:user-invalid, [aria-invalid=\"true\"]) > .syn-label", css)
        self.assertIn("color: var(--syn-danger);", css)
        self.assertIn("&.syn-input-group:focus-within > .syn-input-addon", css)

    def test_inert_panel_visually_indicates_native_unavailability(self):
        css = source("src/components/layout.css")
        self.assertIn("&.syn-panel:where([inert])", css)
        self.assertIn("border-style: dashed;", css)
        self.assertIn("background: var(--syn-surface-recessed);", css)

    def test_oklch_is_explicit_progressive_and_keeps_default_colors(self):
        css = source("src/tokens.css")
        self.assertIn('@supports (color: color-mix(in oklch, red, blue))', css)
        self.assertIn('data-syn-color-space="oklch"', css)
        self.assertIn("--syn-surface-hover: color-mix(in oklch,", css)
        self.assertIn("--syn-surface-hover: color-mix(in srgb,", css)
        self.assertNotIn("@import", css)

    def test_editor_metadata_exposes_the_documented_opt_in_api(self):
        metadata = json.loads(source("metadata/syntyr-contract.json"))
        css_tokens = {token["name"] for token in metadata["tokens"]}
        expected = {
            "--syn-grid-min", "--syn-grid-gap", "--syn-layout-min",
            "--syn-layout-gap", "--syn-stack-gap", "--syn-inline-gap",
            "--syn-kpi-min", "--syn-kpi-gap", "--syn-filter-gap",
            "--syn-filter-field-min", "--syn-filter-query-min",
            "--syn-detail-gap", "--syn-detail-main-basis",
            "--syn-detail-main-min", "--syn-detail-aside-basis",
            "--syn-detail-aside-min",
        }
        self.assertFalse(expected - css_tokens, expected - css_tokens)
        self.assertEqual(metadata["attributes"].get("data-syn-color-space"), ["oklch"])

    def test_documentation_explains_explicit_theme_scope_and_no_compiler(self):
        docs = source("docs/theme-customization.md")
        for phrase in ("--syn-grid-min", "syn-filter-bar", "data-syn-color-space",
                       "Nested themes", "no build step", "accessibility"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, docs)


if __name__ == "__main__":
    unittest.main()
