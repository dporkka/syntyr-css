"""Regression checks for reproducible, actionable axe manual-review reports."""
import unittest
from tests import axe_audit as MODULE


class AuditReportingTests(unittest.TestCase):
    def test_normalizes_incomplete_nodes_with_selectors_and_summaries(self):
        data = {
            'violations': [],
            'incomplete': [{
                'id': 'color-contrast', 'impact': 'serious',
                'help': 'Elements must have sufficient color contrast',
                'nodes': [
                    {'target': ['.syn-root', 'a'], 'html': '<a>Read more</a>',
                     'failureSummary': 'Needs review', 'any': [], 'all': []},
                    {'target': ['.syn-panel'], 'html': '<div>Text</div>',
                     'failureSummary': None},
                ],
            }],
        }
        normalized = MODULE.normalize_findings('examples/themes.html', data)
        self.assertEqual(len(normalized['violations']), 0)
        self.assertEqual(len(normalized['incomplete']), 2)
        first = normalized['incomplete'][0]
        self.assertEqual(first['page'], 'examples/themes.html')
        self.assertEqual(first['rule'], 'color-contrast')
        self.assertEqual(first['selector'], ['.syn-root', 'a'])
        self.assertEqual(first['failure_summary'], 'Needs review')
        self.assertEqual(first['html'], '<a>Read more</a>')
        self.assertEqual(first['impact'], 'serious')

    def test_reports_confirmed_violations_separately(self):
        normalized = MODULE.normalize_findings('index.html', {
            'incomplete': [],
            'violations': [{'id': 'image-alt', 'impact': 'critical', 'help': 'Alternate text',
                            'nodes': [{'target': ['img'], 'html': '<img>', 'failureSummary': 'Missing alt'}]}],
        })
        self.assertEqual(len(normalized['violations']), 1)
        self.assertEqual(normalized['violations'][0]['rule'], 'image-alt')
        self.assertEqual(normalized['incomplete'], [])

    def test_summarizes_incomplete_nodes_not_just_incomplete_rules(self):
        pages = [
            {'page': 'a.html', 'violations': [], 'incomplete': [
                {'rule': 'color-contrast', 'selector': ['.a'],
                 'failure_summary': 'Background gradient'},
                {'rule': 'color-contrast', 'selector': ['.b'],
                 'failure_summary': 'Pseudo element'},
            ]},
            {'page': 'b.html', 'violations': [
                {'rule': 'image-alt', 'selector': ['img']},
            ], 'incomplete': [
                {'rule': 'color-contrast', 'selector': ['.c'],
                 'failure_summary': 'Background gradient'},
            ]},
        ]
        summary = MODULE.summarize_findings(pages)
        self.assertEqual(summary['pages'], 2)
        self.assertEqual(summary['confirmed_violation_nodes'], 1)
        self.assertEqual(summary['incomplete_nodes'], 3)
        self.assertEqual(summary['incomplete_rules'], {'color-contrast': 3})
        self.assertEqual(summary['incomplete_by_page'], {'a.html': 2, 'b.html': 1})


if __name__ == '__main__':
    unittest.main()
