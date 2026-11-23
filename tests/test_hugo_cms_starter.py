"""Hugo must consume the same validated CMS JSON without runtime dependencies."""
from html.parser import HTMLParser
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.build_hugo_cms_starter import build, stage_site

ROOT = Path(__file__).resolve().parents[1]
CMS = ROOT / "examples/cms-starter"


class HugoCmsStarterTests(unittest.TestCase):
    def test_stage_uses_portable_page_contract_and_pinned_local_css(self):
        with TemporaryDirectory() as temp:
            site = Path(temp) / "site"
            stage_site(site)
            source = json.loads((CMS / "content/pages/home.json").read_text())
            generated = json.loads((site / "data/home.json").read_text())
            self.assertEqual(generated, source)
            self.assertTrue((site / "static/assets/syntyr.core.css").exists())
            self.assertTrue((site / "static/assets/syntyr.recipes.css").exists())
            self.assertFalse((site / "static/admin").exists())
            self.assertIn("/syntyr-hugo/", (site / "hugo.toml").read_text())

    def test_stage_supports_custom_deployment_prefix(self):
        with TemporaryDirectory() as temp:
            site = Path(temp) / "site"
            stage_site(site, base_url="https://example.org/agency/")
            self.assertIn("https://example.org/agency/", (site / "hugo.toml").read_text())

    def test_stage_rejects_malformed_base_urls(self):
        for bad in ("javascript:alert(1)", "https://example.org/a/../b/",
                    "https://example.org/a/%2e%2e/b/", "https://example.org/a/%2Fb/",
                    "https://example.org/a%2F", "https://example.org/a%5Cb/",
                    "https://example.org/path/?injected=1", "https://example.org/path/\nkey='unsafe'"):
            with self.subTest(bad=bad), TemporaryDirectory() as temp:
                site = Path(temp) / "site"
                with self.assertRaises(ValueError):
                    stage_site(site, base_url=bad)
                self.assertFalse(site.exists())

    def test_stage_rejects_unsafe_cms_content_before_writing(self):
        with TemporaryDirectory() as temp:
            bad = Path(temp) / "bad.json"
            data = json.loads((CMS / "content/pages/home.json").read_text())
            data["sections"][0]["button"]["url"] = "javascript:alert(1)"
            bad.write_text(json.dumps(data))
            site = Path(temp) / "site"
            with self.assertRaisesRegex(ValueError, "URL"):
                stage_site(site, content_path=bad)
            self.assertFalse(site.exists())

    def test_stage_rejects_duplicate_section_anchors(self):
        with TemporaryDirectory() as temp:
            bad = Path(temp) / "bad.json"
            data = json.loads((CMS / "content/pages/home.json").read_text())
            data["sections"][1]["id"] = data["sections"][0]["id"]
            bad.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                stage_site(Path(temp) / "site", content_path=bad)

    def test_failed_build_leaves_output_untouched(self):
        for render_fails in (False, True):
            for existing in (False, True):
                with self.subTest(render_fails=render_fails, existing=existing), TemporaryDirectory() as temp:
                    output = Path(temp) / "public"
                    if existing:
                        output.mkdir()

                    def render(command, *, check):
                        candidate = Path(command[command.index("--destination") + 1])
                        candidate.mkdir(exist_ok=True)
                        (candidate / "index.html").write_text("<html>Unverified content</html>")
                        if render_fails:
                            raise subprocess.CalledProcessError(1, command)

                    error = subprocess.CalledProcessError if render_fails else AssertionError
                    with patch("scripts.build_hugo_cms_starter.subprocess.run", side_effect=render):
                        with self.assertRaises(error):
                            build(output)
                    self.assertEqual(output.exists(), existing)
                    self.assertEqual(list(Path(temp).rglob("index.html")), [])
                    self.assertEqual(list(Path(temp).iterdir()), [output] if existing else [])

    def test_build_refuses_to_overwrite_existing_release(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "public"
            output.mkdir()
            prior_page = output / "index.html"
            prior_page.write_text("Previous release")
            with patch("scripts.build_hugo_cms_starter.subprocess.run") as render:
                with self.assertRaisesRegex(ValueError, "missing or empty"):
                    build(output)
                render.assert_not_called()
            self.assertEqual(prior_page.read_text(), "Previous release")

    def test_real_hugo_build_resolves_css_and_section_links(self):
        hugo = os.environ.get("HUGO_BIN") or shutil.which("hugo")
        if not hugo:
            self.skipTest("Hugo not installed; set HUGO_BIN to exercise real output")
        with TemporaryDirectory() as temp:
            output = Path(temp) / "public"
            output.mkdir()
            self.assertEqual(build(output, hugo=hugo), 1)
            html = (output / "index.html").read_text()
            self.assertRegex(html, r'href="?/syntyr-hugo/assets/syntyr\.core\.css"?(?:[ >])')
            self.assertIn("href=/syntyr-hugo/#section-features", html)
            self.assertIn("id=section-pricing", html)
            self.assertEqual(html.count("<h1 "), 1)
            self.assertNotIn("<script", html.lower())

    def test_real_hugo_build_custom_base_path(self):
        hugo = os.environ.get("HUGO_BIN") or shutil.which("hugo")
        if not hugo:
            self.skipTest("Hugo not installed; set HUGO_BIN to exercise real output")
        for prefix in ("/client/site/", "/my%20project/"):
            with self.subTest(prefix=prefix), TemporaryDirectory() as temp:
                output = Path(temp) / "public"
                self.assertEqual(build(output, hugo=hugo, base_url=f"https://example.org{prefix}"), 1)
                html = (output / "index.html").read_text()
                self.assertIn(f"href={prefix}assets/syntyr.core.css", html)
                self.assertIn(f"href={prefix}#section-features", html)

    def test_real_hugo_preserves_action_query_parameters(self):
        hugo = os.environ.get("HUGO_BIN") or shutil.which("hugo")
        if not hugo:
            self.skipTest("Hugo not installed; set HUGO_BIN to exercise real output")

        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.hrefs = []

            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    self.hrefs.append(dict(attrs).get("href"))

        with TemporaryDirectory() as temp:
            data = json.loads((CMS / "content/pages/home.json").read_text())
            local = "/checkout?plan=pro&quantity=2"
            external = "https://example.org" + local
            data["sections"][0]["button"]["url"] = local
            data["sections"][-1]["button"]["url"] = external
            input_path = Path(temp) / "page.json"
            input_path.write_text(json.dumps(data))
            output = Path(temp) / "public"
            self.assertEqual(build(output, hugo=hugo, content_path=input_path), 1)
            links = Links()
            links.feed((output / "index.html").read_text())
            self.assertIn("/syntyr-hugo" + local, links.hrefs)
            self.assertIn(external, links.hrefs)

    def test_real_hugo_autoescapes_untrusted_but_valid_text(self):
        hugo = os.environ.get("HUGO_BIN") or shutil.which("hugo")
        if not hugo:
            self.skipTest("Hugo not installed; set HUGO_BIN to exercise real output")
        with TemporaryDirectory() as temp:
            data = json.loads((CMS / "content/pages/home.json").read_text())
            data["sections"][0]["heading"] = '<img src=x onerror="alert(1)">'
            input_path = Path(temp) / "page.json"
            input_path.write_text(json.dumps(data))
            output = Path(temp) / "public"
            self.assertEqual(build(output, hugo=hugo, content_path=input_path), 1)
            html = (output / "index.html").read_text()
            self.assertNotIn('<img src=x', html)
            self.assertIn('&lt;img', html)

    def test_hugo_template_covers_all_portable_block_types(self):
        source = (ROOT / "examples/hugo-cms/layouts/home.html").read_text()
        # .Site.Data works on Cloudflare Pages' preinstalled Hugo 0.147.7
        # and newer Hugo. The 'hugo' namespace has no Data property there.
        self.assertIn(".Site.Data.home", source)
        self.assertNotIn("hugo.Data.home", source)
        for kind in ("hero", "features", "pricing", "faq", "cta"):
            with self.subTest(kind=kind):
                self.assertIn('eq $block.type "' + kind + '"', source)
        self.assertIn("relURL", source)
        self.assertIn("syn-root", source)
        self.assertNotIn("<script", source.lower())


if __name__ == "__main__":
    unittest.main()
