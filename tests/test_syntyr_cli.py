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

    def test_show_outputs_exact_canonical_html_for_pipes(self):
        gallery = json.loads((ROOT / "metadata/component-gallery.v1.json").read_text())
        example = next(x for x in gallery["examples"] if x["id"] == "catalog-buttons-title")
        result = self.run_cli("show", example["id"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, example["html"] + "\n")
        self.assertIn("source", result.stderr.lower())
        self.assertIn("0.3.0-alpha.4", result.stderr)
        checked = self.run_cli("check", "-", "--format", "json", payload=result.stdout)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_show_json_labels_source_and_target_and_preserves_requirements(self):
        gallery = json.loads((ROOT / "metadata/component-gallery.v1.json").read_text())
        example = next(x for x in gallery["examples"] if x["id"] == "catalog-buttons-title")
        result = self.run_cli("show", example["id"], "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["source_version"], gallery["source_version"])
        self.assertEqual(report["release"], "0.3.0-alpha.4")
        self.assertEqual(report["release_status"], "published")
        self.assertEqual(report["example"]["html"], example["html"])
        self.assertEqual(report["example"]["required_stylesheets"], example["required_stylesheets"])
        self.assertEqual(result.stderr, "")

    def test_show_rejects_candidate_only_and_unknown_examples_by_default(self):
        for name in ("catalog-breadcrumbs-title", "../README.md", "missing-example"):
            with self.subTest(name=name):
                result = self.run_cli("show", name, "--format", "json")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn(name, result.stderr)
        result = self.run_cli("show", "catalog-breadcrumbs-title", "--release",
                              "0.3.0-alpha.5", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["release_status"], "unreleased_candidate")

    def test_deps_uses_same_release_checked_requirements_as_show(self):
        name = "catalog-buttons-title"
        shown = self.run_cli("show", name, "--format", "json")
        expected = json.loads(shown.stdout)
        result = self.run_cli("deps", name, "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["release"], expected["release"])
        self.assertEqual(report["source_version"], expected["source_version"])
        self.assertEqual(report["required_stylesheets"], expected["example"]["required_stylesheets"])
        self.assertEqual(report["native_feature_requirements"], expected["example"]["native_feature_requirements"])
        self.assertNotIn("html", report)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, self.run_cli("deps", name, "--format", "json").stdout)

    def test_deps_text_is_ordered_stylesheet_filter(self):
        result = self.run_cli("deps", "catalog-buttons-title")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["syntyr.core.css"])
        self.assertIn("0.3.0-alpha.4", result.stderr)
        self.assertIn("host", result.stderr.lower())

    def test_deps_rejects_unavailable_and_unknown_examples_without_output(self):
        for name in ("catalog-breadcrumbs-title", "../README.md"):
            with self.subTest(name=name):
                result = self.run_cli("deps", name, "--format", "json")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn(name, result.stderr)
        result = self.run_cli("deps", "catalog-breadcrumbs-title", "--release",
                              "0.3.0-alpha.5", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["release_status"], "unreleased_candidate")

    def test_doctor_delegates_exact_validator_contract_for_piped_html(self):
        html = ('<link rel="stylesheet" href="/v/0.3.0-alpha.4/syntyr.core.css">'
                '<link rel="stylesheet" href="/v/0.3.0-alpha.5/syntyr.recipes.css">')
        direct = self.run_cli("check", "--doctor", "-", "--format", "json", payload=html)
        result = self.run_cli("doctor", "-", "--format", "json", payload=html)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.returncode, direct.returncode)
        self.assertEqual(result.stdout, direct.stdout)
        self.assertEqual(json.loads(result.stdout)[0]["code"], "mixed-stylesheet-versions")

    def test_doctor_tokens_preserves_advisory_status_for_inert_links(self):
        html = ('<link rel="stylesheet" href="syntyr.recipes.css">'
                '<template><link rel="stylesheet" href="syntyr.core.css"></template>'
                '<div style="gap:var(--syn-space-2)"></div>')
        result = self.run_cli("doctor", "--tokens", "-", "--format", "json", payload=html)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([d["code"] for d in json.loads(result.stdout)], ["missing-token-stylesheet"])

    def test_help_and_invalid_command(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("version", "check", "diff", "info", "project-check", "search", "man", "show", "deps", "doctor"):
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
