"""Contracts for the optional framework comparison harness (stdlib only)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "scripts/perf_framework_fixtures.py"
BENCH = ROOT / "scripts/perf_framework_compare.py"


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FrameworkFixturesTest(unittest.TestCase):
    def test_all_six_variants_have_identical_semantic_dom_and_content(self):
        tool = load(FIXTURES)
        for fixture in ("dashboard", "marketing"):
            pages = [tool.make_page(framework, fixture, rows=32)
                     for framework in tool.FRAMEWORKS]
            signatures = [tool.structural_signature(page) for page in pages]
            self.assertTrue(all(sig == signatures[0] for sig in signatures))
            self.assertIn("<main", pages[0])
            self.assertIn("<form", pages[0])
            self.assertIn("<button", pages[0])
            self.assertNotIn("<script", pages[0])
            for page in pages:
                self.assertNotIn('src="https://', page)
                self.assertNotIn('href="https://', page)
                self.assertEqual(page.count('data-bench-anchor='), pages[0].count('data-bench-anchor='))

    def test_generation_is_deterministic_and_rejects_bad_input(self):
        tool = load(FIXTURES)
        html = tool.make_page("syntyr", "dashboard", rows=12)
        self.assertEqual(html, tool.make_page("syntyr", "dashboard", rows=12))
        for framework, fixture, rows in (("unknown", "dashboard", 10),
                                         ("plain", "unknown", 10),
                                         ("plain", "marketing", -1)):
            with self.assertRaises(ValueError):
                tool.make_page(framework, fixture, rows=rows)

    def test_css_bundle_requires_real_framework_artifacts(self):
        tool = load(FIXTURES)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                tool.prepare_css("tailwind", Path(tmp), ROOT)
            with self.assertRaises(FileNotFoundError):
                tool.prepare_css("uno", Path(tmp), ROOT)

    def test_structural_signature_rejects_missing_stylesheet(self):
        tool = load(FIXTURES)
        page = tool.make_page("plain", "marketing", rows=5)
        self.assertIn('href="../plain.css"', page)
        changed = page.replace("Available now", "Unavailable")
        self.assertNotEqual(tool.structural_signature(page), tool.structural_signature(changed))


class FrameworkCompareTest(unittest.TestCase):
    def test_statistics_report_median_p75_and_unavailable_as_null(self):
        tool = load(BENCH)
        self.assertEqual(tool.metric_stats([{"fcp_ms": 20}, {"fcp_ms": 30},
                                            {"fcp_ms": 40}, {"fcp_ms": 90}], "fcp_ms"),
                         {"median": 35.0, "p75": 40, "samples": 4})
        self.assertEqual(tool.metric_stats([{"fcp_ms": None}], "fcp_ms"),
                         {"median": None, "p75": None, "samples": 0})

    def test_rotated_trial_order_and_duplicate_validation(self):
        tool = load(BENCH)
        self.assertEqual(tool.trial_order(["a", "b", "c"], 1), ["b", "c", "a"])
        with self.assertRaises(ValueError):
            tool.validate_selection(["syntyr", "syntyr"], ["chromium"], ["mobile"], 10)
        with self.assertRaises(ValueError):
            tool.validate_selection(["syntyr"], ["webkit", "invalid"], ["mobile"], 10)
        with self.assertRaises(ValueError):
            tool.validate_selection(["syntyr"], ["chromium"], ["mobile"], 0)

    def test_report_does_not_conflate_transfer_size_with_gzip(self):
        tool = load(BENCH)
        with tempfile.TemporaryDirectory() as tmp:
            css = Path(tmp) / "sample.css"
            css.write_text(".x { color: red; }\n", encoding="utf8")
            sizes = tool.css_sizes(css)
            self.assertEqual(sizes["raw_bytes"], len(css.read_bytes()))
            self.assertGreater(sizes["gzip_bytes"], 0)
            self.assertIn("brotli_bytes", sizes)
            self.assertNotIn("transfer_bytes", sizes)


class FrameworkParityTest(unittest.TestCase):
    def test_unequal_table_geometry_is_flagged_not_silently_ranked(self):
        tool = load(BENCH)
        anchors = {
            "plain": {"table": {"width": 600, "height": 6000},
                      "header": {"width": 600, "height": 100}},
            "syntyr": {"table": {"width": 600, "height": 6100},
                       "header": {"width": 600, "height": 105}},
            "uno": {"table": {"width": 600, "height": 2900},
                    "header": {"width": 600, "height": 100}},
        }
        warnings = tool.geometry_warnings(anchors, reference="plain", tolerance=0.2)
        self.assertTrue(any(w["framework"] == "uno" and w["anchor"] == "table"
                            for w in warnings))
        self.assertFalse(any(w["framework"] == "syntyr" for w in warnings))

    def test_uno_output_includes_relevant_preflight_reset(self):
        tool = load(FIXTURES)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated = root / "benchmarks/frameworks/generated"
            generated.mkdir(parents=True)
            (generated / "uno.compiled.css").write_text(".grid{display:grid}", encoding="utf8")
            reset = root / "benchmarks/frameworks/node_modules/@unocss/reset/tailwind.css"
            reset.parent.mkdir(parents=True)
            reset.write_text("/* preflight reset */ body{margin:0}", encoding="utf8")
            css = tool.prepare_css("uno", generated, root).read_text(encoding="utf8")
            self.assertIn("/* preflight reset */", css)
            self.assertIn(".grid{display:grid}", css)


if __name__ == "__main__":
    unittest.main()
