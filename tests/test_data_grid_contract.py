"""Opt-in data-workspace styling contracts; no runtime framework dependency."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class DataGridContract(unittest.TestCase):
    def test_opt_in_module_and_zero_js_delivery(self):
        from scripts.build import distributions
        self.assertEqual(distributions()["syntyr.data-grid.css"], ("data-grid.css",))
        self.assertNotIn("data-grid.css", distributions()["syntyr.core.css"])
        self.assertTrue((ROOT / "dist/syntyr.data-grid.css").is_file())
        css = (ROOT / "src/data-grid.css").read_text()
        self.assertIn("@layer syn.components", css)
        self.assertIn(".syn-root", css)
        self.assertIn(".syn-data-grid", css)
        self.assertNotIn("javascript:", css)

    def test_accessible_cell_states_and_density(self):
        css = (ROOT / "src/data-grid.css").read_text()
        for state in ('[aria-selected="true"]', '[aria-invalid="true"]',
                      '[aria-readonly="true"]', '[data-syn-dirty="true"]',
                      ':focus-visible', 'forced-colors: active'):
            with self.subTest(state=state):
                self.assertIn(state, css)
        self.assertIn('data-syn-density="compact"', css)
        self.assertIn("font-variant-numeric: tabular-nums", css)
        self.assertIn(".syn-data-grid__header-row", css)

    def test_density_overrides_have_distinct_inherited_scopes(self):
        css = (ROOT / "src/data-grid.css").read_text()
        for value in ("2rem", "2.5rem", "3rem"):
            with self.subTest(value=value):
                self.assertIn(f"--syn-grid-density-row-block: {value}", css)
        self.assertIn("--syn-grid-row-block: var(--syn-grid-density-row-block, 2.5rem)", css)

    def test_keyboard_focus_is_distinct_from_selection_in_forced_colors(self):
        css = (ROOT / "src/data-grid.css").read_text()
        forced = css.split("@media (forced-colors: active)", 1)[-1]
        self.assertIn(".syn-data-grid__cell:focus-visible", forced)
        self.assertIn("3px double CanvasText", forced)

    def test_public_guide_and_example_are_both_allowlisted_and_indexed(self):
        from scripts.build_cloudflare_site import PUBLIC_DOCS, source_files
        self.assertIn("data-grid.md", PUBLIC_DOCS)
        files = source_files()
        self.assertIn("docs/data-grid.html", files)
        self.assertIn("examples/data-grid.html", files)
        self.assertIn(
            "https://syntyr-css.pages.dev/docs/data-grid.md",
            (ROOT / "llms.txt").read_text(),
        )
        self.assertIn(
            "## Source: docs/data-grid.md",
            (ROOT / "llms-full.txt").read_text(),
        )

    def test_nearest_density_scope_wins_and_comfortable_resets(self):
        css = (ROOT / "src/data-grid.css").read_text()
        for density in ("compact", "comfortable", "spacious"):
            with self.subTest(density=density):
                self.assertIn(f'.syn-root [data-syn-density="{density}"]', css)
        self.assertIn("--syn-grid-row-block: var(--syn-grid-density-row-block, 2.5rem)", css)
        self.assertIn("--syn-grid-pad-inline: var(--syn-grid-density-pad-inline, .65rem)", css)
        self.assertNotIn('.syn-root[data-syn-density="compact"] .syn-data-grid', css)

    def test_text_clipping_uses_shrinkable_element_not_anonymous_flex_item(self):
        css = (ROOT / "src/data-grid.css").read_text()
        self.assertIn(".syn-data-grid__cell-text", css)
        self.assertIn("flex: 0 1 auto", css)
        self.assertIn("text-overflow: ellipsis", css)
        self.assertIn('class="syn-data-grid__cell-text"', (ROOT / "examples/data-grid.html").read_text())
        self.assertIn("syn-data-grid__cell-text", (ROOT / "docs/data-grid.md").read_text())

    def test_keyboard_scrollable_viewport_ring_is_not_clipped_by_the_grid(self):
        """The tabindex="0" viewport gets the global outset focus ring, but
        `.syn-data-grid` clips it with `overflow: hidden` (1px of room against
        the 3px + 3px ring). A visible indicator must survive that clip."""
        css = (ROOT / "src/data-grid.css").read_text()
        grid = css.split(".syn-data-grid__viewport", 1)[0]
        self.assertIn("overflow: hidden", grid,
                      "Precondition: the grid still clips its viewport.")
        # The wrapper ring and the inner `outline: none` must both live inside
        # the :has() feature query, or a browser without :has() would lose the
        # only indicator it has.
        guarded = css.split("@supports selector(:has(*))", 1)
        self.assertEqual(len(guarded), 2, "The ring override must be feature-queried.")
        enhancement = guarded[1].split("\n  }", 1)[0]
        self.assertRegex(
            enhancement,
            r"\.syn-data-grid:has\(>\s*\.syn-data-grid__viewport:focus-visible\)\)?\s*\{[^}]*outline:",
            "The grid must paint the viewport's focus ring on the wrapper that "
            "overflow: hidden cannot clip.",
        )
        self.assertRegex(
            enhancement,
            r"\.syn-data-grid__viewport:focus-visible\)\)?\s*\{\s*outline:\s*none",
            "The inner outset ring must be removed so the two rings do not stack.",
        )

    def test_root_self_grid_keeps_visible_keyboard_focus(self):
        """A grid can itself be .syn-root, not only a descendant of one."""
        css = (ROOT / "src/data-grid.css").read_text()
        enhancement = css.split("@supports selector(:has(*))", 1)[1].split("\n  }", 1)[0]
        self.assertIn(
            ".syn-root.syn-data-grid:has(> .syn-data-grid__viewport:focus-visible)",
            enhancement,
            "Root-self grids must receive the wrapper outline before the inner one is removed.",
        )
        self.assertIn(
            ".syn-root .syn-data-grid:has(> .syn-data-grid__viewport:focus-visible)",
            enhancement,
            "Descendant grids must retain their existing wrapper focus treatment.",
        )

    def test_spreadsheet_pinning_uses_logical_offsets_and_opaque_background(self):
        css = (ROOT / "src/data-grid.css").read_text()
        self.assertIn('[data-syn-pin="start"]', css)
        self.assertIn('[data-syn-pin="end"]', css)
        self.assertIn("inset-inline-start: var(--syn-grid-pin-offset, 0px)", css)
        self.assertIn("inset-inline-end: var(--syn-grid-pin-offset, 0px)", css)
        self.assertIn("background: inherit", css)

    def test_range_and_conflict_states_preserve_forced_color_focus(self):
        css = (ROOT / "src/data-grid.css").read_text()
        for hook in ('[data-syn-range="true"]', '[data-syn-conflict="true"]'):
            self.assertIn(hook, css)
            self.assertIn(hook, css.split("@media (forced-colors: active)", 1)[1])
        self.assertIn("3px double CanvasText", css)

    def test_spreadsheet_hooks_document_host_ownership(self):
        guide = (ROOT / "docs/data-grid.md").read_text()
        for hook in ("data-syn-pin", "--syn-grid-pin-offset", "data-syn-range", "data-syn-conflict"):
            self.assertIn(hook, guide)
        example = (ROOT / "examples/data-grid.html").read_text()
        self.assertIn('data-syn-pin="start"', example)
        self.assertIn('data-syn-range="true"', example)
        self.assertIn('data-syn-conflict="true"', example)

    def test_static_html_example_is_self_contained(self):
        example = (ROOT / "examples/data-grid.html").read_text()
        self.assertIn("syntyr.data-grid.css", example)
        self.assertIn("syn-data-grid", example)
        self.assertIn('role="table"', example)
        self.assertNotIn('role="grid"', example)
        self.assertIn('data-syn-selected="true"', example)
        self.assertIn('[data-syn-selected="true"]', (ROOT / "src/data-grid.css").read_text())
        self.assertIn('role="row" aria-rowindex="1" class="syn-data-grid__header-row"', example)
        self.assertNotIn("<script", example.lower())

if __name__ == "__main__":
    unittest.main()
