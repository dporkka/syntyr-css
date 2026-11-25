"""SaaS parity benchmark: source/behavior contracts; no third-party test dependencies."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/perf_saas_parity.py"


def load():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("perf_saas_parity", MODULE)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    return tool


class SaaSParityContract(unittest.TestCase):
    def test_all_four_variants_identical_semantic_structure_and_content(self):
        tool = load()
        from sys import path
        path.insert(0, str(ROOT / "scripts"))
        from perf_framework_fixtures import structural_signature
        pages = [tool.render_html(f, query="customer 001", rows=32) for f in tool.FRAMEWORKS]
        self.assertTrue(all(structural_signature(page) == structural_signature(pages[0])
                            for page in pages))
        for page in pages:
            self.assertIn('method="get"', page)
            self.assertIn('name="q"', page)
            self.assertIn('aria-live="polite"', page)
            self.assertIn('scope="col"', page)
            self.assertNotIn("<script", page)
            self.assertNotIn('href="https://', page)
        self.assertEqual(len(tool.FRAMEWORKS), 4)

    def test_filter_is_case_insensitive_with_empty_and_no_results(self):
        tool = load()
        self.assertEqual(len(tool.filtered_rows("", 32)), 32)
        self.assertEqual([r["customer"] for r in tool.filtered_rows("CUSTOMER 0004", 32)],
                         ["Customer 0004"])
        self.assertEqual(tool.filtered_rows("no-such-customer", 32), [])
        self.assertEqual(tool.filtered_rows("   ", 32), tool.filtered_rows("", 32))

    def test_server_side_get_filter_and_safe_user_query(self):
        tool = load()
        with tool.local_parity_server(rows=32) as base:
            for framework in tool.FRAMEWORKS:
                with urlopen(f"{base}/{framework}/saas.html?q=Customer%200004") as response:
                    html = response.read().decode()
                    self.assertEqual(response.status, 200)
                self.assertIn("1 of 32", html)
                self.assertIn("Customer 0004", html)
                self.assertNotIn("Customer 0005", html)
                with urlopen(f"{base}/{framework}/saas.html?q=%3Cscript%3E") as response:
                    html = response.read().decode()
                self.assertNotIn('<script>', html)

    def test_missing_or_unknown_routes_do_not_render_dashboard(self):
        tool = load()
        with tool.local_parity_server(rows=12) as base:
            from urllib.error import HTTPError
            with self.assertRaises(HTTPError) as error:
                urlopen(f"{base}/invalid/saas.html")
            self.assertEqual(error.exception.code, 404)
            error.exception.close()

    def test_setup_generation_and_metrics_do_not_require_runtime_deps(self):
        tool = load()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated = tool.generate_pages(root, rows=20)
            self.assertEqual(len(generated), 4)
            for framework in tool.FRAMEWORKS:
                page = root / framework / "saas.html"
                self.assertTrue(page.is_file())
                self.assertEqual(page.read_text(), tool.render_html(framework, rows=20))
            report = tool.productivity_metrics(root, rows=20)
            self.assertEqual(set(report), set(tool.FRAMEWORKS))
            self.assertTrue(all(report[f]["class_attribute_bytes"] >= 0 for f in report))
            self.assertTrue(all(report[f]["human_authoring_minutes"] is None for f in report))

    def test_visual_gate_does_not_pass_when_reference_is_missing(self):
        tool = load()
        findings = tool.visual_deviations({"plain": {}, "syntyr": {}})
        self.assertTrue(findings)
        self.assertEqual(findings[0]["issue"], "reference missing")

    def test_generated_html_must_match_requested_row_count(self):
        tool = load()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            tool.generate_pages(output, rows=20)
            for name in tool.FRAMEWORKS:
                (output / f"{name}.css").write_text("/* controlled fixture */")
            with self.assertRaisesRegex(ValueError, "stale"):
                tool.benchmark(output, rows=21, runs=1, browsers=["chromium"],
                               viewports=["mobile"], axe_script=None, screenshots=None)

    def test_empty_framework_css_is_rejected_before_benchmark(self):
        tool = load()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool.generate_pages(root, rows=8)
            for name in tool.FRAMEWORKS:
                (root / f"{name}.css").write_text("/* fixture */")
            (root / "syntyr.css").write_text("")
            with self.assertRaisesRegex(ValueError, "empty|zero"):
                tool.benchmark(root, rows=8, runs=1, browsers=["chromium"],
                               viewports=["mobile"], axe_script=None, screenshots=None)

    def test_zero_row_visual_gate_requires_only_present_anchors(self):
        tool = load()
        metrics = {"width": 900, "height": 80, "background": "rgb(0, 0, 0)", "font": "16px"}
        base = {name: metrics.copy() for name in ("header", "metrics", "search")}
        variants = {f: base.copy() for f in tool.FRAMEWORKS}
        self.assertEqual(tool.visual_deviations(variants, required=("header", "metrics", "search")), [])
        self.assertTrue(tool.visual_deviations(variants))  # A nonempty fixture still needs a table.
        self.assertEqual(tool.visual_anchors_for_rows(0), ("header", "metrics", "search"))
        self.assertEqual(tool.visual_anchors_for_rows(5), tool.ANCHORS)

    def test_browser_parity_verifies_customer_and_campaign_content(self):
        tool = load()
        code = MODULE.read_text(encoding="utf8")
        self.assertIn('to_contain_text("Customer 0004")', code)
        self.assertIn('to_contain_text("Campaign 0004")', code)
        for framework in tool.FRAMEWORKS:
            html = tool.render_html(framework, query="Customer 0004", rows=12)
            self.assertIn("Customer 0004", html)
            self.assertIn("Campaign 0004", html)
            self.assertNotIn("Customer 0005", html)

    def test_input_fingerprints_cover_lock_and_fixture_sources(self):
        tool = load()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            tool.generate_pages(output, rows=20)
            manifest = tool.input_fingerprints(output)
            self.assertEqual(len(manifest["html_sha256"]), 4)
            self.assertEqual(len(manifest["calibration_sha256"]), 64)
            self.assertEqual(len(manifest["compiler_lock_sha256"]), 64)

    def test_optional_webkit_wrapper_is_never_required_for_other_engines(self):
        tool = load()
        wrapper = Path("/tmp/browser-wrapper")
        self.assertEqual(tool.browser_launch_options("webkit", wrapper),
                         {"executable_path": str(wrapper)})
        self.assertEqual(tool.browser_launch_options("chromium", wrapper), {})
        self.assertEqual(tool.browser_launch_options("firefox", wrapper), {})
        self.assertEqual(tool.browser_launch_options("webkit", None), {})

    def test_accessibility_incomplete_is_not_clean(self):
        tool = load()
        self.assertFalse(tool.accessibility_clean({"status": "not-run"}))
        self.assertFalse(tool.accessibility_clean({
            "status": "executed", "violations": [], "incomplete": [{"id": "color-contrast"}]
        }))
        self.assertFalse(tool.accessibility_clean({
            "status": "executed", "violations": [{"id": "label"}], "incomplete": []
        }))
        self.assertTrue(tool.accessibility_clean({
            "status": "executed", "violations": [], "incomplete": []
        }))

    def test_visual_gate_rejects_missing_and_misaligned_style_metrics(self):
        tool = load()
        reference = {"width": 900, "height": 80, "background": "rgb(0, 0, 0)",
                     "font": "16px"}
        base = {"plain": {role: reference.copy() for role in tool.ANCHORS}}
        actual = {**base, "syntyr": {role: reference.copy() for role in tool.ANCHORS}}
        self.assertEqual(tool.visual_deviations(actual, reference="plain", tolerance=.05), [])
        actual["syntyr"]["header"]["width"] = 800
        self.assertEqual(tool.visual_deviations(actual, reference="plain",
                                                 tolerance=.05)[0]["property"], "width")
        del actual["syntyr"]["header"]
        self.assertEqual(tool.visual_deviations(actual, reference="plain",
                                                 tolerance=.05)[0]["issue"], "missing anchor")

    def test_framework_benchmark_lockfile_picomatch_advisory_bounded_to_devtools(self):
        """GHSA-fc5q-39xc-vjpf / CVE-2026-112366 originally reported picomatch <= 4.0.7 ReDoS
        (withdrawn by GitHub on November 18, 2026).

        Assert benchmarks/frameworks is private dev-only tooling, does not leak
        into root package.json or production CSS, and has picomatch pinned to 4.0.7.
        """
        bench_dir = ROOT / "benchmarks/frameworks"
        pkg = json.loads((bench_dir / "package.json").read_text())
        self.assertTrue(pkg.get("private"), "Framework benchmark package must remain private")
        self.assertIn("dev-only benchmark compilers", pkg.get("description", ""))

        # Verify no benchmark dependencies leak into root package.json
        root_pkg = json.loads((ROOT / "package.json").read_text())
        for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            self.assertNotIn("picomatch", root_pkg.get(key, {}))
            for dep in pkg.get("devDependencies", {}):
                self.assertNotIn(dep, root_pkg.get(key, {}))

        # Lockfile integrity: verify picomatch instances are dev-only and pinned to upstream 4.0.7
        lock = json.loads((bench_dir / "package-lock.json").read_text())
        picomatch_versions = []
        for name, meta in lock.get("packages", {}).items():
            if name.endswith("node_modules/picomatch"):
                picomatch_versions.append((name, meta.get("version"), meta.get("dev", False)))

        self.assertTrue(picomatch_versions, "picomatch should be tracked in benchmark lockfile")
        for name, version, is_dev in picomatch_versions:
            self.assertTrue(is_dev, f"{name} must be marked as dev dependency")
            self.assertEqual(version, "4.0.7", f"picomatch must be pinned to 4.0.7 (latest upstream), got {version}")


if __name__ == "__main__":
    unittest.main()
