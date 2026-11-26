"""Regression checks for independent static renderers and HTML processing."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.render_cms_starter import render_document
from scripts.verify_cms_parity import CONTENT, signature, verify_cms_output
from scripts.verify_static_generators import Page, verify_static_site

ROOT = Path(__file__).resolve().parents[1]
BASE = "/agency/site/"


class CmsGeneratorParity(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(CONTENT.read_text())
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "site"
        self.output.mkdir()
        self.content = self.root / "home.json"
        self.content.write_text(json.dumps(self.document))
        css = self.output / "css"
        css.mkdir()
        for name in ("syntyr.core.css", "syntyr.recipes.css"):
            shutil.copyfile(ROOT / "dist" / name, css / name)
        self.markup = render_document(self.document).replace('href="/', f'href="{BASE}')
        self.page = self.output / "index.html"
        self.page.write_text(self.markup)

    def verify(self):
        return verify_cms_output(self.output, base_path=BASE, content_path=self.content)

    def test_equivalent_formatting_and_optional_end_tags(self):
        self.page.write_text(self.markup.replace("</li>", "").replace("</p>", "")
                             .replace('class="syn-region syn-panel"', 'class="syn-panel syn-region"')
                             .replace(">\n", ">"))
        self.assertEqual(self.verify(), 1)

    def test_rejects_missing_or_changed_content_and_semantics(self):
        mutations = (
            ("Built for long-lived websites", "Changed heading"),
            ('id="section-features"', 'id="broken"'),
            ('aria-labelledby="section-features"', 'aria-labelledby="wrong"'),
            ("<details", "<div"),
            ("<summary>", "<span>"),
            ('class="syn-price-card"', 'class="syn-panel"'),
            ('data-syn-theme="studio"', 'data-syn-theme="noir"'),
            ("Syntyr CMS Starter", "Other site"),
            ('href="https://syntyr-css.pages.dev/"', 'href="https://other.example/"'),
            ("<main", "<div"),
        )
        for old, new in mutations:
            with self.subTest(old=old):
                self.assertIn(old, self.markup)
                self.page.write_text(self.markup.replace(old, new, 1))
                with self.assertRaisesRegex(AssertionError, "CMS parity mismatch"):
                    self.verify()

    def test_rejects_links_that_escape_deployment_prefix(self):
        self.page.write_text(self.markup.replace(BASE + "#section-features", "/#section-features"))
        with self.assertRaisesRegex(AssertionError, "CMS link ignores base path"):
            self.verify()

    def test_rejects_url_traversal_even_with_literal_mount_prefix(self):
        self.page.write_text(self.markup.replace(BASE + "#section-features", BASE + "%2e%2e/#section-features"))
        with self.assertRaisesRegex(AssertionError, "CMS link contains a traversal segment"):
            self.verify()

    def test_rejects_unexpected_document_base_and_duplicate_attributes(self):
        self.page.write_text(self.markup.replace("<head>", f'<head><base href="{BASE}other/">'))
        with self.assertRaisesRegex(AssertionError, "CMS parity mismatch"):
            self.verify()
        self.page.write_text(self.markup.replace('id="section-features"', 'id="wrong" id="section-features"'))
        with self.assertRaisesRegex(AssertionError, "Duplicate attributes"):
            self.verify()

    def test_rejects_missing_recipes_and_browser_script(self):
        self.page.write_text(self.markup.replace(f'<link rel="stylesheet" href="{BASE}css/syntyr.recipes.css">', ''))
        with self.assertRaisesRegex(AssertionError, "Missing required CSS markers"):
            self.verify()
        self.page.write_text(self.markup.replace("</body>", '<script src="app.js"></script></body>'))
        with self.assertRaisesRegex(AssertionError, "Unexpected JavaScript"):
            self.verify()

    def test_escaped_text_query_and_external_link_preserved(self):
        data = deepcopy(self.document)
        data["sections"][0]["heading"] = 'Unicode café & <img src=x onerror="alert(1)">'
        data["sections"][0]["button"]["url"] = "/checkout%2Fitem?plan=pro&qty=2"
        self.content.write_text(json.dumps(data))
        markup = render_document(data).replace('href="/', f'href="{BASE}')
        self.page.write_text(markup)
        self.assertEqual(self.verify(), 1)
        self.page.write_text(markup.replace("checkout%2Fitem", "checkout/item"))
        with self.assertRaisesRegex(AssertionError, "CMS parity mismatch"):
            self.verify()

    def test_eleventy_output_if_built(self):
        site = ROOT / "examples/eleventy/_site"
        if not (site / "index.html").is_file():
            self.skipTest("Run npm run build in examples/eleventy for actual output")
        self.assertEqual(verify_cms_output(site, base_path="/syntyr-eleventy/"), 1)

    def test_astro_output_if_built(self):
        site = ROOT / "examples/astro-keystatic/dist"
        if not (site / "index.html").is_file():
            self.skipTest("Run npm run build in examples/astro-keystatic for actual output")
        self.assertEqual(verify_cms_output(site, base_path="/syntyr-astro-keystatic/"), 1)


class SoupaultExample(unittest.TestCase):
    def test_source_keeps_scope_explicit_and_configuration_narrow(self):
        source = ROOT / "examples/soupault"
        config = (source / "soupault.toml").read_text()
        self.assertIn("generator_mode = false", config)
        self.assertIn('widget = "insert_html"', config)
        self.assertIn('selector = "head"', config)
        self.assertNotIn("exec", config)
        for page in (source / "site").rglob("*.html"):
            self.assertIn('class="syn-root syn-semantic"', page.read_text())
            self.assertNotIn("<script", page.read_text())

    def test_real_soupault_build_preserves_content_and_local_css(self):
        binary = os.environ.get("SOUPAULT_BIN") or shutil.which("soupault")
        if not binary:
            self.skipTest("Soupault not installed; set SOUPAULT_BIN to check actual output")
        with TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            shutil.copytree(ROOT / "examples/soupault", project,
                            ignore=shutil.ignore_patterns("build", "assets", ".soupault-cache"))
            asset = project / "site/assets/syntyr.semantic-bundle.css"
            asset.parent.mkdir()
            shutil.copyfile(ROOT / "dist" / asset.name, asset)
            subprocess.run([binary], cwd=project, check=True)
            output = project / "build"
            self.assertEqual(verify_static_site(output, base_path="/syntyr-soupault/"), 2)
            self.assertEqual((output / "assets" / asset.name).read_bytes(), asset.read_bytes())
            first_build = {path.relative_to(output): path.read_bytes()
                           for path in output.rglob("*") if path.is_file()}
            subprocess.run([binary], cwd=project, check=True)
            self.assertEqual(first_build, {path.relative_to(output): path.read_bytes()
                                          for path in output.rglob("*") if path.is_file()})
            self.assertFalse((project / ".soupault-cache").exists())
            for source in (project / "site").rglob("*.html"):
                result = output / source.relative_to(project / "site")
                self.assertEqual(signature(result.read_text(), "/syntyr-soupault/"),
                                 signature(source.read_text(), "/syntyr-soupault/"))
                page = Page()
                page.feed(result.read_text())
                self.assertEqual(page.stylesheets, ["/syntyr-soupault/assets/" + asset.name])


if __name__ == "__main__":
    unittest.main()
