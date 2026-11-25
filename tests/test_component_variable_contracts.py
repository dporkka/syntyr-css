"""Public prerelease component variables and server-supplied form states."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ComponentVariableContracts(unittest.TestCase):
    def test_button_variants_expose_consistent_local_customization(self):
        css = (ROOT / "src/components/buttons.css").read_text()
        for token in ("--syn-button-bg", "--syn-button-color", "--syn-button-border-color",
                      "--syn-button-hover-bg", "--syn-button-hover-border-color"):
            with self.subTest(token=token):
                self.assertGreater(css.count("var(" + token + ","), 0)
        for kind in ("--primary", "--outline", "--danger", "--ghost"):
            self.assertIn("&.syn-button" + kind, css)
        self.assertIn("background: var(--syn-button-hover-bg, var(--syn-accent-soft)); border-color: var(--syn-button-hover-border-color, var(--syn-frame));", css)
        self.assertNotIn("!important", css)

    def test_outline_and_danger_hover_allow_border_overrides(self):
        css = (ROOT / "src/components/buttons.css").read_text()
        for variant in ("outline", "danger"):
            with self.subTest(variant=variant):
                line = next(line for line in css.splitlines()
                            if f"&.syn-button--{variant}:where(" in line and ":hover" in line)
                self.assertIn("--syn-button-hover-border-color", line)

    def test_panels_expose_surface_color_border_variables(self):
        css = (ROOT / "src/components/layout.css").read_text()
        for token in ("--syn-panel-bg", "--syn-panel-color", "--syn-panel-border-color"):
            self.assertIn("var(" + token + ",", css)

    def test_form_controls_and_summary_have_explicit_states(self):
        css = (ROOT / "src/components/forms.css").read_text()
        for token in ("--syn-field-bg", "--syn-field-color", "--syn-field-border-color",
                      "--syn-field-invalid-border-color", "--syn-field-valid-border-color"):
            self.assertIn("var(" + token + ",", css)
        self.assertIn(':user-invalid', css)
        self.assertIn(':user-valid', css)
        self.assertIn('data-syn-validation="valid"', css)
        self.assertIn('aria-invalid="true"', css)
        self.assertIn('&.syn-error-summary', (ROOT / "src/recipes.css").read_text())
        self.assertIn('forced-colors: active', css)
        self.assertNotIn('!important', css)

    def test_examples_document_server_owned_state_and_aria(self):
        example = (ROOT / "examples/form-state-contracts.html").read_text()
        self.assertIn('role="alert"', example)
        self.assertIn('aria-describedby="account-help account-error"', example)
        self.assertIn('aria-invalid="true"', example)
        self.assertIn('data-syn-validation="valid"', example)
        self.assertIn('type="submit"', example)
        self.assertNotIn("<script", example)
        docs = (ROOT / "docs/component-recipes.md").read_text()
        self.assertIn("--syn-field-valid-border-color", docs)
        self.assertIn("--syn-button-bg", docs)
        self.assertIn("data-syn-validation", docs)


if __name__ == "__main__":
    unittest.main()
