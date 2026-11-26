"""Standalone Expo starter export contracts (no Node or network required)."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export_native_starter.py"
FIXTURE = ROOT / "examples/expo-native-smoke"


class NativeStarterTest(unittest.TestCase):
    def export(self, destination):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--output", str(destination)],
            capture_output=True, text=True, timeout=30,
        )

    def test_exact_portable_manifest_and_canonical_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "starter"
            result = self.export(destination)
            self.assertEqual(result.returncode, 0, result.stderr)
            files = {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()}
            self.assertEqual(files, {
                ".gitignore", "LICENSE", "README.md", "index.ts", "tsconfig.json",
                "App.test.tsx", "OperationsScreen.test.tsx", "app.json", "package.json",
                "package-lock.json", "src/tokens.ts", "src/styles.ts", "src/recipes.tsx",
                "src/App.tsx", "src/OperationsScreen.tsx",
            })
            for name in ("tokens.ts", "styles.ts", "recipes.tsx"):
                self.assertEqual((destination / "src" / name).read_bytes(),
                                 (ROOT / "integrations/react-native" / name).read_bytes())
            for name in ("App.tsx", "OperationsScreen.tsx"):
                canonical = (ROOT / "examples/react-native" / name).read_text()
                self.assertEqual((destination / "src" / name).read_text(),
                                 canonical.replace("../../integrations/react-native/", "./"))
            for name in ("index.ts", "tsconfig.json", "App.test.tsx", "OperationsScreen.test.tsx"):
                self.assertEqual((destination / name).read_bytes(), (FIXTURE / name).read_bytes())
            self.assertNotIn("src/", (destination / ".gitignore").read_text().splitlines())
            self.assertEqual((destination / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())

    def test_lock_and_scripts_are_standalone(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "starter"
            self.assertEqual(self.export(destination).returncode, 0)
            package = json.loads((destination / "package.json").read_text())
            lock = json.loads((destination / "package-lock.json").read_text())
            fixture_lock = json.loads((FIXTURE / "package-lock.json").read_text())
            self.assertTrue(package["private"])
            self.assertEqual(package["name"], lock["name"])
            for key in ("name", "version", "dependencies", "devDependencies"):
                self.assertEqual(package[key], lock["packages"][""][key])
            fixture_lock["name"] = fixture_lock["packages"][""]["name"] = package["name"]
            self.assertEqual(lock, fixture_lock)
            self.assertEqual(set(package["scripts"]),
                             {"start", "android", "ios", "typecheck", "test", "export:android", "export:ios"})
            for command in package["scripts"].values():
                self.assertNotIn("sync", command)
                self.assertNotIn("../", command)
            for req in ("nativewind", "uniwind", "@syntyr/css"):
                self.assertNotIn(req, package["dependencies"])
            self.assertEqual(package["overrides"], json.loads((FIXTURE / "package.json").read_text())["overrides"])

    def test_legacy_probe_overlay_does_not_replace_canonical_sources(self):
        overlay = ROOT / "examples/native-sdk54-coexistence/overlay"
        self.assertEqual({p.relative_to(overlay).as_posix() for p in overlay.rglob("*") if p.is_file()}, {
            "package.json", "index.ts", "metro.config.js", "babel.config.js", "tailwind.config.js",
            "global.css", "nativewind-env.d.ts", "src/Host.tsx", "Host.test.tsx",
        })
        package = json.loads((overlay / "package.json").read_text())
        self.assertEqual(package["dependencies"]["expo"], "54.0.37")
        self.assertEqual(package["dependencies"]["react-native"], "0.81.5")
        self.assertEqual(package["dependencies"]["nativewind"], "4.2.3")
        self.assertEqual(package["devDependencies"]["tailwindcss"], "3.3.2")
        self.assertNotIn("@syntyr/css", package["dependencies"])
        self.assertIn('import App from "./App"', (overlay / "src/Host.tsx").read_text())
        self.assertIn("className=", (overlay / "src/Host.tsx").read_text())
        self.assertNotIn("@theme", (overlay / "global.css").read_text())

    def test_repeatable_contents_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / "one", Path(temp) / "two"
            for destination in (first, second):
                self.assertEqual(self.export(destination).returncode, 0)
            for path in first.rglob("*"):
                if path.is_file():
                    self.assertEqual(path.read_bytes(), (second / path.relative_to(first)).read_bytes())
            marker = first / "mine.txt"
            marker.write_text("unchanged")
            result = self.export(first)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), "unchanged")

    def test_rejects_missing_parent_and_dangling_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            self.assertNotEqual(self.export(parent / "missing" / "starter").returncode, 0)
            self.assertFalse((parent / "missing").exists())
            link = parent / "link"
            try:
                link.symlink_to(parent / "not-created", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation not supported")
            self.assertNotEqual(self.export(link).returncode, 0)
            self.assertTrue(link.is_symlink())
            self.assertFalse((parent / "not-created").exists())


if __name__ == "__main__":
    unittest.main()
