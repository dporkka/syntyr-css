"""Real Blades and Bulma fixtures without consumer dependencies or fake CSS."""
import importlib.util
from pathlib import Path
import json
import hashlib
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / 'scripts' / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BladesBulmaBenchmarkTest(unittest.TestCase):
    def test_frameworks_have_identical_semantic_dom_without_runtime_js(self):
        generator = load('perf_framework_fixtures.py')
        runner = load('perf_framework_compare.py')
        for framework in ('blades', 'bulma'):
            self.assertIn(framework, generator.FRAMEWORKS)
            self.assertIn(framework, runner.FRAMEWORKS)
            runner.validate_selection(['syntyr', framework], ['chromium'], ['mobile'], 2)
            for fixture in generator.FIXTURES:
                expected = generator.structural_signature(generator.make_page('syntyr', fixture, rows=5))
                html = generator.make_page(framework, fixture, rows=5)
                self.assertEqual(expected, generator.structural_signature(html))
                self.assertIn(f'href="../{framework}.css"', html)
                self.assertNotIn('<script', html)
                self.assertNotIn('https://', html)

    def test_vendor_css_is_required_and_styles_are_not_substituted(self):
        generator = load('perf_framework_fixtures.py')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'benchmarks/frameworks/generated'
            packages = {
                'blades': 'node_modules/@anyblades/blades/css/blades.min.css',
                'bulma': 'node_modules/bulma/css/bulma.min.css',
            }
            for framework, relative in packages.items():
                with self.assertRaises(FileNotFoundError):
                    generator.prepare_css(framework, output, root)
                vendor = root / 'benchmarks/frameworks' / relative
                vendor.parent.mkdir(parents=True, exist_ok=True)
                vendor.write_text('/* GENUINE VENDOR FIXTURE */ .vendor{color:red}', encoding='utf8')
                stylesheet = generator.prepare_css(framework, output, root).read_text(encoding='utf8')
                self.assertIn('/* GENUINE VENDOR FIXTURE */', stylesheet)
                self.assertIn('benchmark adapter', stylesheet)
                self.assertNotEqual(stylesheet, generator.BASE_CSS)

    def test_run_provenance_tracks_commit_lock_and_dirty_state(self):
        runner = load('perf_framework_compare.py')
        actual = runner.benchmark_provenance(ROOT)
        expected_sha = subprocess.check_output(
            ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
        expected_lock = hashlib.sha256(
            (ROOT / 'benchmarks/frameworks/package-lock.json').read_bytes()
        ).hexdigest()
        self.assertEqual(actual['git_revision'], expected_sha)
        self.assertEqual(actual['benchmark_lock_sha256'], expected_lock)
        self.assertIsInstance(actual['working_tree_dirty'], bool)
        self.assertEqual(actual['vendor_versions']['blades'], '3.1.3')
        self.assertEqual(actual['vendor_versions']['bulma'], '1.0.4')

    def test_framework_packages_are_pinned_and_dev_only(self):
        bench = json.loads((ROOT / 'benchmarks/frameworks/package.json').read_text())
        self.assertEqual(bench['devDependencies']['@anyblades/blades'], '3.1.3')
        self.assertEqual(bench['devDependencies']['bulma'], '1.0.4')
        main = json.loads((ROOT / 'package.json').read_text())
        for dependency in ('@anyblades/blades', 'bulma'):
            self.assertNotIn(dependency, main.get('dependencies', {}))
            self.assertNotIn(dependency, main.get('devDependencies', {}))


if __name__ == '__main__':
    unittest.main()
