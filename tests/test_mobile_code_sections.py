"""Regression for reusable keyboard-scrollable code examples in static pages."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MobileCodeSectionsTests(unittest.TestCase):
    def test_api_reference_code_previews_are_keyboard_scrollable(self):
        snippet = (ROOT / 'blocks/snippets/api-endpoint-reference.html').read_text()
        self.assertEqual(snippet.count('<pre'), 2)
        self.assertEqual(snippet.count('class="syn-code-scroll"'), 2)
        self.assertEqual(snippet.count('tabindex="0"'), 2)
        self.assertIn('aria-label="Example API request"', snippet)
        self.assertIn('aria-label="Example JSON response"', snippet)
        css = (ROOT / 'src/components/data.css').read_text()
        self.assertIn('&.syn-code-scroll', css)
        self.assertIn('overflow-x: auto', css)
        self.assertIn('max-inline-size: 100%', css)

if __name__ == "__main__":
    unittest.main()
