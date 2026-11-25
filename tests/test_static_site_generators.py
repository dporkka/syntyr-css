"""Generator-neutral, zero-runtime CSS contracts with a real Eleventy fixture."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.verify_static_generators import verify_static_site

ROOT = Path(__file__).resolve().parents[1]


class StaticSiteGeneratorContract(unittest.TestCase):
    def test_eleventy_build_source_uses_passthrough_and_path_prefix(self):
        project = ROOT / "examples/eleventy"
        package = json.loads((project / "package.json").read_text())
        self.assertIn("@11ty/eleventy", package["devDependencies"])
        self.assertNotIn("@syntyr/css", package.get("dependencies", {}))
        self.assertNotIn("dependencies", json.loads((ROOT / "package.json").read_text()))
        config = (project / "eleventy.config.js").read_text()
        self.assertIn("addPassthroughCopy", config)
        self.assertIn("../../dist/syntyr.core.css", config)
        self.assertIn("pathPrefix", config)
        template = (project / "src/index.njk").read_text()
        self.assertIn("| url", template)
        self.assertIn("syn-root", template)
        self.assertIn("data-syn-theme", template)
        self.assertNotIn("<script", template.lower())

    def test_astro_output_has_explicit_static_base_path_and_build_verifier(self):
        project = ROOT / "examples/astro"
        config = (project / "astro.config.mjs").read_text()
        self.assertIn("output: 'static'", config)
        self.assertIn("base: '/syntyr-astro/'", config)
        package = json.loads((project / "package.json").read_text())
        self.assertIn("--base-path /syntyr-astro/", package["scripts"]["verify"])

    def test_generator_guide_covers_static_and_package_workflows(self):
        guide = (ROOT / "docs/static-site-generators.md").read_text()
        for generator in ("Astro", "Eleventy", "Hugo", "Jekyll", "Zola", "Next.js"):
            with self.subTest(generator=generator):
                self.assertIn(generator, guide)
        self.assertIn("base path", guide.lower())
        self.assertIn("unreleased", guide.lower())

    def _site(self, root: Path, stylesheet_href: str, css: bool = True, script: bool = False):
        (root / "guide").mkdir(parents=True)
        (root / "guide/index.html").write_text(
            '<!doctype html><html lang="en"><head>'
            f'<link rel="stylesheet" href="{stylesheet_href}">'
            '</head><body><main class="syn-root" data-syn-theme="studio">'
            '<h1>Guide</h1></main>'
            + ('<script src="/app.js"></script>' if script else '')
            + '</body></html>'
        )
        if css:
            (root / "assets").mkdir()
            (root / "assets/syntyr.core.css").write_text(".syn-root { color: black; }")

    def test_verifier_accepts_base_prefixed_css_and_no_javascript(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "/my-site/assets/syntyr.core.css")
            pages = verify_static_site(root, base_path="/my-site/")
            self.assertEqual(pages, 1)

    def test_verifier_keeps_seo_structured_data_without_executable_javascript(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "/my-site/assets/syntyr.core.css")
            page = root / "guide/index.html"
            content = page.read_text()
            content = content.replace(
                "</head>",
                '<script type="application/ld+json">{"@context":"https://schema.org"}</script></head>',
            )
            page.write_text(content)
            self.assertEqual(verify_static_site(root, base_path="/my-site/"), 1)

    def test_verifier_rejects_unprefixed_root_url(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "/assets/syntyr.core.css")
            with self.assertRaisesRegex(AssertionError, "base path"):
                verify_static_site(root, base_path="/my-site/")

    def test_verifier_rejects_missing_local_css(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "/my-site/assets/syntyr.core.css", css=False)
            with self.assertRaisesRegex(AssertionError, "Missing stylesheet"):
                verify_static_site(root, base_path="/my-site/")

    def test_verifier_rejects_accidental_javascript_and_external_css(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "/my-site/assets/syntyr.core.css", script=True)
            with self.assertRaisesRegex(AssertionError, "JavaScript"):
                verify_static_site(root, base_path="/my-site/")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "https://cdn.example.com/syntyr.css")
            with self.assertRaisesRegex(AssertionError, "External stylesheet"):
                verify_static_site(root, base_path="/my-site/")

    def test_rejects_inline_event_handlers_without_script_tags(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "/my-site/assets/syntyr.core.css")
            page = root / "guide/index.html"
            page.write_text(page.read_text().replace("<body>", '<body onload="alert(1)">'))
            with self.assertRaisesRegex(AssertionError, "JavaScript"):
                verify_static_site(root, base_path="/my-site/")

    def test_rejects_javascript_navigation_and_form_urls(self):
        for html in ('<a href="javascript:alert(1)">Launch</a>',
                     '<button formaction=" javascript:alert(1)">Launch</button>'):
            with self.subTest(html=html), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                self._site(root, "/my-site/assets/syntyr.core.css")
                page = root / "guide/index.html"
                page.write_text(page.read_text().replace("</main>", html + "</main>"))
                with self.assertRaisesRegex(AssertionError, "JavaScript"):
                    verify_static_site(root, base_path="/my-site/")

    def test_rejects_base_url_that_rewrites_relative_stylesheet(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "assets/syntyr.core.css")
            local = root / "guide/assets"
            local.mkdir(parents=True)
            (local / "syntyr.core.css").write_text(".syn-root { color: black }")
            self.assertEqual(verify_static_site(root, base_path="/my-site/"), 1)
            page = root / "guide/index.html"
            page.write_text(page.read_text().replace("<head>", '<head><base href="/other/">'))
            with self.assertRaisesRegex(AssertionError, "base path"):
                verify_static_site(root, base_path="/my-site/")

    def test_accepts_local_reset_stylesheet_alongside_syntyr_css(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._site(root, "/my-site/assets/syntyr.core.css")
            (root / "assets/reset.css").write_text("* { box-sizing: border-box }")
            page = root / "guide/index.html"
            page.write_text(page.read_text().replace(
                "</head>", '<link rel="stylesheet" href="/my-site/assets/reset.css"></head>'))
            self.assertEqual(verify_static_site(root, base_path="/my-site/"), 1)

    def test_public_generator_guide_is_published_and_indexed(self):
        publisher = (ROOT / "scripts/build_cloudflare_site.py").read_text()
        index = (ROOT / "llms.txt").read_text()
        self.assertIn('"static-site-generators.md"', publisher)
        self.assertIn("docs/static-site-generators.md", index)
        eleventy = (ROOT / "examples/eleventy/README.md").read_text()
        self.assertIn("--base-path", eleventy)
        self.assertIn("pathPrefix", eleventy)



if __name__ == "__main__":
    unittest.main()
