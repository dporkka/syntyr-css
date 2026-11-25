"""Public static examples must expose working keyboard and ARIA semantics."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicAccessibilitySemantics(unittest.TestCase):
    def test_builder_preview_canvas_is_named_and_keyboard_scrollable(self):
        page = (ROOT / "docs/page-builder.html").read_text()
        css = (ROOT / "docs/page-builder.css").read_text()
        self.assertRegex(page, r'<div class="builder-canvas"[^>]*tabindex="0"'
                               r'[^>]*role="region"[^>]*aria-label="[^"]+"')
        self.assertIn(".builder-canvas:focus-visible", css)

    def test_static_read_only_grid_uses_table_not_interactive_grid_semantics(self):
        page = (ROOT / "examples/data-grid.html").read_text()
        self.assertIn('<section class="syn-data-grid">', page)
        self.assertRegex(page, r'<div class="syn-data-grid__viewport"[^>]*role="table"')
        self.assertIn('role="rowgroup"', page)
        self.assertIn('role="columnheader"', page)
        self.assertIn('role="cell"', page)
        self.assertNotIn('role="grid"', page)
        self.assertNotIn('role="gridcell"', page)
        self.assertNotIn('aria-selected="true"', page)
        self.assertNotRegex(page, r'role="cell"[^>]*tabindex=')

    def test_code_figure_keeps_caption_without_disallowed_pre_aria_name(self):
        page = (ROOT / "examples/native-recipes.html").read_text()
        self.assertIn('<figcaption id="snippet-caption">', page)
        code_start = re.search(r'<pre\b[^>]*>', page)
        self.assertIsNotNone(code_start)
        self.assertIn('tabindex="0"', code_start.group())
        self.assertNotIn('aria-labelledby', code_start.group())


if __name__ == "__main__":
    unittest.main()
