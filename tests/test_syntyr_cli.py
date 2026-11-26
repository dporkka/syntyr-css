import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "syntyr_cli.py"


class UnifiedCliTests(unittest.TestCase):
    def run_cli(self, *args, payload=None, cwd=None):
        return subprocess.run(
            [sys.executable, str(CLI), *args], input=payload,
            text=True, capture_output=True, cwd=cwd,
        )

    def test_version_distinguishes_candidate_and_published(self):
        result = self.run_cli("version", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        info = json.loads(result.stdout)
        self.assertEqual(info["source_version"], (ROOT / "VERSION").read_text().strip())
        from agent_mcp.catalog import PUBLISHED
        self.assertEqual(info["published_version"], PUBLISHED)

    def test_check_preserves_stdin_json_diagnostics_and_exit_status(self):
        result = self.run_cli("check", "-", "--format", "json",
                              payload='<div class="syn-not-a-real-class"></div>')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(json.loads(result.stdout))
        self.assertEqual(result.stderr, "")

    def test_diff_preserves_report_and_gate_mode(self):
        manifest = str(ROOT / "metadata" / "syntyr-contract.json")
        result = self.run_cli("diff", manifest, manifest, "--json", "--fail-on-breaking")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["breaking"])

    def test_info_is_read_only_and_preserves_uninitialized_status(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("info", "--project", directory, "--json", cwd=directory)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIsInstance(json.loads(result.stdout), dict)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_help_and_invalid_command(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("version", "check", "diff", "info", "project-check"):
            self.assertIn(name, result.stdout)
        result = self.run_cli("not-a-command")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)

    def test_project_check_preserves_pinned_project_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("project-check", "--project", directory, "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("error", json.loads(result.stdout))
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
