"""Scoped native-form regression coverage complementing merged native input styling."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class BladesNativeFollowup(unittest.TestCase):
    def test_label_first_and_narrow_fallback(self):
        css = (ROOT / "src/native-recipes.css").read_text()
        self.assertIn("syn-field--floating:has(", css)
        self.assertIn(":not(:placeholder-shown)", css)
        self.assertIn("@container syn-floating-field (max-width: 21rem)", css)

    def test_invalid_semantic_file_upload_has_border(self):
        css = (ROOT / "src/semantic.css").read_text()
        self.assertIn('input[type="file"]:not([class])', css)
        self.assertIn('input[type="file"][data-syn-semantic]', css)
        self.assertIn('border: 1px solid var(--syn-danger)', css)

    def test_search_clear_space_in_both_modes(self):
        self.assertIn('&.syn-input[type="search"]', (ROOT / "src/components/forms.css").read_text())
        self.assertIn('input[type="search"]:not([class])', (ROOT / "src/semantic.css").read_text())
        self.assertIn("padding-inline-end: 2.25rem", (ROOT / "src/semantic.css").read_text())

    def test_demo_preserves_native_labels(self):
        html = (ROOT / "examples/native-recipes.html").read_text()
        for marker in ('id="example-organization"', 'for="example-organization"',
                       'id="native-file-invalid"', 'aria-invalid="true"', 'syntyr.semantic.css'):
            self.assertIn(marker, html)
        self.assertNotIn("<script", html.lower())

if __name__ == "__main__":
    unittest.main()
