"""Stable theme-token, native-control and optional-utility contracts."""
from pathlib import Path
from html.parser import HTMLParser
import re
import unittest

from test_contract import contrast

ROOT = Path(__file__).resolve().parents[1]
THEMES = ("grid", "noir", "studio", "industrial", "terminal", "corporate", "minimal")
REQUIRED_TOKENS = (
    "--syn-bg", "--syn-surface", "--syn-surface-hi", "--syn-text",
    "--syn-muted", "--syn-accent", "--syn-on-accent", "--syn-frame",
    "--syn-danger", "--syn-success", "--syn-warning", "--syn-accent-soft",
    "--syn-accent-2", "--syn-frame-strong",
)


def theme_rules(source, theme):
    selector = f'.syn-root[data-syn-theme="{theme}"]'
    start = source.find(selector)
    if start < 0:
        return None
    start = source.find("{", start)
    end = source.find("}", start)
    if start < 0 or end < 0:
        return None
    declarations = source[start + 1:end]
    return dict(re.findall(r'(--syn-[\w-]+|color-scheme):\s*([^;]+);', declarations))


class ThemeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.themes = set()
        self.scripts = 0
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "data-syn-theme" in values:
            self.themes.add(values["data-syn-theme"])
        if tag == "script":
            self.scripts += 1


class ThemeAndUtilitiesContract(unittest.TestCase):
    def test_seven_palettes_define_complete_accessible_tokens(self):
        source = (ROOT / "src/tokens.css").read_text()
        for name in THEMES:
            with self.subTest(theme=name):
                tokens = theme_rules(source, name)
                self.assertIsNotNone(tokens, f"missing theme: {name}")
                for token in REQUIRED_TOKENS:
                    self.assertIn(token, tokens)
                for foreground, background in (
                    ("--syn-text", "--syn-bg"),
                    ("--syn-text", "--syn-surface"),
                    ("--syn-muted", "--syn-surface"),
                    ("--syn-on-accent", "--syn-accent"),
                ):
                    self.assertGreaterEqual(
                        contrast(tokens[foreground], tokens[background]), 4.5,
                        f"{name}: {foreground} contrast against {background}",
                    )

    def test_themes_are_nested_and_native_controls_get_correct_color_scheme(self):
        source = (ROOT / "src/tokens.css").read_text()
        for name in THEMES:
            with self.subTest(theme=name):
                self.assertIn(f'.syn-root [data-syn-theme="{name}"]', source)
                tokens = theme_rules(source, name)
                self.assertEqual(tokens.get("color-scheme"),
                                 "light" if name in ("studio", "corporate", "minimal") else "dark")
                # Theme geometry token *names* are part of the extension
                # contract; aesthetic values are intentionally not frozen.
                for role in ("--syn-radius", "--syn-cut"):
                    self.assertIn(role, tokens)
                    self.assertTrue(tokens[role].strip(), f"{name}: empty {role}")

    def test_utilities_are_opt_in_and_built_deterministically(self):
        utilities = (ROOT / "src/utilities.css").read_text()
        self.assertIn("@layer syn.utilities", utilities)
        self.assertIn(".syn-root", utilities)
        for cls in ("syn-u-flex", "syn-u-grid", "syn-u-gap-2",
                    "syn-u-p-2", "syn-u-mt-2", "syn-u-sr-only"):
            with self.subTest(cls=cls):
                self.assertIn("." + cls, utilities)
                self.assertIn("." + cls, (ROOT / "dist/syntyr.utilities.css").read_text())
                self.assertIn("." + cls, (ROOT / "dist/syntyr.all.css").read_text())
                self.assertNotIn("." + cls, (ROOT / "dist/syntyr.core.css").read_text())
        self.assertNotIn("@import", utilities)
        self.assertNotIn("javascript", utilities.lower())
        self.assertIn("'syntyr.utilities.css'", (ROOT / "scripts/build.py").read_text())
        self.assertLess(utilities.index(".syn-u-center"), utilities.index(".syn-u-between"),
                        "between must win over centered justification when both are present")

    def test_release_includes_optional_utility_distribution(self):
        from scripts.package_release import FILES
        self.assertIn("dist/syntyr.utilities.css", FILES)

    def test_seven_theme_gallery_is_static_accessible_and_discoverable(self):
        demo = (ROOT / "examples/themes.html").read_text()
        parser = ThemeParser()
        parser.feed(demo)
        self.assertTrue(set(THEMES) <= parser.themes)
        self.assertEqual(parser.scripts, 0)
        self.assertIn("syntyr.utilities.css", demo)
        self.assertNotIn('class="syn-grid" aria-label=', demo, "unroled div should not have an aria-label")
        self.assertNotIn('<button type="button"', demo, "gallery controls must perform navigation")
        self.assertEqual(demo.count('href="../docs/#components"'), 7)
        self.assertIn('href="../examples/themes.html"', (ROOT / "docs/index.html").read_text())
        guide = (ROOT / "docs/theme-customization.md").read_text()
        for theme in THEMES:
            self.assertIn("data-syn-theme=\"" + theme + "\"", guide)
        self.assertIn("syntyr.utilities.css", guide)


if __name__ == "__main__":
    unittest.main()
