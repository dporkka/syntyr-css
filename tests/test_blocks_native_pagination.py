"""Static no-JavaScript progressive gallery contract."""
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

from scripts.build_blocks import build

ROOT = Path(__file__).resolve().parents[1]


class _GroupedContent(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.blocks = []
        self.icons = []
        self.block_groups = []
        self.icon_groups = []
        self.has_scroll_snap = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        classes = values.get("class", "").split()
        if "blocks-batch" in classes:
            self.block_groups.append({"tag": tag, "open": "open" in values,
                                      "cards": [], "label": values.get("aria-label", "")})
        if "blocks-icons-batch" in classes:
            self.icon_groups.append({"tag": tag, "open": "open" in values,
                                     "icons": []})
        ident = values.get("data-block-id")
        if ident:
            self.blocks.append(ident)
            if self.block_groups:
                self.block_groups[-1]["cards"].append(ident)
        ident = values.get("data-icon-id")
        if ident:
            self.icons.append(ident)
            if self.icon_groups:
                self.icon_groups[-1]["icons"].append(ident)


class BlocksNativePaginationTests(unittest.TestCase):
    def test_all_blocks_are_present_in_bounded_native_batches(self):
        html = build()
        parser = _GroupedContent()
        parser.feed(html)
        expected = [entry["id"] for entry in json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]]
        self.assertEqual(parser.blocks, expected)
        self.assertEqual([len(group["cards"]) for group in parser.block_groups], [12, 12, 12, 12, 12, 8])
        self.assertEqual([group["tag"] for group in parser.block_groups], ["section"] + ["details"] * 5)
        self.assertIn('id="blocks-grid" class="blocks-pages"', html)
        self.assertIn('href="#block-title-', html)

    def test_all_svg_icons_remain_pre_rendered_without_script(self):
        html = build()
        parser = _GroupedContent()
        parser.feed(html)
        expected = [entry["id"] for entry in json.loads((ROOT / "blocks/icons.json").read_text())["icons"]]
        self.assertEqual(parser.icons, expected)
        self.assertEqual([len(group["icons"]) for group in parser.icon_groups], [30, 30, 30, 30, 30])
        self.assertEqual([group["tag"] for group in parser.icon_groups], ["section"] + ["details"] * 4)
        self.assertIn('class="blocks-icons-pages"', html)

    def test_gallery_declares_accessible_no_js_scroll_navigation(self):
        html = build()
        self.assertIn("No JavaScript needed", html)
        self.assertIn("Show more blocks", html)
        self.assertIn("Show more SVG icons", html)
        style = (ROOT / "docs/blocks.css").read_text()
        self.assertIn("scroll-snap-type:inline proximity", style)
        self.assertIn("scroll-padding-inline", style)


if __name__ == "__main__":
    unittest.main()
