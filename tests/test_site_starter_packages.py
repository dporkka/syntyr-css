"""Deterministic candidate archives are distinct from an authorized release."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZIP_STORED, ZipFile

from scripts.export_site_starter import CORE, STARTER_ROUTES, check_starter
from scripts.package_site_starters import package_starters

ROOT = Path(__file__).resolve().parents[1]


class StarterPackageTests(unittest.TestCase):
    def test_four_versioned_archives_match_export_and_manifest(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, second = root / "one", root / "two"
            package_starters(first)
            package_starters(second)
            package_starters(first, check=True)
            manifest = json.loads((first / "manifest.json").read_text())
            version = (ROOT / "VERSION").read_text().strip()
            self.assertEqual(manifest["version"], version)
            self.assertEqual(manifest["format"], 1)
            self.assertEqual(set(manifest["packages"]), set(STARTER_ROUTES))
            self.assertEqual(len(list(first.iterdir())), 5)
            for name, info in manifest["packages"].items():
                with self.subTest(starter=name):
                    expected = f"syntyr-starter-{name}-{version}.zip"
                    self.assertEqual(info["filename"], expected)
                    archive_path = first / expected
                    data = archive_path.read_bytes()
                    self.assertEqual(data, (second / expected).read_bytes())
                    self.assertEqual(sha256(data).hexdigest(), info["sha256"])
                    self.assertEqual(len(data), info["bytes"])
                    with ZipFile(archive_path) as archive:
                        entries = sorted((*STARTER_ROUTES[name], "assets/site.css", "assets/syntyr.core.css", "LICENSE"))
                        self.assertEqual(archive.namelist(), entries)
                        self.assertEqual(set(info["files"]), set(entries))
                        for item in archive.infolist():
                            self.assertEqual(item.compress_type, ZIP_STORED)
                            self.assertEqual(item.date_time, (1980, 1, 1, 0, 0, 0))
                            self.assertEqual(item.external_attr >> 16, 0o100644)
                            self.assertEqual(sha256(archive.read(item)).hexdigest(), info["files"][item.filename])
                        archive.extractall(root / name)
                    check_starter(name, root / name)
            self.assertEqual((first / "manifest.json").read_bytes(), (second / "manifest.json").read_bytes())

    def test_check_rejects_tampered_or_unexpected_files_without_overwrite(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "packages"
            package_starters(output)
            manifest = output / "manifest.json"
            old = manifest.read_bytes()
            manifest.write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "differs"):
                package_starters(output, check=True)
            self.assertEqual(manifest.read_bytes(), b"{}")
            manifest.write_bytes(old)
            (output / "unexpected").write_text("not public")
            with self.assertRaisesRegex(ValueError, "inventory"):
                package_starters(output, check=True)
            with self.assertRaises(FileExistsError):
                package_starters(output)
            self.assertEqual((output / "unexpected").read_text(), "not public")

    def test_failure_leaves_no_partial_output(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "packages"
            with patch("scripts.package_site_starters.stage_starter", side_effect=ValueError("invalid site")):
                with self.assertRaisesRegex(ValueError, "invalid site"):
                    package_starters(output)
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])
            with patch("scripts.package_site_starters.subprocess.run", side_effect=subprocess.CalledProcessError(1, "build")):
                with self.assertRaises(subprocess.CalledProcessError):
                    package_starters(output)
            self.assertFalse(output.exists())

    def test_check_rejects_symlinked_archive_or_destination(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "packages"
            package_starters(output)
            alias = root / "alias"
            alias.symlink_to(output, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlinked"):
                package_starters(alias, check=True)
            archive = next(output.glob("*.zip"))
            target = root / "copy.zip"
            target.write_bytes(archive.read_bytes())
            archive.unlink()
            archive.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "differs"):
                package_starters(output, check=True)

    def test_symlinked_source_is_rejected_before_packaging(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            symlink = root / "core.css"
            symlink.symlink_to(CORE)
            output = root / "packages"
            with patch("scripts.export_site_starter.CORE", symlink):
                with self.assertRaisesRegex(ValueError, "symlinked starter input"):
                    package_starters(output)
            self.assertFalse(output.exists())

    def test_ci_uses_existing_locked_node_browser_and_read_only_package_verification(self):
        workflow = (ROOT / ".woodpecker/portable-starters.yaml").read_text()
        progressive = (ROOT / ".woodpecker/progressive.yaml").read_text()
        image = next(line.strip() for line in progressive.splitlines() if line.strip().startswith("image:"))
        self.assertIn(image, workflow)
        for entry in ("event: pull_request", "event: push", "event: manual", "event: tag",
                      "examples/site-starters/**", "npm ci --prefix examples/lit",
                      "      - node examples/lit/portable-starters-browser.mjs"):
            self.assertIn(entry, workflow)
        self.assertNotIn("pip install", workflow)
        quality = (ROOT / ".woodpecker/quality.yaml").read_text()
        package = "      - python3 scripts/package_site_starters.py --output /tmp/syntyr-starter-candidates"
        self.assertIn(package + "\n", quality)
        self.assertIn(package + " --check\n", quality)
        self.assertIn("      - python3 scripts/render_cms_starter.py --validate-only\n", quality)


if __name__ == "__main__":
    unittest.main()
