"""Regression contracts for Syntyr's native-first enhancement boundaries."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProgressiveReliabilityTests(unittest.TestCase):
    def test_floating_labels_remain_real_pointer_targets(self):
        css = (ROOT / "src/native-recipes.css").read_text()
        label_rule = css.split("> .syn-floating-label {", 1)[1].split("}", 1)[0]
        self.assertNotIn("pointer-events: none", label_rule)
        self.assertIn("for=\"example-email\"", (ROOT / "examples/native-recipes.html").read_text())

    def test_critical_dialog_information_has_scriptless_disclosure(self):
        html = (ROOT / "examples/native-recipes.html").read_text()
        self.assertIn('command="show-modal"', html)
        self.assertIn('id="native-report-fallback"', html)
        self.assertIn("<details", html)
        self.assertIn("<summary>Read system report without a dialog</summary>", html)
        self.assertIn("System report", html)

    def test_htmx_failure_recovery_preserves_native_submission(self):
        html = (ROOT / "examples/htmx.html").read_text()
        recovery = (ROOT / "examples/htmx-recovery.js").read_text()
        self.assertIn('action="/customers/search" method="get"', html)
        self.assertIn('id="search-error"', html)
        self.assertIn('id="native-search-link"', html)
        self.assertIn('src="/examples/htmx-recovery.js"', html)
        for event in ("htmx:responseError", "htmx:sendError", "htmx:timeout", "htmx:beforeRequest", "htmx:afterSwap"):
            with self.subTest(event=event):
                self.assertIn(event, recovery)
        self.assertIn("URLSearchParams", recovery)
        self.assertNotIn("innerHTML", recovery)
        self.assertNotIn("eval(", recovery)
        self.assertNotIn("htmx-recovery.js", (ROOT / "src/server.css").read_text())

    def test_release_browser_pipeline_includes_progressive_regression(self):
        browser = (ROOT / ".woodpecker/browser.yaml").read_text()
        self.assertIn("tests/progressive_reliability_browser.py", browser)
        script = (ROOT / "tests/progressive_reliability_browser.py").read_text()
        self.assertIn("java_script_enabled=False", script)
        self.assertIn("document.activeElement", script)


if __name__ == "__main__":
    unittest.main()
