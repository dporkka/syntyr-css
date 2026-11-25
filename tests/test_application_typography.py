"""Additive application typography roles remain independent of theme and density."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ApplicationTypographyContract(unittest.TestCase):
    def test_public_roles_are_in_source_and_distribution(self):
        for file in ('src/components/typography.css', 'dist/syntyr.core.css'):
            text = (ROOT / file).read_text()
            for role in ('page-title', 'card-heading'):
                self.assertIn('.syn-' + role, text)
                self.assertIn('--syn-type-' + role, text)

    def test_opt_in_interface_profile_is_scoped(self):
        text = (ROOT / 'src/tokens.css').read_text()
        self.assertIn('.syn-root[data-syn-typography="application"]', text)
        self.assertIn('.syn-root [data-syn-typography="application"]', text)

    def test_examples_adopt_application_roles(self):
        for file in ('examples/saas.html', 'examples/crm.html'):
            text = (ROOT / file).read_text()
            self.assertIn('class="syn-page-title"', text)
            self.assertIn('class="syn-card-heading"', text)

if __name__ == '__main__':
    unittest.main()
