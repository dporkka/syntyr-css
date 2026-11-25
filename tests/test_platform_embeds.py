"""Platform embed distribution and install contracts, no external dependencies."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from scripts.build import assemble_embed, distributions

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class MarkupParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append(dict(attrs))


class PlatformEmbedTests(unittest.TestCase):
    def test_embed_build_rejects_nested_layers_even_when_indented_or_inline(self):
        # Future source additions must not silently reintroduce layers in
        # the separately advertised unlayered embed output.
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nested.css"
            for inner in (
                "@layer theme { .syn-root { color: red; } }",
                "  @layer theme { .syn-root { color: red; } }",
                "@media (width > 20rem) { @layer theme { .syn-root { color: red; } } }",
            ):
                with self.subTest(nested=inner):
                    path.write_text("@layer syn.components {\n" + inner + "\n}\n")
                    with patch("scripts.build.SOURCE", Path(folder)):
                        with self.assertRaisesRegex(ValueError, "nested layer"):
                            assemble_embed(("nested.css",))

    def test_embed_build_ignores_layer_text_in_css_comment(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "comment.css"
            path.write_text(
                "@layer syn.components {\n"
                " /* @layer annotation from documentation */\n"
                " .syn-root { color: red; }\n"
                "}\n"
            )
            with patch("scripts.build.SOURCE", Path(folder)):
                css = assemble_embed(("comment.css",))
            self.assertIn(".syn-root { color: red; }", css)

    def test_embed_bundle_is_a_named_distribution(self):
        self.assertIn("syntyr.embed.css", distributions())

    def test_embed_has_no_layers_but_retains_core_components(self):
        css = (DIST / "syntyr.embed.css").read_text()
        self.assertNotIn("@layer ", css)
        self.assertIn(".syn-root", css)
        self.assertIn("&.syn-button--primary", css)
        self.assertIn("--syn-accent:", css)
        self.assertIn("forced-colors: active", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertEqual(css, assemble_embed(distributions()["syntyr.embed.css"]))

    def test_layered_core_remains_byte_identical_to_source(self):
        self.assertEqual((DIST / "syntyr.core.css").read_text(),
                         __import__("scripts.build", fromlist=["assemble"]).assemble(
                             distributions()["syntyr.core.css"]))

    def test_embed_bundle_avoids_global_html_and_cms_selectors(self):
        css = (DIST / "syntyr.embed.css").read_text()
        # No site-wide reset or platform-specific internal markup selectors.
        self.assertNotRegex(css, r"(?m)^\s*(?:html|body|\*|button|input|a|h1)\s*[{,]")
        for forbidden in (".wix-", ".shopify-section", ".w-", ".framer-", ".wp-block-"):
            self.assertNotIn(forbidden, css)

    def test_standalone_embed_fixture_has_host_sibling_and_native_controls(self):
        parser = MarkupParser()
        parser.feed((ROOT / "examples/platform-embed.html").read_text())
        self.assertIn("button", parser.tags)
        self.assertIn("section", parser.tags)
        self.assertIn("details", parser.tags)
        self.assertIn("summary", parser.tags)
        self.assertTrue(any(a.get("class") == "syn-root" for a in parser.attrs))
        self.assertTrue(any(a.get("id") == "cms-host-control" and
                            "syn-button" in a.get("class", "")
                            for a in parser.attrs))
        self.assertTrue(any(a.get("id") == "cms-syntyr-control" for a in parser.attrs))
        self.assertFalse(any(tag in parser.tags for tag in ("script", "iframe")))

    def test_shopify_section_is_dynamic_and_escaped(self):
        liquid = (ROOT / "integrations/shopify/sections/syntyr-feature.liquid").read_text()
        self.assertIn("{% schema %}", liquid)
        self.assertIn("{% endschema %}", liquid)
        self.assertIn('class="syn-root', liquid)
        for key in ("heading", "description", "cta_label", "cta_url"):
            self.assertIn("section.settings." + key + " | escape", liquid)
        self.assertNotIn("<script", liquid)

    def test_shopify_section_schema_is_valid_json(self):
        liquid = (ROOT / "integrations/shopify/sections/syntyr-feature.liquid").read_text()
        schema = liquid.split("{% schema %}", 1)[1].split("{% endschema %}", 1)[0]
        parsed = json.loads(schema)
        self.assertEqual(parsed["name"], "Syntyr feature")
        self.assertEqual({s["id"] for s in parsed["settings"]},
                         {"heading", "description", "cta_label", "cta_url"})

    def test_wordpress_enqueue_sample_is_child_theme_scoped(self):
        php = (ROOT / "integrations/wordpress/syntyr-enqueue.php").read_text()
        self.assertIn("wp_enqueue_scripts", php)
        self.assertIn("wp_enqueue_style(", php)
        self.assertIn("get_stylesheet_directory_uri()", php)
        self.assertIn("get_stylesheet_directory()", php)
        self.assertNotIn("get_template_directory_uri()", php)
        self.assertNotIn("<script", php)

    def test_platform_guide_documents_install_routes_and_limitations(self):
        guide = (ROOT / "docs/site-builders.md").read_text()
        for name in ("WordPress", "Wix", "Shopify", "Webflow", "Framer",
                     "Squarespace", "Ghost", "HubSpot", "Drupal"):
            with self.subTest(platform=name):
                self.assertIn(name, guide)
        self.assertIn("syntyr.embed.css", guide)
        self.assertIn("iframe", guide)
        self.assertIn("unreleased", guide)


if __name__ == "__main__":
    unittest.main()
