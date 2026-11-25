"""Regression contracts for HTML-first adoption and intrinsic compositions."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.classes = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.classes.extend(attrs.get("class", "").split())
        if tag == "script":
            self.scripts.append(attrs.get("src"))


class AdoptionComposition(unittest.TestCase):
    def test_sidecar_wraps_without_js_or_viewport_media_queries(self):
        css = (ROOT / "src/components/layout.css").read_text()
        self.assertIn("&.syn-sidecar {", css)
        sidecar = css.split("&.syn-sidecar {", 1)[1].split("&.syn-panel {", 1)[0]
        self.assertIn("display: flex;", sidecar)
        self.assertIn("flex-wrap: wrap;", sidecar)
        self.assertIn("--syn-sidecar-gap", sidecar)
        self.assertIn("--syn-sidecar-main-min", sidecar)
        self.assertIn("--syn-sidecar-aside-width", sidecar)
        self.assertIn("min(100%,", sidecar)
        self.assertNotIn("@media", sidecar)
        self.assertNotIn("@import", sidecar)

    def test_optional_aside_keeps_main_child_overflow_protection(self):
        css = (ROOT / "src/components/layout.css").read_text()
        self.assertIn("&.syn-sidecar > :first-child {", css)
        self.assertNotIn("&.syn-sidecar > :first-child:not(:last-child)", css)

    def test_existing_inline_supports_configurable_cluster_alignment(self):
        css = (ROOT / "src/components/layout.css").read_text()
        inline = css.split("&.syn-inline {", 1)[1].split("}", 1)[0]
        self.assertIn("--syn-inline-align", inline)
        self.assertIn("--syn-inline-justify", inline)
        self.assertIn("flex-wrap: wrap;", inline)

    def test_compositions_are_shipped_and_documented_as_html_first(self):
        guide = (ROOT / "docs/composition-adoption.md").read_text()
        self.assertIn("syn-sidecar", guide)
        self.assertIn("syn-inline", guide)
        self.assertIn("No additional JavaScript", guide)
        html = (ROOT / "examples/composition-adoption.html").read_text()
        parser = Elements()
        parser.feed(html)
        for cls in ("syn-root", "syn-sidecar", "syn-inline", "syn-panel"):
            self.assertIn(cls, parser.classes)
        self.assertFalse(parser.scripts)
        self.assertIn('href="../dist/syntyr.core.css"', html)
        self.assertIn("composition-adoption.md", (ROOT / "README.md").read_text())

    def test_go_template_starter_is_linked_without_importing_go_into_css(self):
        self.assertTrue((ROOT / "examples/go-htmx/go.mod").is_file())
        self.assertTrue((ROOT / "examples/go-htmx/main.go").is_file())
        self.assertTrue((ROOT / "examples/go-htmx/main_test.go").is_file())
        self.assertIn("go-htmx", (ROOT / "docs/framework-integrations.md").read_text())
        self.assertIn("go-htmx", (ROOT / "README.md").read_text())
        self.assertNotIn("@import", (ROOT / "src/components/layout.css").read_text())


if __name__ == "__main__":
    unittest.main()
