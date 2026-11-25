"""Regression coverage for Syntyr's built-in semantic-color contract."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

from scripts import design_conformance

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/tokens.css"


class DesignConformanceTest(unittest.TestCase):
    def test_all_seven_named_palettes_pass_accessible_semantic_pairs(self):
        report = design_conformance.audit(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(set(report["palettes"]), {
            "studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal"
        })
        self.assertTrue(report["ok"], report["failures"])
        for palette in report["palettes"].values():
            roles = {check["role"] for check in palette["checks"]}
            self.assertIn("primary-action", roles)
            self.assertIn("muted-on-surface", roles)
            self.assertIn("focus-on-surface", roles)
            self.assertIn("strong-boundary", roles)
            self.assertGreaterEqual(len(roles), 10)

    def test_detects_low_contrast_primary_action_in_any_theme(self):
        css = SOURCE.read_text(encoding="utf-8").replace(
            "--syn-on-accent: #ffffff;",
            "--syn-on-accent: #2458c6;",
            1,
        )
        report = design_conformance.audit(css)
        self.assertFalse(report["ok"])
        self.assertTrue(any(
            issue["theme"] == "studio" and issue["role"] == "primary-action"
            for issue in report["failures"]
        ), report["failures"])

    def test_comment_cannot_mask_active_low_contrast_color(self):
        css = SOURCE.read_text(encoding="utf-8").replace(
            "--syn-on-accent: #ffffff;",
            "--syn-on-accent: #2458c6;\n"
            "/*\n"
            "  --syn-on-accent: #ffffff;\n"
            "*/",
            1,
        )
        report = design_conformance.audit(css)
        self.assertFalse(report["ok"], "commented token must not override active CSS")
        self.assertTrue(any(
            issue["theme"] == "studio" and issue["role"] == "primary-action"
            and issue["reason"] == "insufficient-contrast"
            for issue in report["failures"]
        ), report["failures"])

    def test_missing_semantic_token_is_failure_not_a_skipped_check(self):
        css = SOURCE.read_text(encoding="utf-8").replace("--syn-muted: #4b5d76;", "", 1)
        report = design_conformance.audit(css)
        self.assertFalse(report["ok"])
        self.assertTrue(any(
            issue["theme"] == "studio" and issue["role"] == "muted-on-surface"
            and issue["reason"] == "missing-token"
            for issue in report["failures"]
        ), report["failures"])

    def test_cli_json_uses_nonzero_exit_on_contrast_regression(self):
        css = SOURCE.read_text(encoding="utf-8").replace(
            "--syn-on-accent: #ffffff;", "--syn-on-accent: #2458c6;", 1
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "colors.css"
            source.write_text(css, encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(ROOT / "scripts/design_conformance.py"),
                 "--source", str(source), "--format", "json"],
                text=True, capture_output=True,
            )
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertFalse(json.loads(run.stdout)["ok"])

    def test_primary_hover_preserves_semantic_foreground(self):
        tokens = SOURCE.read_text(encoding="utf-8")
        buttons = (ROOT / "src/components/buttons.css").read_text(encoding="utf-8")
        self.assertIn("--syn-primary-hover-bg: var(--syn-accent);", tokens)
        self.assertIn("background: var(--syn-button-hover-bg, var(--syn-primary-hover-bg))", buttons)
        self.assertIn("color: var(--syn-button-hover-color, var(--syn-on-accent))", buttons)


if __name__ == "__main__":
    unittest.main()
