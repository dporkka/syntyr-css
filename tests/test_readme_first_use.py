"""Verify the first copy/paste example against the actual published release."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.3.0-alpha.4"
PUBLISHED_URL = (
    f"https://syntyr-css.pages.dev/v/{VERSION}/syntyr.core.css"
)


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class ReadmeFirstUseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        marker = "## Quick start — published alpha.4"
        if marker not in cls.readme:
            cls.section = ""
            cls.example = ""
            return
        cls.section = cls.readme.split(marker, 1)[1].split("\n## ", 1)[0]
        match = re.search(r"```html\n(.*?)\n```", cls.section, re.S)
        cls.example = match.group(1) if match else ""

    def test_quickstart_appears_before_feature_catalog(self):
        self.assertTrue(self.section, "Missing pinned, published-release quickstart")
        self.assertLess(self.readme.index("## Quick start — published alpha.4"),
                        self.readme.index("## Live gallery and installation"))
        self.assertIn("unreleased", self.section.lower())

    def test_copy_paste_html_is_semantic_and_has_real_navigation(self):
        self.assertTrue(self.example, "Missing standalone HTML example")
        doc = Markup()
        doc.feed(self.example)
        tags = [tag for tag, _ in doc.elements]
        self.assertIn(("html", {"lang": "en"}), doc.elements)
        self.assertIn("main", tags)
        self.assertIn("h1", tags)
        self.assertNotIn("script", tags)
        self.assertNotIn("button", tags, "Avoid inert demo actions")
        css_links = [a["href"] for tag, a in doc.elements
                     if tag == "link" and a.get("rel") == "stylesheet"]
        self.assertEqual(css_links, [PUBLISHED_URL])
        links = [a.get("href", "") for tag, a in doc.elements if tag == "a"]
        self.assertIn("https://syntyr-css.pages.dev/docs/", links)
        self.assertTrue(all(x and x != "#" for x in links))
        self.assertIn(("main", {"class": "syn-root syn-shell",
                                "data-syn-theme": "studio"}), doc.elements)

    def test_all_example_classes_exist_in_published_css(self):
        doc = Markup()
        doc.feed(self.example)
        css = (ROOT / "site-releases" / VERSION /
               "syntyr.core.css").read_text(encoding="utf-8")
        classes = {part for _, attrs in doc.elements
                   for part in attrs.get("class", "").split()
                   if part.startswith("syn-")}
        self.assertTrue(classes)
        for name in sorted(classes):
            with self.subTest(class_name=name):
                self.assertIn("." + name, css,
                              f"{name} missing from the pinned public release")

    def test_self_hosting_copies_exact_published_version(self):
        self.assertIn("curl -fsSLo syntyr.core.css " + PUBLISHED_URL,
                      self.section)
        self.assertIn('href="./syntyr.core.css"', self.section)
        self.assertNotIn("alpha.5/syntyr.core.css", self.section)
        self.assertIn("self-host", self.section.lower())


if __name__ == "__main__":
    unittest.main()
