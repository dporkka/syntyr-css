"""Optional geometry, terminal and native-state regression contracts."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GeometryTerminalContract(unittest.TestCase):
    def test_geometry_is_opt_in_and_ships_as_independent_module(self):
        geometry = (ROOT / "src/geometry.css").read_text()
        build = (ROOT / "scripts/build.py").read_text()
        self.assertIn("syn.geometry", geometry)
        self.assertIn("'syntyr.geometry.css': ('geometry.css',)", build)
        self.assertIn("'geometry.css'", build)
        self.assertIn(".syn-frame--bevel", geometry)
        self.assertIn(".syn-frame--notch", geometry)
        self.assertIn(".syn-frame--bracket", geometry)
        self.assertIn(".syn-frame--inset", geometry)
        self.assertIn(".syn-frame--circuit", geometry)
        self.assertIn("--syn-frame-cut", geometry)
        self.assertIn("--syn-frame-stroke", geometry)
        self.assertIn("@media (forced-colors: active)", geometry)
        core = (ROOT / "dist/syntyr.core.css").read_text()
        all_css = (ROOT / "dist/syntyr.all.css").read_text()
        self.assertNotIn(".syn-frame--bevel", core)
        self.assertIn(".syn-frame--bevel", all_css)

    def test_table_emphasis_is_opt_in(self):
        css = (ROOT / "src/components/data.css").read_text()
        self.assertNotIn("td:last-child", css)
        self.assertIn(".syn-table-emphasis", css)
        self.assertIn(".syn-cell--numeric", css)
        self.assertIn("font-variant-numeric: tabular-nums", css)

    def test_long_technical_captions_wrap_at_text_zoom(self):
        typography = (ROOT / "src/components/typography.css").read_text()
        self.assertIn("overflow-wrap: anywhere", typography.split(".syn-caption {", 1)[1].split("}", 1)[0])

    def test_stack_grid_allows_terminal_to_shrink_to_mobile_viewport(self):
        layout = (ROOT / "src/components/layout.css").read_text()
        self.assertIn(".syn-stack { display: grid; grid-template-columns: minmax(0, 1fr);", layout)

    def test_nested_geometry_tokens_are_respected(self):
        css = (ROOT / "src/geometry.css").read_text()
        root = css.split(".syn-frame {", 1)[1].split("}", 1)[0]
        for token in ("--syn-frame-cut:", "--syn-frame-stroke:",
                      "--syn-frame-fill:", "--syn-frame-outline:"):
            self.assertNotIn(token, root, "frames must not overwrite inherited tokens")
        for default in ("var(--syn-frame-cut, 1rem)", "var(--syn-frame-stroke, 1px)",
                        "var(--syn-frame-fill, var(--syn-surface))",
                        "var(--syn-frame-outline, var(--syn-frame-strong))"):
            self.assertIn(default, css)

    def test_disabled_button_hover_states_are_excluded(self):
        css = (ROOT / "src/components/buttons.css").read_text()
        for variant in (".syn-button", ".syn-button--primary", ".syn-button--outline",
                        ".syn-button--danger", ".syn-button--ghost"):
            self.assertIn(variant + ":where(:not(:disabled):not([aria-disabled=\"true\"]):hover)", css)
        self.assertIn("cursor: not-allowed", css)

    def test_aria_disabled_is_not_functionally_disabled_by_css(self):
        css = (ROOT / "src/components/buttons.css").read_text()
        self.assertNotIn("pointer-events: none", css)
        docs = (ROOT / "docs/components.md").read_text()
        self.assertIn("aria-disabled", docs)
        self.assertIn("does not block activation", docs)

    def test_terminal_readouts_and_states_are_optional(self):
        css = (ROOT / "src/recipes.css").read_text()
        for selector in (".syn-terminal-title", ".syn-terminal-dots", ".syn-terminal-output",
                         ".syn-terminal-error", ".syn-terminal-warning", ".syn-terminal-cursor",
                         ".syn-terminal-path", ".syn-terminal-meta"):
            with self.subTest(selector=selector):
                self.assertIn(selector, css)
        self.assertNotIn("@keyframes", css)
        self.assertIn("prefers-reduced-motion", (ROOT / "src/base.css").read_text())

    def test_original_gallery_has_geometry_terminal_example_without_javascript(self):
        page = (ROOT / "examples/geometry-terminal.html").read_text()
        for value in ("syn-frame--bevel", "syn-frame--bracket", "syn-frame--notch",
                      "syn-frame--inset", "syn-frame--circuit", "syn-terminal", "<main",
                      "syn-table-emphasis", "syn-terminal-error", "syn-terminal-warning"):
            with self.subTest(value=value):
                self.assertIn(value, page)
        self.assertIn('href="#main"', page)
        self.assertIn('<main id="main">', page)
        self.assertNotIn("<script", page.lower())
        self.assertIn("geometry-terminal.html", (ROOT / "docs/index.html").read_text())
        self.assertIn("dist/syntyr.geometry.css", page)

    def test_standalone_distribution_is_tracked_for_clean_checkouts(self):
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "dist/syntyr.geometry.css", "dist/syntyr.geometry.css"],
            cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, "generated geometry CSS must be committed, not only built locally")

    def test_download_package_includes_geometry(self):
        from scripts.package_release import FILES
        self.assertIn("dist/syntyr.geometry.css", FILES)


if __name__ == "__main__":
    unittest.main()
