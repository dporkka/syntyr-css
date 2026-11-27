"""Regression checks for independent static renderers and HTML processing."""
from copy import deepcopy
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import time
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
        # A paragraph directly followed by an inline link must keep its end;
        # omitting it would move the link inside the paragraph in HTML.
        omitted = re.sub(r"</p>(?=\s*(?:</|<(?:h1|div|ul)\b))", "", self.markup)
        self.page.write_text(omitted.replace("</li>", "")
                             .replace('class="syn-region syn-panel"', 'class="syn-panel syn-region"')
                             .replace(">\n", ">"))
        self.assertEqual(self.verify(), 1)

    def test_signature_preserves_text_placement_inside_styled_paragraphs(self):
        page = '<html><body><footer><p class="syn-muted">Title</p></footer></body></html>'
        omitted = page.replace("</p>", "")
        moved = page.replace("Title</p>", "</p>Title")
        self.assertEqual(signature(page, "/"), signature(omitted, "/"))
        self.assertNotEqual(signature(page, "/"), signature(moved, "/"))
        with_link = page.replace("</p>", '</p><a href="/signup">Join</a>')
        self.assertNotEqual(signature(with_link, "/"), signature(with_link.replace("</p>", ""), "/"))

    def test_signature_preserves_text_placement_inside_list_items(self):
        page = '<html><body><ul><li>First</li><li>Second</li></ul></body></html>'
        self.assertEqual(signature(page, "/"), signature(page.replace("</li>", ""), "/"))
        self.assertNotEqual(signature(page, "/"), signature(page.replace("Second</li>", "</li>Second"), "/"))

    def test_rejects_duplicate_keys_even_when_last_value_matches_output(self):
        valid = json.dumps(self.document)
        self.content.write_text('{"title":"Shadowed title",' + valid[1:], encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.verify()

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


class EleventyStrictInput(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node") and shutil.which("python3"), "Node and Python needed")
    def test_real_config_rejects_ambiguous_content_before_template_data(self):
        # Isolate the actual JS config and canonical Python loader from the
        # checkout; no npm installation or mutation of real editor data.
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples/eleventy"
            example.mkdir(parents=True)
            for name in ("eleventy.config.js", "package.json"):
                shutil.copyfile(ROOT / "examples/eleventy" / name, example / name)
            scripts = root / "scripts"
            scripts.mkdir()
            shutil.copyfile(ROOT / "scripts/render_cms_starter.py", scripts / "render_cms_starter.py")
            content = root / "examples/cms-starter/content/pages/home.json"
            content.parent.mkdir(parents=True)
            good = json.loads(CONTENT.read_text())
            good["title"] = "Olá 🌐"
            probe = """
import configure from "./eleventy.config.js";
configure({
  addWatchTarget(path, options) {
    console.log("WATCH", path, JSON.stringify(options));
  },
  addGlobalData(name, load) {
    const value = load();
    console.log("TEMPLATE_DATA", name, value.title, value.sections.length,
      value.sections.at(-1).items?.at(-1).description.length ?? 0);
  },
  setNunjucksEnvironmentOptions() {}, addFilter() {}, addPassthroughCopy() {},
});
"""
            def run(payload):
                content.write_bytes(payload)
                return subprocess.run(
                    ["node", "--input-type=module", "-e", probe],
                    cwd=example, capture_output=True, text=True, encoding="utf-8", timeout=30,
                )

            valid = json.dumps(good, ensure_ascii=False).encode("utf-8")
            result = run(valid)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('WATCH ../cms-starter/content/pages/home.json {"resetConfig":true}', result.stdout)
            self.assertIn("TEMPLATE_DATA pageContent Olá 🌐", result.stdout)
            # Last-key-wins parsing would accept this exact page.
            invalid = (
                (b'{"title":"shadow",' + valid[1:], "Duplicate"),
                (valid.replace(b'Ol\xc3\xa1', b'Ol\xff'), "Unicode"),
                (valid.replace(b'Ol\xc3\xa1', b'\\ud800'), "Unicode"),
                (b'{"metadata":NaN,' + valid[1:], "Non-JSON"),
                (b'[' * 33 + b'0' + b']' * 33, "nesting"),
            )
            for payload, message in invalid:
                with self.subTest(message=message, beginning=payload[:40]):
                    result = run(payload)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertNotIn("TEMPLATE_DATA", result.stdout)
            # Valid documents can exceed Node's default 1 MiB stdout limit.
            good["sections"] = [good["sections"][0]] + [
                {"type": "features", "id": f"features-{index}", "heading": "Features",
                 "items": [{"title": "á" * 1000, "description": "é" * 1000}] * 24}
                for index in range(23)
            ]
            large = json.dumps(good, ensure_ascii=False).encode("utf-8")
            self.assertGreater(len(large), 1024 * 1024)
            result = run(large)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("TEMPLATE_DATA pageContent Olá 🌐 24 1000", result.stdout)


    @unittest.skipUnless(shutil.which("node") and shutil.which("python3"), "Node and Python needed")
    def test_real_eleventy_watch_refreshes_external_json_if_installed(self):
        cli = ROOT / "examples/eleventy/node_modules/@11ty/eleventy/cmd.cjs"
        if not cli.is_file():
            self.skipTest("Run npm ci in examples/eleventy for live watch proof")
        with TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            example = fixture / "examples/eleventy"
            shutil.copytree(ROOT / "examples/eleventy", example,
                            ignore=shutil.ignore_patterns("node_modules", "_site"))
            shutil.copytree(ROOT / "examples/cms-starter/content",
                            fixture / "examples/cms-starter/content")
            (fixture / "scripts").mkdir()
            shutil.copyfile(ROOT / "scripts/render_cms_starter.py",
                            fixture / "scripts/render_cms_starter.py")
            (fixture / "dist").mkdir()
            for name in ("syntyr.core.css", "syntyr.recipes.css"):
                shutil.copyfile(ROOT / "dist" / name, fixture / "dist" / name)
            content = fixture / "examples/cms-starter/content/pages/home.json"
            output = example / "_site/index.html"
            log = fixture / "watch.log"
            changed = "Independent CMS watch refresh"
            with log.open("w") as stream:
                process = subprocess.Popen(["node", str(cli), "--watch"], cwd=example,
                                           stdout=stream, stderr=subprocess.STDOUT)
                try:
                    def wait_for(predicate):
                        deadline = time.monotonic() + 20
                        while time.monotonic() < deadline:
                            if process.poll() is not None or predicate():
                                break
                            time.sleep(.1)
                        self.assertTrue(predicate(), log.read_text(encoding="utf-8"))

                    wait_for(lambda: output.is_file() and
                             "Watching" in log.read_text(encoding="utf-8"))
                    page = json.loads(content.read_text(encoding="utf-8"))
                    page["title"] = changed
                    content.write_text(json.dumps(page), encoding="utf-8")
                    wait_for(lambda: changed in output.read_text(encoding="utf-8"))
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()


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
