"""MCP validation must reuse the version-pinned CLI diagnostic contract."""
import unittest
from agent_mcp.catalog import SyntyrCatalog, CatalogError


class AgentMcpValidatorBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = SyntyrCatalog()

    def test_unknown_class_returns_structured_repair_hints_from_release(self):
        result = self.catalog.validate_markup('<button class="syn-buttn">Save</button>',
                                              '0.3.0-alpha.4', ['syntyr.core.css'])
        self.assertEqual(result['unknown_classes'], ['syn-buttn'])
        diag = next(d for d in result['diagnostics'] if d['code'] == 'unknown-class')
        self.assertEqual((diag['line'], diag['column']), (1, 1))
        suggestion = next(s for s in diag['suggestions'] if s['name'] == 'syn-button')
        self.assertEqual(suggestion['stylesheets'], ['syntyr.all.css', 'syntyr.core.css', 'syntyr.css'])

    def test_candidate_only_classes_never_appear_in_published_suggestions(self):
        result = self.catalog.validate_markup('<div class="syn-field"></div>',
                                              '0.3.0-alpha.4', ['syntyr.core.css'])
        self.assertEqual(result['unknown_classes'], ['syn-field'])
        self.assertFalse(any(s['name'] == 'syn-field'
                             for d in result['diagnostics'] for s in d.get('suggestions', [])))
        candidate = self.catalog.validate_markup('<div class="syn-field"></div>',
                                                 '0.3.0-alpha.5', ['syntyr.core.css'])
        self.assertEqual(candidate['unknown_classes'], [])

    def test_published_theme_validation_does_not_approve_unreleased_themes(self):
        pub = self.catalog.validate_markup('<main data-syn-theme="industrial"></main>',
                                           '0.3.0-alpha.4')
        self.assertEqual(pub['diagnostics'][0]['code'], 'invalid-attribute-value')
        self.assertEqual(pub['diagnostics'][0]['allowed_values'], ['grid', 'noir', 'studio'])
        candidate = self.catalog.validate_markup('<main data-syn-theme="industrial"></main>',
                                                 '0.3.0-alpha.5')
        self.assertEqual(candidate['diagnostics'], [])

    def test_explicit_missing_stylesheet_yields_actionable_diagnostic(self):
        result = self.catalog.validate_markup('<main class="syn-root syn-app-shell"></main>',
                                              '0.3.0-alpha.4', ['syntyr.core.css'])
        diag = next(d for d in result['diagnostics'] if d['code'] == 'missing-stylesheet')
        self.assertIn('syntyr.recipes.css', diag['required_stylesheets'])
        self.assertEqual(diag['loaded_stylesheets'], ['syntyr.core.css'])
        self.assertIn('syntyr.recipes.css', result['missing_stylesheets'])

    def test_detect_linked_stylesheets_and_skip_unrendered_templates(self):
        result = self.catalog.validate_markup('''<link rel="stylesheet" href="/dist/syntyr.core.css?v=1">
          <div class="{{ syn-imaginary }}"></div>
          <button class="syn-button">Go</button>''', '0.3.0-alpha.4')
        self.assertEqual(result['unknown_classes'], [])
        self.assertEqual(result['classes_checked'], ['syn-button'])
        self.assertEqual(result['installed_stylesheets'], ['syntyr.core.css'])
        self.assertEqual(result['diagnostics'], [])

    def test_candidate_accepts_css_defined_loading_selected_and_viz_states(self):
        for name in ('active', 'loading', 'selected', 'healthy', 'degraded', 'down', 'unknown'):
            result = self.catalog.validate_markup(
                f'<main data-syn-state="{name}" class="syn-root"></main>',
                '0.3.0-alpha.5', ['syntyr.all.css'])
            self.assertFalse(any(d['code'] == 'invalid-attribute-value'
                                 for d in result['diagnostics']), name)
        invalid = self.catalog.validate_markup('<main data-syn-state="imaginary"></main>',
                                               '0.3.0-alpha.5')
        self.assertIn('invalid-attribute-value', [d['code'] for d in invalid['diagnostics']])

    def test_candidate_semantic_bundle_is_recognized_as_css_provider(self):
        html = ('''<link rel="stylesheet" href="/dist/syntyr.semantic-bundle.css">'''
                '<main class="syn-root syn-semantic"><button>Save</button></main>')
        result = self.catalog.validate_markup(html, '0.3.0-alpha.5')
        self.assertEqual(result['installed_stylesheets'], ['syntyr.semantic-bundle.css'])
        self.assertEqual([d['code'] for d in result['diagnostics']], [])

    def test_explicit_empty_stylesheets_has_diagnostics_but_omission_does_not(self):
        html = '<button class="syn-button">Go</button>'
        explicitly_empty = self.catalog.validate_markup(html, '0.3.0-alpha.4', [])
        self.assertIn('missing-stylesheet', [d['code'] for d in explicitly_empty['diagnostics']])
        unknown = self.catalog.validate_markup(html, '0.3.0-alpha.4')
        self.assertEqual(unknown['diagnostics'], [])

    def test_explicit_sheet_overrides_links_and_rejects_unpublished_modules(self):
        result = self.catalog.validate_markup('''<link rel="stylesheet" href="syntyr.recipes.css">
             <button class="syn-button"></button>''', '0.3.0-alpha.4', ['syntyr.core.css'])
        self.assertEqual(result['installed_stylesheets'], ['syntyr.core.css'])
        self.assertEqual(result['diagnostics'], [])
        with self.assertRaisesRegex(CatalogError, 'Unknown stylesheet'):
            self.catalog.validate_markup('<main></main>', '0.3.0-alpha.4', ['syntyr.native-recipes.css'])


if __name__ == '__main__':
    unittest.main()
