"""Fair, reproducible static checks for independent AI-generated UI outputs."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'scripts/benchmark_agent_markup.py'


def load():
    spec = importlib.util.spec_from_file_location('benchmark_agent_markup', PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MANIFEST = {'schema_version': 1, 'frameworks': ['syntyr', 'tailwind', 'daisyui'],
            'cases': [{'id': 'account', 'required_tags': ['form', 'input', 'label', 'button'],
                       'required_text': ['Account settings', 'Email']}]}

VALID = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Account settings</title>
<link rel="stylesheet" href="/{framework}.css"></head><body>
<main {css}><h1>Account settings</h1><form action="/profile" method="post">
<label for="email">Email</label><input id="email" name="email" type="email" required>
<button type="submit">Save</button></form></main></body></html>'''


class AgentOutputBenchmarkTests(unittest.TestCase):
    def test_task_manifest_has_ten_distinct_structured_prompts(self):
        tool = load()
        manifest = tool.load_manifest(ROOT / 'benchmarks/agent-output/tasks.json')
        self.assertEqual(len(manifest['cases']), 10)
        self.assertEqual(len({c['id'] for c in manifest['cases']}), 10)
        self.assertEqual(manifest['frameworks'], ['syntyr', 'tailwind', 'daisyui'])

    def test_complete_submission_reports_real_source_metrics_without_token_guesses(self):
        tool = load()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for framework in MANIFEST['frameworks']:
                file = root / 'account' / (framework + '.html')
                file.parent.mkdir(parents=True, exist_ok=True)
                css = 'class="syn-root"' if framework == 'syntyr' else ''
                file.write_text(VALID.format(framework=framework, css=css))
            report = tool.evaluate(root, MANIFEST)
            self.assertTrue(report['complete'])
            self.assertEqual(report['missing_outputs'], [])
            self.assertEqual(len(report['results']), 3)
            self.assertTrue(all(r['findings'] == [] for r in report['results']))
            self.assertTrue(all(r['html_bytes'] > 0 for r in report['results']))
            self.assertNotIn('estimated_tokens', report['results'][0])
            self.assertFalse(report['comparable'])  # no provenance declared

    def test_invalid_controls_are_identified_but_not_claimed_as_wcag_audit(self):
        tool = load()
        page = ('<!doctype html><html><body><main><h1>Account settings</h1>'
                '<form><input id="email" type="email"><button>Save</button>'
                '<a href="#">Email</a><script>bad()</script></form></main></body></html>')
        findings = tool.inspect_html(page, MANIFEST['cases'][0], 'tailwind')
        codes = {f['code'] for f in findings}
        self.assertGreaterEqual(len(codes), 5)
        self.assertIn('missing-label', codes)
        self.assertIn('missing-language', codes)
        self.assertIn('script-not-allowed', codes)
        self.assertIn('missing-form-action', codes)

    def test_incomplete_submission_is_not_ranked_as_a_winner(self):
        tool = load()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'account/syntyr.html'
            path.parent.mkdir()
            path.write_text(VALID.format(framework='syntyr', css='class="syn-root"'))
            report = tool.evaluate(root, MANIFEST)
            self.assertFalse(report['complete'])
            self.assertFalse(report['comparable'])
            self.assertEqual(len(report['missing_outputs']), 2)
            self.assertEqual(len(report['results']), 1)

    def test_syntyr_unknown_classes_use_existing_versioned_contract(self):
        tool = load()
        result = tool.inspect_html(VALID.format(framework='syntyr', css='class="syn-buttn"'),
                                   MANIFEST['cases'][0], 'syntyr')
        self.assertIn('syntyr-unknown-class', {f['code'] for f in result})

    def test_strict_cli_fails_when_submissions_are_missing(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, str(PATH), '--inputs', temp, '--strict'],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            import json
            report = json.loads(result.stdout)
            self.assertFalse(report['complete'])
            self.assertEqual(report['expected_outputs'], 30)
            self.assertEqual(len(report['missing_outputs']), 30)

    def test_manifest_rejects_duplicate_case_ids_and_unsafe_paths(self):
        tool = load()
        for name in ('../escape', 'a/b', 'a\\b'):
            bad = {**MANIFEST, 'cases': [{**MANIFEST['cases'][0], 'id': name}]}
            with self.assertRaises(ValueError):
                tool.validate_manifest(bad)


if __name__ == '__main__':
    unittest.main()
