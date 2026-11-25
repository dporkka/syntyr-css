"""Optional clipboard helper is independently distributable, not part of CSS runtime."""
from pathlib import Path
import json
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClipboardDistribution(unittest.TestCase):
    def test_copy_module_and_types_are_published_independently(self):
        from scripts.build import javascript_distributions, all_distributions
        js = javascript_distributions()
        self.assertEqual(js['syntyr.copy.mjs'], 'copy.mjs')
        self.assertEqual(js['syntyr.copy.d.mts'], 'copy.d.mts')
        self.assertNotIn('syntyr.copy.mjs', all_distributions())
        for compiled, source in (('syntyr.copy.mjs', 'copy.mjs'), ('syntyr.copy.d.mts', 'copy.d.mts')):
            self.assertEqual((ROOT / 'dist' / compiled).read_bytes(),
                             (ROOT / 'src' / source).read_bytes())
        exports = json.loads((ROOT / 'package.json').read_text())['exports']
        self.assertEqual(exports['./copy'], {
            'types': './dist/syntyr.copy.d.mts',
            'default': './dist/syntyr.copy.mjs',
        })
        for filename in ('syntyr.core.css', 'syntyr.all.css', 'syntyr.semantic.css'):
            css = (ROOT / 'dist' / filename).read_text()
            self.assertNotIn('copy.mjs', css)
            self.assertNotIn('data-syn-copy-target', css)

    def test_only_opt_in_allowlisted_assets_are_shipped(self):
        from scripts.package_release import FILES
        from scripts.build_cloudflare_site import source_files
        for name in ('dist/syntyr.copy.mjs', 'dist/syntyr.copy.d.mts',
                     'docs/clipboard.md', 'examples/copy.html', 'examples/copy-demo.mjs'):
            with self.subTest(name=name):
                self.assertIn(name, FILES)
                self.assertIn(name, source_files())
        self.assertIn('docs/clipboard.html', source_files())
        self.assertIn('clipboard.html', (ROOT / 'docs/index.html').read_text())
        self.assertIn('docs/clipboard.md', (ROOT / 'README.md').read_text())
        guide = (ROOT / 'docs/clipboard.md').read_text()
        self.assertIn("from '/js/syntyr.copy.mjs'", guide)
        self.assertIn("from '@syntyr/css/copy'", guide)

    def test_demo_retains_useful_no_script_content_and_announcement(self):
        html = (ROOT / 'examples/copy.html').read_text()
        self.assertIn('<code id="copy-source">npm install @syntyr/css</code>', html)
        self.assertIn('type="button" hidden', html)
        self.assertIn('[data-syn-copy-target][hidden] { display: none; }', html)
        self.assertIn('role="status" aria-live="polite"', html)
        self.assertIn('data-syn-copy-target="copy-source"', html)
        self.assertIn('data-syn-copy-status="copy-status"', html)
        self.assertIn('type="module" src="copy-demo.mjs"', html)
        self.assertNotIn('http://', html)
        self.assertNotIn('https://', html)

    def test_python_only_quality_gate_does_not_require_node(self):
        import os
        import sys
        # The production quality job runs Python without a Node executable.
        env = {**os.environ, "PATH": "/nonexistent"}
        proc = subprocess.run([
            sys.executable, "-m", "unittest", "discover", "-s", "tests",
            "-p", "test_copy_distribution.py", "-k",
            "test_existing_js_ci_runs_native_clipboard_tests", "-q",
        ], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_existing_js_ci_runs_native_clipboard_tests(self):
        config = (ROOT / '.woodpecker/js-adoption.yaml').read_text()
        self.assertIn('node --test tests/animate.test.mjs tests/copy.test.mjs', config)
        # Native JavaScript tests run in the optional Node CI job, not the
        # Python-only quality gate.


if __name__ == '__main__':
    unittest.main()
