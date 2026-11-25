"""Legacy selector fallback: native chip inputs remain perceivable without :has()."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]

class FilterChoiceFallback(unittest.TestCase):
    def test_input_is_hidden_only_when_has_selector_is_supported(self):
        css = (ROOT / "src/components/patterns.css").read_text()
        start = css.index("&.syn-filter-choices > .syn-chip > input:is")
        end = css.index("&.syn-filter-choices > .syn-chip:has", start)
        block = css[start:end]
        self.assertIn("@supports selector(:has(", block)
        self.assertIn("opacity: 0", block)
        self.assertIn("pointer-events: none", block)
        self.assertIn("accent-color: var(--syn-accent)", block)
        self.assertIn("margin-inline-end: .375rem", block)
        before = block.split("@supports selector(:has(",1)[0]
        self.assertNotIn("opacity: 0", before)
        self.assertNotIn("pointer-events: none", before)

    def test_browser_example_uses_native_label_control(self):
        html = (ROOT / "examples/native-choice-filter-list.html").read_text()
        self.assertIn("syn-filter-choices", html)
        self.assertIn('type="radio"', html)
