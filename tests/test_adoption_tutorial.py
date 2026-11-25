"""Validate the published-release first-use tutorial and social preview."""
from html.parser import HTMLParser
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TutorialMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class AdoptionTutorialTests(unittest.TestCase):
    def test_tutorial_uses_published_classes_and_local_css(self):
        doc = (ROOT / "docs/distribution.md").read_text()
        section = doc.split("## Your first five minutes (published alpha.4)", 1)[1]
        section = section.split("\n## ", 1)[0]
        markup = re.search(r"```html\n(.*?)\n```", section, re.S).group(1)
        css = (ROOT / "site-releases/0.3.0-alpha.4/syntyr.core.css").read_text()
        parser = TutorialMarkup()
        parser.feed(markup)
        tags = parser.tags
        self.assertIn(("link", {"rel": "stylesheet", "href": "./syntyr.core.css"}), tags)
        self.assertNotIn("script", [tag for tag, _ in tags])
        self.assertIn("details", [tag for tag, _ in tags])
        self.assertIn("summary", [tag for tag, _ in tags])
        ids = {attrs["id"] for _, attrs in tags if "id" in attrs}
        for tag, attrs in tags:
            for name in attrs.get("class", "").split():
                self.assertIn("." + name, css)
            if tag == "a":
                self.assertTrue(attrs["href"].startswith("#"))
                self.assertIn(attrs["href"][1:], ids)
        self.assertIn("https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css", section)
        self.assertNotIn("alpha.5/syntyr.core.css", section)

    def test_roadmap_and_tutorial_have_human_navigation(self):
        self.assertIn('id="your-first-five-minutes-published-alpha4"',
                      (ROOT / "docs/distribution.html").read_text())
        self.assertIn('id="public-roadmap"', (ROOT / "docs/launch-status.html").read_text())
        self.assertIn("distribution.html#your-first-five-minutes-published-alpha4",
                      (ROOT / "docs/guides.html").read_text())

    def test_social_preview_dimensions(self):
        data = (ROOT / "assets/og-syntyr.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", data[16:24]), (1200, 630))
