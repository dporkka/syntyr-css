"""Native carousel affordances remain optional, accessible, and JS-free."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RailMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rails = []
        self.articles = []
        self._in_enhanced_rail = False
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        classes = props.get("class", "").split()
        if tag == "div" and "syn-media-rail--controls" in classes:
            self.rails.append(props)
            self._in_enhanced_rail = True
            self._depth = 1
        elif self._in_enhanced_rail and tag == "div":
            self._depth += 1
        if self._in_enhanced_rail and tag == "article":
            self.articles.append(props)

    def handle_endtag(self, tag):
        if self._in_enhanced_rail and tag == "div":
            self._depth -= 1
            if self._depth == 0:
                self._in_enhanced_rail = False


class NativeCarouselContracts(unittest.TestCase):
    def test_native_affordances_are_opt_in_and_preserve_base_rail(self):
        css = (ROOT / "src/media.css").read_text()
        self.assertIn(".syn-media-rail--controls::scroll-button(inline-start)", css)
        self.assertIn(".syn-media-rail--controls::scroll-button(inline-end)", css)
        self.assertIn('content: "‹" / "Scroll backward"', css)
        self.assertIn('content: "›" / "Scroll forward"', css)
        self.assertIn("::scroll-button(*):focus-visible", css)
        self.assertIn("::scroll-button(*):disabled", css)
        self.assertIn(".syn-media-rail--markers::scroll-marker-group", css)
        self.assertIn("scroll-marker-group: after", css)
        self.assertIn("attr(data-syn-scroll-label)", css)
        self.assertIn("::scroll-marker:target-current", css)
        self.assertIn("::scroll-marker:focus-visible", css)
        self.assertIn("forced-colors: active", css)
        self.assertIn("scroll-snap-type: inline proximity", css)
        self.assertNotIn("<script", css)

    def test_demo_has_a_named_rail_and_per_item_marker_names_without_script(self):
        html = (ROOT / "examples/media-entertainment.html").read_text()
        document = RailMarkup()
        document.feed(html)
        self.assertNotIn("<script", html)
        self.assertEqual(len(document.rails), 1)
        self.assertIn("syn-media-rail--markers", document.rails[0]["class"])
        self.assertEqual(document.rails[0]["tabindex"], "0")
        self.assertEqual(document.rails[0]["role"], "region")
        self.assertIn("aria-label", document.rails[0])
        self.assertGreaterEqual(len(document.articles), 4)
        for item in document.articles:
            with self.subTest(item=item):
                self.assertTrue(item.get("data-syn-scroll-label", "").strip())

    def test_docs_publish_compatibility_and_behavior_limitations(self):
        guide = (ROOT / "docs/media-entertainment.md").read_text()
        native = (ROOT / "docs/native-patterns.md").read_text()
        stability = (ROOT / "docs/api-stability.md").read_text()
        for expected in (
            "syn-media-rail--controls", "syn-media-rail--markers",
            "data-syn-scroll-label", "Firefox", "Safari",
            "scrollbar", "no JavaScript",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, guide)
        self.assertIn("syn-media-rail--controls", native)
        self.assertIn("syn-media-rail--controls", stability)


if __name__ == "__main__":
    unittest.main()
