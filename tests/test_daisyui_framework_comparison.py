"""The optional CSS comparison uses genuine daisyUI rather than a mock."""
import importlib.util
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(file):
    spec = importlib.util.spec_from_file_location(file.stem, file)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class DaisyBenchmarkContractTests(unittest.TestCase):
    def test_daisyui_has_same_content_and_document_structure_as_syntyr(self):
        tool = module(ROOT / 'scripts/perf_framework_fixtures.py')
        self.assertIn('daisyui', tool.FRAMEWORKS)
        for name in tool.FIXTURES:
            reference = tool.make_page('syntyr', name, rows=4)
            page = tool.make_page('daisyui', name, rows=4)
            self.assertEqual(tool.structural_signature(page), tool.structural_signature(reference))
            self.assertIn('class="btn btn-primary"', page)
            self.assertIn('href="../daisyui.css"', page)
            self.assertNotIn('<script', page)

    def test_daisyui_requires_compiled_real_css(self):
        tool = module(ROOT / 'scripts/perf_framework_fixtures.py')
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            with self.assertRaises(FileNotFoundError):
                tool.prepare_css('daisyui', directory)
            compiled = directory / 'daisyui.compiled.css'
            compiled.write_text('/* built by actual daisyUI Tailwind plugin */ .btn{display:inline-flex}')
            result = tool.prepare_css('daisyui', directory)
            self.assertIn('.btn{display:inline-flex}', result.read_text())

    def test_daisyui_compiler_is_pinned_and_benchmark_only(self):
        import json
        nested = ROOT / 'benchmarks/frameworks'
        manifest = json.loads((nested / 'package.json').read_text())
        self.assertEqual(manifest['devDependencies']['daisyui'], '5.8.0')
        self.assertIn('daisyui.input.css', manifest['scripts']['build'])
        self.assertIn('@plugin "daisyui"', (nested / 'daisyui.input.css').read_text())
        core = json.loads((ROOT / 'package.json').read_text())
        self.assertNotIn('daisyui', core.get('dependencies', {}))
        self.assertNotIn('daisyui', core.get('devDependencies', {}))

    def test_markup_size_metrics_count_literal_class_tokens(self):
        tool = module(ROOT / 'scripts/perf_framework_compare.py')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'example.html'
            path.write_text('<div class="btn btn-primary"><span class="btn">OK</span></div>')
            metrics = tool.markup_stats(path)
            self.assertEqual(metrics['html_bytes'], len(path.read_bytes()))
            self.assertEqual(metrics['class_tokens'], 3)
            self.assertEqual(metrics['distinct_class_tokens'], 2)
            self.assertGreater(metrics['class_attribute_bytes'], 0)

    def test_browser_harness_recognizes_daisyui(self):
        tool = module(ROOT / 'scripts/perf_framework_compare.py')
        self.assertIn('daisyui', tool.FRAMEWORKS)
        tool.validate_selection(['syntyr', 'tailwind', 'daisyui'], ['chromium'], ['mobile'], 2)


if __name__ == '__main__':
    unittest.main()
