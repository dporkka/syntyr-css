"""Contract tests for Syntyr's opt-in Expo native integration smoke fixture."""
import json
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/expo-native-smoke"


class ExpoNativeSmokeTest(unittest.TestCase):
    def test_fixture_uses_official_expo_sdk_with_no_native_core_dependency(self):
        package = json.loads((FIXTURE / "package.json").read_text())
        self.assertTrue(package["private"])
        self.assertTrue(package["dependencies"]["expo"].startswith("~58."))
        self.assertTrue(package["dependencies"]["react-native"].startswith("0.88."))
        for name in ("sync", "typecheck", "test", "export:android", "export:ios"):
            self.assertIn(name, package["scripts"])
        core = json.loads((ROOT / "package.json").read_text())
        self.assertNotIn("expo", core.get("dependencies", {}))
        self.assertNotIn("react-native", core.get("dependencies", {}))
        self.assertNotIn("jest", core.get("devDependencies", {}))

    def test_expo_lock_avoids_minimatch_globparts_dos_range(self):
        """GHSA-g3hv-75wg-m249 affects minimatch 7.x through 11.0.0."""
        package = json.loads((FIXTURE / "package.json").read_text())
        lock = json.loads((FIXTURE / "package-lock.json").read_text())
        self.assertIn("minimatch", package.get("overrides", {}),
                      "Pin an explicitly vetted minimatch override for Expo tooling")
        affected = []
        for name, meta in lock["packages"].items():
            if not name.endswith("/node_modules/minimatch") and name != "node_modules/minimatch":
                continue
            version = tuple(int(n) for n in meta["version"].split(".")[:3])
            if (7, 0, 0) <= version < (11, 0, 1):
                affected.append((name, meta["version"]))
        self.assertEqual(affected, [], f"GHSA-g3hv-75wg-m249 in lock: {affected}")

    @unittest.skipUnless(shutil.which("node"), "Node is optional; Expo sync requires Node")
    def test_source_sync_reuses_exact_canonical_adapter(self):
        with tempfile.TemporaryDirectory() as temp:
            node = shutil.which("node")
            self.assertIsNotNone(node)
            result = subprocess.run(
                [node, str(FIXTURE / "scripts/sync-adapter.mjs"), "--output", temp],
                cwd=FIXTURE, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            target = Path(temp)
            for file in ("tokens.ts", "styles.ts", "recipes.tsx"):
                self.assertEqual(
                    (target / file).read_bytes(),
                    (ROOT / "integrations/react-native" / file).read_bytes(),
                )
            for name in ("App.tsx", "OperationsScreen.tsx"):
                source = (ROOT / "examples/react-native" / name).read_text()
                rewritten = source.replace("../../integrations/react-native/", "./")
                self.assertEqual((target / name).read_text(), rewritten)

    def test_python_only_checkout_runs_core_contract_checks_without_node_or_git(self):
        # The optional Expo test must not break the Python-only Syntyr core suite.
        with tempfile.TemporaryDirectory() as empty_path:
            env = dict(os.environ, PATH=empty_path)
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_expo_native_smoke.py", "-v",
                 "-k", "test_source_sync_reuses_exact_canonical_adapter",
                 "-k", "test_fixture_has_native_interaction_tests_and_platform_exports",
                 "-k", "test_fixture_uses_official_expo_sdk_with_no_native_core_dependency"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("skipped", result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is optional; bundle report requires Node")
    def test_bundle_size_report_counts_only_platform_bundles_and_rejects_mixed_formats(self):
        script = FIXTURE / "scripts/report-bundle-size.mjs"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for label, files in (("baseline", {"index.hbc": b"abc"}), ("other", {"index.hbc": b"12345", "split.hbc": b"6"})):
                folder = root / label / "_expo/static/js/android"
                folder.mkdir(parents=True)
                for name, payload in files.items():
                    (folder / name).write_bytes(payload)
                (folder / "metadata.json").write_text("{}")
            args = [shutil.which("node"), str(script), "android",
                    f"baseline={root / 'baseline'}", f"other={root / 'other'}"]
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["metric"], "raw-production-js-bundle-bytes")
            self.assertEqual([case["bytes"] for case in data["cases"]], [3, 6])
            self.assertEqual(data["cases"][1]["deltaPercent"], 100)
            (root / "other/_expo/static/js/android/extra.js").write_text("export {}")
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mixed bundle formats", result.stderr)

    def test_fixture_has_native_interaction_tests_and_platform_exports(self):
        test = (FIXTURE / "App.test.tsx").read_text()
        for fragment in ("fireEvent.press", "fireEvent.changeText", "getByLabelText",
                         "getByRole", "Submitted 1 time(s)"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, test)
        package = json.loads((FIXTURE / "package.json").read_text())
        self.assertIn("--platform android", package["scripts"]["export:android"])
        self.assertIn("--platform ios", package["scripts"]["export:ios"])
        self.assertTrue((FIXTURE / "package-lock.json").is_file())
        # Verify npm ci's committed lock contract without requiring Git or Node
        # in Syntyr's Python-only quality gate.
        lock = json.loads((FIXTURE / "package-lock.json").read_text())
        self.assertGreaterEqual(lock["lockfileVersion"], 3)
        self.assertEqual(lock["packages"][""]["dependencies"], package["dependencies"])
        self.assertEqual(lock["packages"][""]["devDependencies"], package["devDependencies"])
        self.assertTrue((FIXTURE / "tsconfig.json").is_file())
        self.assertTrue((FIXTURE / "index.ts").is_file())
        self.assertTrue((FIXTURE / "README.md").is_file())
        self.assertTrue((FIXTURE / ".gitignore").is_file())


if __name__ == "__main__":
    unittest.main()
