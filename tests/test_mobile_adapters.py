"""Contract tests for portable mobile tokens and React Native integration."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.export_ecosystem_adapters import COLORS, PALETTES, read_palettes

ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "metadata/mobile/syntyr.tokens.json"


class MobileAdaptersTest(unittest.TestCase):
    def test_mobile_artifacts_are_generated_and_current(self):
        result = subprocess.run(
            [sys.executable, "scripts/export_mobile_tokens.py", "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_palettes_match_css_without_derived_css_only_values(self):
        tokens = json.loads(MOBILE.read_text(encoding="utf-8"))
        palettes = read_palettes((ROOT / "src/tokens.css").read_text())
        self.assertEqual(tokens["schemaVersion"], 1)
        self.assertEqual(set(tokens["themes"]), set(PALETTES))
        self.assertEqual(tokens["unit"], "logical-points")
        for name in PALETTES:
            with self.subTest(name=name):
                theme = tokens["themes"][name]
                self.assertEqual(set(theme["colors"]), set(COLORS))
                for role in COLORS:
                    self.assertEqual(theme["colors"][role].lower(),
                                     palettes[name][f"--syn-{role}"].lower())
                    self.assertRegex(theme["colors"][role], r"^#[0-9A-Fa-f]{6}$")
                for dimension in ("radius", "cut"):
                    self.assertIsInstance(theme[dimension], (int, float))
                    self.assertGreaterEqual(theme[dimension], 0)
        self.assertEqual(tokens["spacing"], {"1": 6, "2": 12, "3": 18, "4": 28, "5": 40})
        self.assertEqual(tokens["fontSize"], {"xs": 12, "sm": 14, "base": 16})
        self.assertEqual(tokens["controlHeight"], 44)
        self.assertEqual(tokens["bodyLeading"], 1.55)
        self.assertNotIn("color-mix", MOBILE.read_text())
        self.assertNotIn("var(", MOBILE.read_text())

    def test_react_native_adapter_is_dependency_free_and_copyable(self):
        adapter = (ROOT / "integrations/react-native").resolve()
        tokens = (adapter / "tokens.ts").read_text()
        styles = (adapter / "styles.ts").read_text()
        self.assertIn("export const syntyrMobileTokens", tokens)
        self.assertIn("export type SyntyrMobileTheme", tokens)
        self.assertIn("createSyntyrNativeStyles", styles)
        self.assertIn("syntyrMobileTokens.themes[theme]", styles)
        self.assertNotIn("react-native", tokens.lower())
        self.assertNotIn("react-native", styles.lower())
        self.assertNotIn("var(--", styles)
        self.assertNotIn("className", styles)
        self.assertNotIn("gridTemplateColumns", styles)
        self.assertIn("StyleSheet.create", (ROOT / "examples/react-native/App.tsx").read_text())

    def test_ts_token_module_is_identical_to_portable_json(self):
        document = json.loads(MOBILE.read_text())
        typescript = (ROOT / "integrations/react-native/tokens.ts").read_text()
        literal = typescript.split("export const syntyrMobileTokens = ", 1)[1].split(" as const;", 1)[0]
        self.assertEqual(json.loads(literal), document)

    def test_native_tailwind_bridges_are_literal_complete_and_namespaced(self):
        from scripts.export_mobile_tokens import native_theme_css
        tokens = json.loads(MOBILE.read_text())
        directory = ROOT / "integrations/react-native/tailwind"
        self.assertEqual({p.stem for p in directory.glob("*.css")}, set(PALETTES))
        for name, palette in tokens["themes"].items():
            with self.subTest(theme=name):
                css = (directory / f"{name}.css").read_text()
                self.assertEqual(css, native_theme_css(tokens, name))
                self.assertEqual(css.count("@theme {"), 1)
                self.assertNotIn("var(", css)
                self.assertNotIn(".syn-root", css)
                self.assertNotIn("@import", css)
                declarations = {}
                for line in css.splitlines():
                    if line.strip().startswith("--"):
                        declaration = line.strip().removesuffix(";")
                        key, value = declaration.split(": ", 1)
                        self.assertNotIn(key, declarations)
                        declarations[key] = value
                expected = {
                    **{f"--color-syntyr-{key}": value for key, value in palette["colors"].items()},
                    **{f"--spacing-syntyr-{key}": f"{value}px" for key, value in tokens["spacing"].items()},
                    **{f"--text-syntyr-{key}": f"{value}px" for key, value in tokens["fontSize"].items()},
                    "--spacing-syntyr-control": f'{tokens["controlHeight"]}px',
                    "--radius-syntyr": f'{palette["radius"]}px',
                }
                self.assertEqual(declarations, expected)

    def test_nonliteral_body_leading_is_rejected(self):
        from scripts.export_mobile_tokens import mobile_tokens
        css = (ROOT / "src/tokens.css").read_text()
        with self.assertRaises(ValueError):
            mobile_tokens(css.replace("--syn-leading-body: 1.55;", "--syn-leading-body: calc(1 + .55);"))

    def test_non_literal_native_dimension_is_rejected(self):
        from scripts.export_mobile_tokens import to_points
        for bad in ("calc(1rem + 1px)", "var(--syn-space-1)", "12px", "auto"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                to_points(bad)

    def test_web_css_package_remains_native_runtime_free(self):
        package = json.loads((ROOT / "package.json").read_text())
        self.assertNotIn("react-native", str(package))
        self.assertNotIn("expo", package.get("dependencies", {}))
        self.assertNotIn("dependencies", package)
        self.assertTrue((ROOT / "docs/mobile-frameworks.md").is_file())
        doc = (ROOT / "docs/mobile-frameworks.md").read_text()
        for framework in ("Expo", "React Native", "Flutter", "SwiftUI", "Jetpack Compose", "Ionic", "Capacitor"):
            with self.subTest(framework=framework):
                self.assertIn(framework, doc)


if __name__ == "__main__":
    unittest.main()
