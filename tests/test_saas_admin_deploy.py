"""Portable deployment contract for Syntyr's example SaaS Admin Starter."""
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_saas_admin_starter.py"
SITE_FILES = {
    "index.html", "pipeline.html", "customers.html", "billing.html",
    "styles.css", "assets/syntyr.core.css", "assets/syntyr.recipes.css",
    "README.md", "LICENSE", "robots.txt", ".syntyr-admin-manifest.json",
}


class AssetRefs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.links.append(attrs.get("href", ""))
        if tag == "script":
            self.scripts += 1


class SaaSAdminDeploy(unittest.TestCase):
    def build(self, output, *args):
        return subprocess.run(
            [sys.executable, str(BUILD), "--output", str(output), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_safe_isolated_build_rewrites_css_and_nothing_else(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "public"
            result = self.build(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}, SITE_FILES)
            for page in ("index", "pipeline", "customers", "billing"):
                text = (output / f"{page}.html").read_text()
                refs = AssetRefs()
                refs.feed(text)
                self.assertEqual(refs.links, ["assets/syntyr.core.css", "assets/syntyr.recipes.css", "styles.css"])
                self.assertEqual(refs.scripts, 0)
                self.assertIn('content="noindex,follow"', text)
                self.assertNotIn("../../dist/", text)
                for href in refs.links:
                    self.assertTrue((output / href).is_file())
            self.assertEqual(
                (output / "assets/syntyr.core.css").read_bytes(),
                (ROOT / "dist/syntyr.core.css").read_bytes(),
            )
            self.assertEqual(
                (output / "assets/syntyr.recipes.css").read_bytes(),
                (ROOT / "dist/syntyr.recipes.css").read_bytes(),
            )
            self.assertIn("Disallow: /", (output / "robots.txt").read_text())
            self.assertIn("MIT", (output / "LICENSE").read_text())
            self.assertNotIn("business/", json.dumps(json.loads(
                (output / ".syntyr-admin-manifest.json").read_text()
            )))
            self.assertEqual(self.build(output, "--check").returncode, 0)

    def test_check_detects_drift_and_rebuild_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "public"
            self.assertEqual(self.build(output).returncode, 0)
            before = {p.relative_to(output).as_posix(): p.read_bytes() for p in output.rglob("*") if p.is_file()}
            self.assertEqual(self.build(output).returncode, 0)
            after = {p.relative_to(output).as_posix(): p.read_bytes() for p in output.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            (output / "index.html").write_text("<h1>tampered</h1>")
            self.assertNotEqual(self.build(output, "--check").returncode, 0)

    def test_does_not_overwrite_unrelated_directory_or_source_root(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "existing"
            out.mkdir()
            (out / "important.txt").write_text("keep")
            self.assertNotEqual(self.build(out).returncode, 0)
            self.assertEqual((out / "important.txt").read_text(), "keep")
        self.assertNotEqual(self.build(ROOT).returncode, 0)

    def test_reviewed_accessibility_and_copy_contract(self):
        for name, label in [
            ("customers.html", "Customer directory, scroll horizontally for more columns"),
            ("billing.html", "Invoices, scroll horizontally for more columns"),
        ]:
            page = (ROOT / "examples/saas-admin-starter" / name).read_text()
            self.assertIn(f'role="region" aria-label="{label}" tabindex="0"', page)
        docs = (ROOT / "examples/saas-admin-starter/README.md").read_text()
        self.assertIn("README.md", docs)
        self.assertIn("four HTML files, styles.css, and README.md", docs)

    def test_hosts_use_one_build_and_isolated_publish_directory(self):
        vercel = json.loads((ROOT / "vercel.json").read_text())
        self.assertEqual(vercel["buildCommand"], "python3 scripts/build_saas_admin_starter.py")
        self.assertEqual(vercel["outputDirectory"], ".saas-admin-public")
        netlify = tomllib.loads((ROOT / "netlify.toml").read_text())
        self.assertEqual(netlify["build"]["command"], vercel["buildCommand"])
        self.assertEqual(netlify["build"]["publish"], vercel["outputDirectory"])
        render = (ROOT / "render.yaml").read_text()
        self.assertIn("runtime: static", render)
        self.assertIn("buildCommand: python3 scripts/build_saas_admin_starter.py", render)
        self.assertIn("staticPublishPath: .saas-admin-public", render)
        self.assertIn(".saas-admin-public/", (ROOT / ".gitignore").read_text())
        guide = (ROOT / "examples/saas-admin-starter/README.md").read_text()
        for host in ("Vercel", "Netlify", "Render", "Cloudflare Pages", "GitHub Pages", "static server"):
            self.assertIn(host, guide)


if __name__ == "__main__":
    unittest.main()
