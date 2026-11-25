"""Contract for optional JavaScript animation distribution (CSS remains JS-free)."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AnimationDistribution(unittest.TestCase):
    def test_independent_source_distribution_and_no_core_dependency(self):
        from scripts.build import javascript_distributions, all_distributions
        self.assertEqual({key: javascript_distributions()[key] for key in ('syntyr.animate.mjs', 'syntyr.animate.d.mts')}, {'syntyr.animate.mjs': 'animate.mjs', 'syntyr.animate.d.mts': 'animate.d.mts'})
        self.assertNotIn('syntyr.animate.mjs', all_distributions())
        self.assertIn('syntyr.animate.d.mts', javascript_distributions())
        self.assertEqual((ROOT / 'src/animate.mjs').read_bytes(),
                         (ROOT / 'dist/syntyr.animate.mjs').read_bytes())
        self.assertEqual((ROOT / 'src/animate.d.mts').read_bytes(),
                         (ROOT / 'dist/syntyr.animate.d.mts').read_bytes())
        import json
        package = json.loads((ROOT / 'package.json').read_text())
        self.assertEqual(package['exports']['./animate'], {
            'types': './dist/syntyr.animate.d.mts',
            'default': './dist/syntyr.animate.mjs',
        })
        self.assertNotIn('animate.mjs', (ROOT / 'dist/syntyr.core.css').read_text())

    def test_animation_is_allowlisted_in_release_and_static_site(self):
        from scripts.package_release import FILES
        from scripts.build_cloudflare_site import source_files
        self.assertIn('dist/syntyr.animate.mjs', FILES)
        self.assertIn('docs/animation.md', FILES)
        self.assertIn('examples/animation.html', FILES)
        self.assertIn('examples/animation-demo.mjs', FILES)
        files = source_files()
        self.assertEqual(files['dist/syntyr.animate.mjs'],
                         (ROOT / 'src/animate.mjs').read_bytes())
        self.assertIn('docs/animation.md', files)
        self.assertIn('examples/animation.html', files)
        self.assertIn('examples/animation-demo.mjs', files)

    def test_build_check_detects_outdated_js_artifact(self):
        proc = subprocess.run([sys.executable, 'scripts/build.py', '--check'],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('OK syntyr.animate.mjs', proc.stdout)

    def test_native_js_behavior_is_checked_in_existing_node_ci(self):
        self.assertIn('node --test tests/animate.test.mjs',
                      (ROOT / '.woodpecker/js-adoption.yaml').read_text())

    def test_agent_index_lists_opt_in_animation_guide(self):
        index = (ROOT / 'llms.txt').read_text()
        self.assertIn('https://syntyr-css.pages.dev/docs/animation.md', index)
        self.assertIn('unreleased alpha.5', index)

    def test_readme_describes_opt_in_native_motion_companion(self):
        docs = (ROOT / 'docs/animation.md').read_text()
        for term in ('syntyr.animate.mjs', 'animate(', 'stagger(',
                     'observeReveals(', 'prefers-reduced-motion', '.syn-root',
                     'IntersectionObserver', 'Web Animations API'):
            self.assertIn(term, docs)


if __name__ == '__main__':
    unittest.main()
