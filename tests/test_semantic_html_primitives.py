"""Common HTML elements remain native, opt-in, scoped, and JS-free."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ElementParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.sources = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag == "script":
            self.sources.append(dict(attrs).get("src"))


class SemanticPrimitivesTests(unittest.TestCase):
    def test_common_html_elements_have_class_free_and_explicit_opt_in_selectors(self):
        css = (ROOT / "src/semantic.css").read_text(encoding="utf-8")
        elements = (
            "ul", "ol", "menu", "li", "dl", "dt", "dd",
            "figure", "figcaption", "img", "video", "audio",
            "pre", "kbd", "samp", "mark", "small", "abbr",
            "caption", "progress", "meter", "output", "dialog",
            "h5", "h6", "address",
        )
        for tag in elements:
            with self.subTest(tag=tag):
                self.assertIn(f"{tag}:not([class])", css)
                self.assertIn(f"{tag}[data-syn-semantic]", css)
        self.assertIn("[popover]:not([class])", css)
        self.assertIn("[popover][data-syn-semantic]", css)

    def test_semantic_styles_do_not_change_native_interaction_or_escape_scope(self):
        css = (ROOT / "src/semantic.css").read_text(encoding="utf-8")
        self.assertIn("@layer syn.semantic", css)
        self.assertNotIn("appearance: none", css)
        self.assertNotIn("pointer-events: none", css)
        self.assertNotIn("display: none", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("accent-color: var(--syn-accent)", css)
        self.assertIn("color: var(--syn-on-accent)", css)
        self.assertIn("@media (forced-colors: active)", css)

    def test_demo_shows_supported_elements_without_javascript(self):
        path = ROOT / "examples/native-elements.html"
        parser = ElementParser()
        text = path.read_text(encoding="utf-8")
        parser.feed(text)
        tags = {tag for tag, _ in parser.tags}
        for tag in ("ul", "ol", "menu", "dl", "dt", "dd", "figure", "figcaption",
                    "pre", "code", "kbd", "mark", "progress", "meter",
                    "output", "details", "summary", "dialog", "table", "caption", "img", "samp", "small", "abbr", "h5", "h6"):
            with self.subTest(tag=tag):
                self.assertIn(tag, tags)
        self.assertNotIn("script", tags)
        self.assertIn("syn-semantic", text)
        self.assertIn('syntyr.semantic.css', text)
        self.assertIn('syntyr.core.css', text)

    def test_css_distributions_include_the_optional_native_rules(self):
        from scripts.build import distributions, assemble

        self.assertIn("semantic.css", distributions()["syntyr.semantic.css"])
        for target in ("syntyr.semantic.css", "syntyr.all.css"):
            with self.subTest(target=target):
                css = assemble(distributions()[target])
                self.assertIn("figcaption[data-syn-semantic]", css)
                self.assertIn("progress[data-syn-semantic]", css)


if __name__ == "__main__":
    unittest.main()
