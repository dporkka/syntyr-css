"""Optional inspector bridge: no default executable discovery or release ambiguity."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent_mcp.catalog import CANDIDATE, PUBLISHED, CatalogError
from agent_mcp.html_inspector import inspect_markup

ROOT = Path(__file__).resolve().parents[1]

class InspectorBoundaryTests(unittest.TestCase):
    def test_requires_explicit_candidate_release(self):
        with self.assertRaisesRegex(CatalogError, "candidate"):
            inspect_markup("<p>Test</p>", PUBLISHED)

    def test_missing_configuration_is_actionable(self):
        with patch.dict(os.environ, {"SYNTYR_HTML_INSPECTOR": ""}):
            with self.assertRaisesRegex(CatalogError, "SYNTYR_HTML_INSPECTOR"):
                inspect_markup("<p>Test</p>", CANDIDATE)

    def test_rejects_oversized_input_and_selector_before_execution(self):
        with self.assertRaisesRegex(CatalogError, "HTML"):
            inspect_markup("x" * 20001, CANDIDATE)
        with self.assertRaisesRegex(CatalogError, "selector"):
            inspect_markup("<p>Test</p>", CANDIDATE, "x" * 257)

@unittest.skipUnless(os.environ.get("SYNTYR_HTML_INSPECTOR"), "Build optional Go inspector and configure executable to run integration")
class InspectorIntegrationTests(unittest.TestCase):
    def test_real_inspector_and_bounded_output(self):
        result = inspect_markup('<button class="syn-button">Go</button>' * 41, CANDIDATE, "button")
        self.assertEqual(result["release"], CANDIDATE)
        self.assertEqual(len(result["elements"]), 40)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["elements"][0]["components"], ["Button"])

    def test_exact_limit_is_not_truncated(self):
        result = inspect_markup('<button class="syn-button">Go</button>' * 40, CANDIDATE)
        self.assertEqual(len(result["elements"]), 40)
        self.assertFalse(result["truncated"])

    def test_bad_selector_errors(self):
        with self.assertRaises(CatalogError):
            inspect_markup("<p>Test</p>", CANDIDATE, "[")

    def test_cli_inspects_local_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_text('<div class="syn-app-shell"></div>', encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "scripts/syntyr_agent.py"),
                "inspect-html", "--release", CANDIDATE, str(path)], cwd=directory,
                text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["elements"][0]["recipes"][0]["slots"][0]["status"], "missing")
