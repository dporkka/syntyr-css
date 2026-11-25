"""Opt-in minimalist framework ideas must not change Syntyr's zero-runtime contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MinimalistPatternsContract(unittest.TestCase):
    def test_system_palette_supports_nested_auto_with_native_color_scheme(self):
        css = (ROOT / "src/tokens.css").read_text()
        self.assertIn('.syn-root[data-syn-theme="auto"]', css)
        self.assertIn('.syn-root [data-syn-theme="auto"]', css)
        self.assertIn('color-scheme: light dark;', css)
        self.assertIn('light-dark(', css)
        self.assertIn('@supports (color: light-dark(', css)

    def test_auto_palette_remains_in_sync_with_named_studio_and_grid(self):
        import re
        from test_theme_utility_contract import theme_rules
        css = (ROOT / "src/tokens.css").read_text()
        start = css.index('.syn-root[data-syn-theme="auto"]')
        auto = css[css.index("{", start) + 1:css.index("}", start)]
        studio = theme_rules(css, "studio")
        grid = theme_rules(css, "grid")
        tokens = ("bg", "surface", "surface-hi", "text", "muted", "accent",
                  "accent-2", "on-accent", "frame", "frame-strong",
                  "danger", "success", "warning")
        for short in tokens:
            name = "--syn-" + short
            with self.subTest(token=name):
                match = re.search(re.escape(name) + r": light-dark\((.*?), (.*?)\);", auto)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), studio[name])
                self.assertEqual(match.group(2), grid[name])
        # The alpha is theme-specific and the tint tracks CSS token overrides.
        self.assertIn(
            '--syn-accent-soft: light-dark(' + studio['--syn-accent-soft']
            + ', ' + grid['--syn-accent-soft'] + ');', auto,
        )

    def test_intrinsic_layouts_and_fluid_tokens_are_recipes_only(self):
        css = (ROOT / "src/recipes.css").read_text()
        for fragment in (
            '.syn-sidebar', '.syn-switcher',
            '--syn-sidebar-width', '--syn-sidebar-content-min',
            '--syn-switcher-threshold',
            '--syn-fluid-display-size', '--syn-type-lede', '--syn-reading-width',
            '.syn-fluid-display', '.syn-fluid-lede', '.syn-reading',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, css)
                self.assertIn(fragment, (ROOT / "dist/syntyr.recipes.css").read_text())
                self.assertNotIn(fragment, (ROOT / "dist/syntyr.core.css").read_text())
        self.assertIn('--syn-type-display:', (ROOT / 'src/tokens.css').read_text())
        self.assertNotIn('--syn-type-display:', css, 'optional recipes must not shadow core typography')
        self.assertIn('flex-wrap: wrap', css)
        self.assertIn('clamp(', css)
        self.assertIn('min(100%', css)

    def test_semantic_checkbox_and_radio_labels_are_inline_without_global_reset(self):
        css = (ROOT / "src/semantic.css").read_text()
        self.assertIn('label:not([class]):has(', css)
        self.assertIn('label[data-syn-semantic]:has(', css)
        self.assertIn('> input[type="checkbox"]', css)
        self.assertIn('> input[type="radio"]', css)
        self.assertIn('align-items: center;', css)
        self.assertIn('display: block; cursor: pointer;', css)

    def test_source_and_dist_have_no_merge_conflict_markers(self):
        source_files = list((ROOT / "src").rglob("*.css"))
        source_files += list((ROOT / "dist").glob("*.css"))
        for path in source_files:
            with self.subTest(path=path):
                css = path.read_text()
                for marker in ("<<<<<<<", "|||||||", "=======", ">>>>>>>"):
                    self.assertNotIn(marker, css)

    def test_semantic_choice_controls_have_24px_hit_targets(self):
        css = (ROOT / "src/semantic.css").read_text()
        self.assertIn("min-inline-size: max(1.5rem, 24px);", css)
        self.assertIn("min-block-size: max(1.5rem, 24px);", css)
        self.assertIn('input[type="checkbox"][data-syn-semantic]', css)
        self.assertIn('input[type="radio"][data-syn-semantic]', css)

    def test_choice_targets_remain_24px_at_reduced_root_font_size_and_labels_wrap(self):
        css = (ROOT / "src/semantic.css").read_text()
        self.assertIn("min-inline-size: max(1.5rem, 24px)", css)
        self.assertIn("min-block-size: max(1.5rem, 24px)", css)
        self.assertIn("display: block; cursor: pointer;", css)
        self.assertIn("vertical-align: middle", css)

    def test_optional_browser_uses_documented_chromium_executable(self):
        source = (ROOT / "tests/minimalist_browser.py").read_text()
        self.assertIn("PLAYWRIGHT_CHROMIUM_EXECUTABLE", source)
        self.assertIn("executable_path", source)

    def test_real_html_example_uses_opt_in_css_and_accessible_controls(self):
        html = (ROOT / "examples/minimalist-patterns.html").read_text()
        for fragment in (
            'syntyr.core.css', 'syntyr.semantic.css', 'syntyr.recipes.css',
            'data-syn-theme="auto"', 'syn-semantic',
            'syn-sidebar', 'syn-switcher', 'syn-fluid-display',
            'type="checkbox"', 'for="email"', 'id="email"',
            'name="email"', 'type="submit"',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, html)
        self.assertIn('href="../examples/minimalist-patterns.html"',
                      (ROOT / "docs/index.html").read_text())
        from scripts.build_cloudflare_site import source_files
        self.assertIn("examples/minimalist-patterns.html", source_files())
        self.assertNotIn('<script', html)
        self.assertNotIn('onclick=', html)

    def test_distribution_has_no_new_runtime_or_build_dependency(self):
        src = (ROOT / "scripts/build.py").read_text()
        self.assertNotIn('npm ', src)
        self.assertIn("syntyr.recipes.css", src)
        self.assertIn("syntyr.semantic.css", src)


if __name__ == "__main__":
    unittest.main()
