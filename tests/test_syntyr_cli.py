import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "syntyr_cli.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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

    def test_search_defaults_to_published_and_filters_candidate_only_components(self):
        result = self.run_cli("search", "Content list", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        published = json.loads(result.stdout)
        self.assertEqual(published["release_status"], "published")
        self.assertEqual(published["components"], [])
        result = self.run_cli("search", "Content list", "--release",
                              "0.3.0-alpha.5", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        candidate = json.loads(result.stdout)
        self.assertEqual(candidate["release_status"], "unreleased_candidate")
        self.assertIn("Content list", [entry["name"] for entry in candidate["components"]])

    def test_man_describes_component_and_public_api_without_inventing_markup(self):
        for name, field in (("Button", "component"), ("syn-button", "entry"),
                            ("--syn-accent", "entry")):
            with self.subTest(name=name):
                result = self.run_cli("man", "--format", "json", "--", name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)[field]["name"], name)
        result = self.run_cli("man", "Button")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("syntyr.core.css", result.stdout)
        self.assertIn("syn-button", result.stdout)
        self.assertIn("0.3.0-alpha.4", result.stdout)

    def test_man_unavailable_name_reports_error_only_on_stderr(self):
        for name in ("Content list", "not-a-component"):
            with self.subTest(name=name):
                result = self.run_cli("man", name, "--format", "json")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn(name, result.stderr)

    def test_help_and_invalid_command(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("version", "check", "diff", "info", "project-check", "search", "man"):
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
