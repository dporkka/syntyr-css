"""Generated public Markdown guides must expose scrollable code to keyboards."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

from scripts.build_cloudflare_site import PUBLIC_DOCS

# The hosting build has no Markdown authoring dependency. This test reads
# generated HTML only, so the public-doc allowlist is the correct source.
GUIDES = tuple(name for name in PUBLIC_DOCS if name.endswith(".md"))

ROOT = Path(__file__).resolve().parents[1]


class CodeBlocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.blocks.append(dict(attrs))


class GeneratedCodeFocusTests(unittest.TestCase):
    def test_every_generated_guide_pre_is_keyboard_focusable(self):
        total = 0
        for filename in GUIDES:
            page = ROOT / "docs" / (filename.removesuffix(".md") + ".html")
            parser = CodeBlocks()
            parser.feed(page.read_text(encoding="utf-8"))
            for attrs in parser.blocks:
                total += 1
                with self.subTest(page=page.name, attrs=attrs):
                    self.assertEqual(attrs.get("tabindex"), "0")
                    self.assertNotIn("role", attrs)
        self.assertGreater(total, 100)


if __name__ == "__main__":
    unittest.main()
