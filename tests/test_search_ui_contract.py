"""Search presentation must stay accessible and dependency-free."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SearchUIContract(unittest.TestCase):
    def test_documentation_search_has_separate_result_count_and_copy_status(self):
        for prefix in ("catalog", "blocks"):
            with self.subTest(prefix=prefix):
                html = (ROOT / f"docs/{prefix}.html").read_text()
                js = (ROOT / f"docs/{prefix}.js").read_text()
                self.assertIn(f'id="{prefix}-results"', html)
                self.assertIn(f'id="{prefix}-feedback"', html)
                self.assertIn(f'getElementById("{prefix}-feedback")', js)
                self.assertIn("feedback.textContent", js)
                self.assertNotIn("results.textContent = 'HTML", js)
                self.assertNotIn('results.textContent = "HTML', js)
                self.assertEqual(js.count('results.textContent ='), 1)

    def test_catalog_browser_checks_count_from_actual_cards(self):
        browser = (ROOT / "tests/catalog_browser.js").read_text()
        self.assertIn("const total =", browser)
        self.assertNotIn(".count(), 10", browser)
        self.assertIn("#catalog-feedback", browser)

    def test_search_input_can_resist_long_submit_labels(self):
        css = (ROOT / "src/components/form-composition.css").read_text()
        self.assertIn("min-inline-size: min(100%, 9rem)", css)
        self.assertIn("&.syn-input-group > .syn-button", css)
        self.assertIn("max-inline-size: 100%", css)

    def test_premium_example_uses_native_search_without_false_navigation_state(self):
        page = (ROOT / "examples/premium-compositions.html").read_text()
        self.assertIn('<search aria-label="Search sample actions">', page)
        self.assertNotIn('<search role="search"', page)
        self.assertNotIn('class="syn-command-row" aria-current="true"', page)

    def test_search_recipes_explain_truthful_results_and_optional_behavior(self):
        doc = (ROOT / "docs/component-recipes.md").read_text()
        for term in ("Result counts", "IME composition", "server", "No JavaScript", "RTL"):
            self.assertIn(term, doc)


if __name__ == "__main__":
    unittest.main()
