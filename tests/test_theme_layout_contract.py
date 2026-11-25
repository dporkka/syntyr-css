"""Keep the common spacing layout contract documented and distributed."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ThemeLayoutContract(unittest.TestCase):
    def test_layout_tokens_are_palette_independent_and_in_distribution(self):
        tokens = (ROOT / 'src/tokens.css').read_text()
        bundle = (ROOT / 'dist/syntyr.core.css').read_text()
        for role in ('--syn-page-gutter', '--syn-content-max', '--syn-section-space',
                     '--syn-content-gap', '--syn-panel-padding-default'):
            with self.subTest(role=role):
                self.assertIn(role + ':', tokens)
                self.assertIn(role + ':', bundle)

    def test_stack_and_density_styles_remain_scoped_to_syntyr(self):
        layout = (ROOT / 'src/components/layout.css').read_text()
        utilities = (ROOT / 'src/utilities.css').read_text()
        tokens = (ROOT / 'src/tokens.css').read_text()
        self.assertIn('&.syn-stack > :nth-child(n)', layout)
        self.assertIn('.syn-root :where(.syn-u-stack > *)', utilities)
        for density in ('compact', 'comfortable', 'spacious'):
            self.assertIn(f'data-syn-density="{density}"', tokens)
        self.assertEqual(tokens.count('--syn-panel-padding-default:'), 4)

    def test_composition_rules_are_not_forked_per_theme(self):
        layout = (ROOT / 'src/components/layout.css').read_text()
        recipes = (ROOT / 'src/recipes.css').read_text()
        for role in ('--syn-page-gutter', '--syn-content-max', '--syn-content-gap'):
            self.assertIn(role, layout + recipes)
        for role in ('--syn-site-heading-measure', '--syn-section-space'):
            self.assertIn(role, recipes)
        for name in ('grid', 'noir', 'studio', 'industrial', 'terminal', 'corporate', 'minimal'):
            self.assertNotIn(f'data-syn-theme="{name}"', layout)


if __name__ == '__main__':
    unittest.main()
