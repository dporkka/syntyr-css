"""Runnable Astro + Keystatic fixture protects static-public and editor boundaries."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.verify_astro_keystatic import verify_public_site

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "examples/astro-keystatic"


class AstroKeystaticSiteTests(unittest.TestCase):
    def test_build_scripts_use_portable_validator_before_astros_build(self):
        pkg = json.loads((SITE / "package.json").read_text())
        self.assertIn("prebuild", pkg["scripts"])
        self.assertIn("npm run export:data", pkg["scripts"]["prebuild"])
        self.assertIn("export_cms_adapter.py keystatic", pkg["scripts"]["export:data"])
        self.assertIn("astro build", pkg["scripts"]["build"])
        self.assertIn("@keystatic/astro", pkg["devDependencies"])
        self.assertIn("file:../..", pkg["dependencies"]["@syntyr/css"])
        self.assertNotIn("dependencies", json.loads((ROOT / "package.json").read_text()))

    def test_astro_build_uses_patched_v7_line(self):
        package = json.loads((SITE / "package.json").read_text())
        major, minor, patch = map(int, package["dependencies"]["astro"].split("."))
        self.assertGreaterEqual((major, minor, patch), (7, 4, 7))
        self.assertGreaterEqual(
            int(package["devDependencies"]["@astrojs/react"].split(".")[0]), 7
        )
        self.assertTrue((SITE / "package-lock.json").exists())
        self.assertEqual(package["engines"]["node"], ">=22.23.4")

    def test_editor_is_explicit_dev_only_and_binds_to_loopback(self):
        config = (SITE / "astro.config.mjs").read_text()
        self.assertIn("SYNTYR_ENABLE_LOCAL_EDITOR", config)
        self.assertIn("127.0.0.1", config)
        self.assertIn("output: 'static'", config)
        self.assertIn("base: '/syntyr-astro-keystatic/'", config)
        self.assertIn("keystatic()", config)
        self.assertIn("NODE_ENV === 'development'", config)

    def test_editor_schema_tracks_shared_cms_contract(self):
        shared = (ROOT / "examples/cms-keystatic/keystatic.config.ts").read_text()
        local = (SITE / "keystatic.config.ts").read_text()
        self.assertEqual(local, shared)
        source = json.loads((SITE / "content/pages/home.json").read_text())
        reference = json.loads((ROOT / "examples/cms-keystatic/content/pages/home.json").read_text())
        self.assertEqual(source, reference)

    def test_site_has_native_five_block_renderers_without_raw_html(self):
        content = (SITE / "src/pages/index.astro").read_text()
        for kind in ("hero", "features", "pricing", "faq", "cta"):
            self.assertIn(f"section.type === '{kind}'", content)
        self.assertIn("syn-root", content)
        self.assertIn("aria-labelledby", content)
        self.assertNotIn("set:html", content)

    def test_verifier_cli_accepts_root_assets_with_explicit_base(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp)
            (output / "index.html").write_text(
                '<link rel="stylesheet" href="/site.css"><main class="syn-root"></main>',
                encoding="utf-8",
            )
            (output / "site.css").write_text(".syn-root {}", encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts/verify_astro_keystatic.py"), tmp]
            default = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(default.returncode, 0)
            self.assertIn("Stylesheet URL ignores base path", default.stderr)
            root = subprocess.run(command + ["--base-path", "/"], capture_output=True, text=True)
            self.assertEqual(root.returncode, 0, root.stderr)

    def test_verifier_rejects_extra_editor_route_even_when_script_free(self):
        if not (SITE / "dist").is_dir():
            self.skipTest("Run npm run build to exercise a copied real output")
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "dist"
            shutil.copytree(SITE / "dist", output)
            (output / "keystatic").mkdir()
            (output / "keystatic/index.html").write_text(
                (output / "index.html").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AssertionError, "unexpected HTML route"):
                verify_public_site(output)

    def test_verifier_rejects_editor_asset_or_browser_javascript(self):
        if not (SITE / "dist").is_dir():
            self.skipTest("Run npm run build to exercise a copied real output")
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "dist"
            shutil.copytree(SITE / "dist", output)
            (output / "api/keystatic").mkdir(parents=True)
            (output / "api/keystatic/route.txt").write_text("editor API")
            with self.assertRaisesRegex(AssertionError, "editor route"):
                verify_public_site(output)
            shutil.rmtree(output / "api")
            (output / "client.mjs").write_text("console.log('unexpected')")
            with self.assertRaisesRegex(AssertionError, "JavaScript asset"):
                verify_public_site(output)

    def test_generated_output_is_zero_js_and_safe_under_deployment_base(self):
        if not (SITE / "dist").is_dir():
            self.skipTest("Run npm run build to exercise real Astro output")
        self.assertEqual(
            verify_public_site(SITE / "dist"), 1
        )
        html = (SITE / "dist/index.html").read_text()
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn("section-features", html)
        self.assertNotIn("<script", html.lower())
        self.assertFalse((SITE / "dist/keystatic").exists())


if __name__ == "__main__":
    unittest.main()
