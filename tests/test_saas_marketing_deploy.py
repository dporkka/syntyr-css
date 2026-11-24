"""Contracts for an isolated, repeatable SaaS marketing deploy target."""
from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts/build_saas_marketing_site.py"
DEPLOY = ROOT / "deploy/saas-marketing"
PUBLIC = {
    "index.html", "pricing/index.html", "about/index.html",
    "assets/site.css", "assets/syntyr.core.css",
    "robots.txt", "README.md", "LICENSE",
    ".syntyr-marketing-manifest.json",
}


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.css = []
        self.scripts = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script":
            self.scripts += 1
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.css.append(attributes["href"])
        if tag == "a":
            self.links.append(attributes.get("href", ""))


class SaaSMarketingDeploymentTests(unittest.TestCase):
    def run_build(self, out, *args):
        return subprocess.run(
            [sys.executable, str(BUILD), "--output", str(out), *args],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )

    def test_standalone_html_assets_navigation_and_explicit_allowlist(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "site"
            result = self.run_build(out)
            self.assertEqual(result.returncode, 0, result.stderr)
            items = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
            self.assertEqual(items, PUBLIC)
            self.assertEqual((out / "assets/syntyr.core.css").read_bytes(),
                             (ROOT / "dist/syntyr.core.css").read_bytes())
            self.assertEqual((out / "assets/site.css").read_bytes(),
                             (ROOT / "examples/site-starters/saas-marketing/assets/site.css").read_bytes())
            for route, prefix in (("index.html", ""), ("pricing/index.html", "../"),
                                  ("about/index.html", "../")):
                html = (out / route).read_text(encoding="utf-8")
                dom = Assets()
                dom.feed(html)
                self.assertEqual(dom.scripts, 0, route)
                self.assertEqual(dom.css, [prefix + "assets/syntyr.core.css",
                                            prefix + "assets/site.css"], route)
                self.assertIn('name="robots" content="noindex,follow"', html)
                self.assertNotIn("/dist/", html)
                for href in dom.css + dom.links:
                    if not href or href.startswith(("#", "mailto:")):
                        continue
                    target = (out / route).parent / href.split("#", 1)[0]
                    self.assertTrue(target.is_file(), f"Broken asset/link: {route} {href}")
            self.assertIn("Disallow: /", (out / "robots.txt").read_text())
            manifest = json.loads((out / ".syntyr-marketing-manifest.json").read_text())
            self.assertEqual(set(manifest), PUBLIC - {".syntyr-marketing-manifest.json"})
            for relative, digest in manifest.items():
                self.assertEqual(hashlib.sha256((out / relative).read_bytes()).hexdigest(), digest)
            self.assertIn("MIT", (out / "LICENSE").read_text())

    def test_repeat_build_and_check_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "site"
            self.assertEqual(self.run_build(out).returncode, 0)
            first = {p.relative_to(out).as_posix(): p.read_bytes()
                     for p in out.rglob("*") if p.is_file()}
            self.assertEqual(self.run_build(out, "--check").returncode, 0)
            self.assertEqual(self.run_build(out).returncode, 0)
            second = {p.relative_to(out).as_posix(): p.read_bytes()
                      for p in out.rglob("*") if p.is_file()}
            self.assertEqual(first, second)
            (out / "index.html").write_text("tampered", encoding="utf-8")
            self.assertNotEqual(self.run_build(out, "--check").returncode, 0)
            self.assertEqual(self.run_build(out).returncode, 0)
            self.assertEqual(self.run_build(out, "--check").returncode, 0)

    def test_refuses_unrelated_directories_and_symlink_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "already"
            out.mkdir()
            (out / "keep").write_text("never delete")
            self.assertNotEqual(self.run_build(out).returncode, 0)
            self.assertEqual((out / "keep").read_text(), "never delete")
            alias = Path(temp) / "symlink"
            alias.symlink_to(out, target_is_directory=True)
            self.assertNotEqual(self.run_build(alias).returncode, 0)
            self.assertEqual((out / "keep").read_text(), "never delete")
            dangling = Path(temp) / "dangling"
            dangling.symlink_to(Path(temp) / "nonexistent", target_is_directory=True)
            self.assertNotEqual(self.run_build(dangling).returncode, 0)
            self.assertTrue(dangling.is_symlink())
        self.assertNotEqual(self.run_build(ROOT).returncode, 0)

    def test_host_configs_target_only_marketing_project(self):
        vercel = json.loads((DEPLOY / "vercel.json").read_text())
        self.assertIsNone(vercel.get("framework"))
        self.assertEqual(vercel["buildCommand"], "python3 ../../scripts/build_saas_marketing_site.py")
        self.assertEqual(vercel["outputDirectory"], ".public")
        self.assertEqual(vercel["installCommand"], "echo 'No dependencies to install'")
        netlify = tomllib.loads((DEPLOY / "netlify.toml").read_text())
        self.assertEqual(netlify["build"]["command"],
                         "python3 scripts/build_saas_marketing_site.py")
        self.assertEqual(netlify["build"]["publish"], "deploy/saas-marketing/.public")
        self.assertEqual(netlify["build"]["environment"]["PYTHON_VERSION"], "3.12")
        self.assertIn("deploy/saas-marketing/.public/", (ROOT / ".gitignore").read_text())

    def test_does_not_change_existing_admin_deployment(self):
        root_vercel = json.loads((ROOT / "vercel.json").read_text())
        self.assertEqual(root_vercel["buildCommand"], "python3 scripts/build_saas_admin_starter.py")
        self.assertEqual(root_vercel["outputDirectory"], ".saas-admin-public")
        root_netlify = tomllib.loads((ROOT / "netlify.toml").read_text())
        self.assertIn("build_saas_admin_starter.py", root_netlify["build"]["command"])
        self.assertEqual(root_netlify["build"]["publish"], ".saas-admin-public")

    def test_document_host_setup_including_root_directory(self):
        guide = (DEPLOY / "README.md").read_text()
        for term in ("Vercel", "Netlify", "Render", "Cloudflare",
                     "GitHub Pages", "Root Directory", "Package directory",
                     "outside of the Root Directory", "noindex", "Python"):
            self.assertIn(term, guide)


if __name__ == "__main__":
    unittest.main()
