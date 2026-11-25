"""CSS-first typography and development-only text diagnostics contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return (ROOT / name).read_text(encoding="utf-8")


class TypographyLabContract(unittest.TestCase):
    def test_heading_wrapping_is_resilient(self):
        text = source("src/components/typography.css")
        self.assertIn("min-inline-size: 0; overflow-wrap: anywhere;", text)
        self.assertIn("min-inline-size: 0;", text)

    def test_explicit_typography_utilities_exist(self):
        text = source("src/utilities.css")
        for name in ("syn-u-text-safe", "syn-u-text-pretty", "syn-u-text-balance"):
            self.assertIn("." + name, text)
        self.assertIn("overflow-wrap: anywhere;", text)

    def test_typography_lab_is_in_existing_playground(self):
        html = source("docs/playground.html")
        for name in ("typography-title", "type-lab-text", "type-lab-width", "type-lab-preview", "type-lab-report"):
            self.assertIn('id="' + name + '"', html)
        self.assertIn("playground.js", html)
        self.assertNotIn("@chenglou/pretext", source("package.json"))

    def test_predictor_remains_optional(self):
        js = source("integrations/pretext/audit.mjs")
        self.assertIn("export function", js)
        self.assertNotIn('from "@chenglou/pretext"', js)
        self.assertNotIn("pretext", source("src/components/typography.css").lower())


if __name__ == "__main__":
    unittest.main()
