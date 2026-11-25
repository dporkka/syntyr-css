"""CI should gate releases without adding a consumer-side dependency."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def active_workflow_command_position(source: str, command: str) -> int:
    """Find a real list entry, excluding commented-out Woodpecker steps."""
    match = re.search(r"(?m)^[ \t]*-[ \t]+" + re.escape(command) + r"[ \t]*$", source)
    return match.start() if match else -1


class ContinuousIntegrationContract(unittest.TestCase):
    def test_pull_requests_and_main_pushes_run_standard_library_gates(self):
        workflow = ROOT / ".woodpecker" / "quality.yaml"
        self.assertTrue(workflow.is_file(), "A PR quality workflow is required")
        content = workflow.read_text(encoding="utf-8")
        for contract in (
            "event: pull_request",
            "event: push",
            "branch: main",
            "python:3.14-slim",
            "python3 scripts/build.py --check",
            "python3 -m unittest discover -s tests -v",
            "python3 scripts/build_cloudflare_site.py",
            "python3 scripts/build_cloudflare_site.py --check",
            "python3 scripts/package_release.py",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, content)

    def test_framework_adoption_builds_are_path_scoped_without_skipping_quality(self):
        # Keep the workflow/status present, but skip npm steps for unrelated PRs.
        workflow = (ROOT / ".woodpecker/js-adoption.yaml").read_text()
        self.assertIn("event: pull_request", workflow)
        self.assertIn("event: push", workflow)
        self.assertIn("branch: main", workflow)
        step = workflow.split("- name: node-jsx-tsx-consumers", 1)[1]
        self.assertIn("when:", step)
        self.assertIn("event: manual", step)
        self.assertIn("event: [pull_request, push]", step)
        self.assertIn("path:", step)
        self.assertIn("on_empty: true", step)
        for relevant in (
            "src/**", "dist/**", "package.json", "packages/react/**",
            "examples/react-vite/**", "examples/next-app-router/**",
            "examples/node-express/**", "examples/preact-jsx/**",
            "examples/solid-tsx/**", "tests/animate.test.mjs", "integrations/**",
            ".woodpecker/js-adoption.yaml",
        ):
            with self.subTest(path=relevant):
                self.assertIn(relevant, step)
        # Never path-gate the universal stdlib and release browser workflows.
        self.assertNotIn("path:", (ROOT / ".woodpecker/quality.yaml").read_text())
        self.assertNotIn("path:", (ROOT / ".woodpecker/browser.yaml").read_text())

    def test_quality_runner_installs_git_before_git_tracking_tests(self):
        # Python slim has no Git CLI. Several brand/distribution tests use
        # git ls-files, so the CI image must supply Git before running them.
        content = (ROOT / ".woodpecker" / "quality.yaml").read_text()
        install = "apt-get install -y --no-install-recommends git"
        self.assertIn("apt-get update", content)
        self.assertIn(install, content)
        self.assertIn("git --version", content)
        self.assertLess(content.index(install), content.index("python3 -m unittest discover"))

    def test_maintainer_docs_dependency_is_installed_before_ci_tests(self):
        # CI's Python package index is blocked; use the Debian package available
        # to the pinned Python 3.14 image without changing the shipped CSS.
        install = (
            "apt-get update && apt-get install -y --no-install-recommends "
            "git python3-markdown-it && rm -rf /var/lib/apt/lists/*"
        )
        verify_version = (
            """python3 -c 'from importlib.metadata import version; """
            """assert version("markdown-it-py") == "3.0.0"'"""
        )
        for path, runner in (
            (".woodpecker/quality.yaml", "python3 -m unittest discover -s tests -v"),
            (".woodpecker/pr-merge.yaml", "python3 scripts/check_merge_candidate.py --base FETCH_HEAD"),
        ):
            with self.subTest(workflow=path):
                content = (ROOT / path).read_text()
                install_at = active_workflow_command_position(content, install)
                version_at = active_workflow_command_position(content, verify_version)
                runner_at = active_workflow_command_position(content, runner)
                self.assertGreaterEqual(install_at, 0, "Package install must be an active step")
                self.assertGreaterEqual(version_at, 0, "Version pin check must be active")
                self.assertGreaterEqual(runner_at, 0, "Test gate must be active")
                self.assertLess(install_at, version_at)
                self.assertLess(version_at, runner_at)
                self.assertIn("\n      PYTHONPATH: /usr/lib/python3/dist-packages\n", content)
                self.assertNotIn("pip install", content)
                self.assertEqual(active_workflow_command_position(
                    content.replace("      - " + install, "      # - " + install), install
                ), -1, "Commented-out installation must not satisfy the contract")

    def test_commented_blocks_command_is_not_an_active_release_step(self):
        command = "python3 tests/blocks_browser.py --browsers chromium firefox webkit"
        self.assertEqual(active_workflow_command_position("#      - " + command, command), -1)
        self.assertEqual(active_workflow_command_position("      # - " + command, command), -1)
        self.assertGreaterEqual(active_workflow_command_position("      - " + command, command), 0)

    def test_blocks_gallery_is_in_three_engine_release_browser_gate(self):
        workflow = (ROOT / ".woodpecker" / "browser.yaml").read_text(encoding="utf-8")
        blocks = active_workflow_command_position(
            workflow, "python3 tests/blocks_browser.py --browsers chromium firefox webkit")
        matrix = active_workflow_command_position(
            workflow, "python3 tests/browser_matrix.py --browsers chromium firefox webkit")
        self.assertGreaterEqual(blocks, 0, "Blocks browser test must be an active workflow step")
        self.assertGreaterEqual(matrix, 0, "Browser matrix must be an active workflow step")
        self.assertIn("event: manual", workflow)
        self.assertIn("event: tag", workflow)
        self.assertLess(matrix, blocks)

    def test_published_reflow_matrix_is_an_active_three_engine_release_gate(self):
        script = (ROOT / "tests" / "published_reflow_browser.py").read_text()
        self.assertIn("from scripts.build_cloudflare_site import source_files", script)
        self.assertIn("VIEWPORTS", script)
        self.assertIn("SYNTYR_WEBKIT_EXECUTABLE", script)
        workflow = (ROOT / ".woodpecker" / "browser.yaml").read_text()
        command = "python3 tests/published_reflow_browser.py --browsers chromium firefox webkit"
        self.assertGreaterEqual(active_workflow_command_position(workflow, command), 0)
        self.assertLess(
            active_workflow_command_position(workflow, "python3 tests/reflow_test.py --browsers chromium firefox webkit"),
            active_workflow_command_position(workflow, command),
        )

    def test_release_browser_matrix_is_explicit_and_not_a_runtime_dependency(self):
        workflow = ROOT / ".woodpecker" / "browser.yaml"
        self.assertTrue(workflow.is_file(), "Require a reproducible release browser workflow")
        content = workflow.read_text(encoding="utf-8")
        for contract in (
            "event: manual",
            "event: tag",
            "playwright/python:v1.65.2-noble",
            "python3 tests/browser_matrix.py --browsers chromium firefox webkit",
            "python3 tests/reflow_test.py --browsers chromium firefox webkit",
            "python3 tests/theme_editor_browser.py",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, content)


if __name__ == "__main__":
    unittest.main()
