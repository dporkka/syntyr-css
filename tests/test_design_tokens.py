"""Portable design-token snapshots preserve source aliases and mode boundaries."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.export_design_tokens import export_tokens

ROOT = Path(__file__).resolve().parents[1]


class DesignTokenTests(unittest.TestCase):
    def test_theme_colors_and_density_are_independent(self):
        studio = export_tokens("studio", "compact")
        grid = export_tokens("grid", "compact")
        comfortable = export_tokens("studio", "comfortable")
        self.assertEqual(studio["palette"]["accent"]["$value"]["hex"], "#2458C6")
        self.assertNotEqual(studio["palette"]["accent"], grid["palette"]["accent"])
        self.assertEqual(studio["foundation"]["control-height"]["$value"], {"value": 2.25, "unit": "rem"})
        self.assertEqual(comfortable["foundation"]["control-height"]["$value"], {"value": 2.75, "unit": "rem"})
        self.assertEqual(studio["foundation"]["type-sm"], comfortable["foundation"]["type-sm"])

    def test_aliases_preserve_css_relationships_and_dynamic_values_are_omitted(self):
        tokens = export_tokens("studio", "compact")
        self.assertEqual(tokens["foundation"]["card-padding"]["$value"], "{foundation.space-2}")
        self.assertEqual(tokens["semantic"]["border-focus"]["$value"], "{palette.accent}")
        self.assertEqual(tokens["semantic"]["border-focus"]["$type"], "color")
        self.assertNotIn("type-heading", tokens["foundation"])
        self.assertNotIn("space-fluid-1", tokens["foundation"])
        self.assertNotIn("surface-raised", tokens["semantic"])

    def test_every_alias_resolves_to_same_typed_token_for_every_mode(self):
        from scripts.export_ecosystem_adapters import PALETTES
        for theme in PALETTES:
            for density in ("compact", "comfortable", "spacious"):
                tokens = export_tokens(theme, density)
                for group in tokens.values():
                    for token in group.values():
                        value = token["$value"]
                        if isinstance(value, str) and value.startswith("{"):
                            category, name = value[1:-1].split(".")
                            target = tokens[category][name]
                            self.assertEqual(token["$type"], target["$type"])
                            self.assertIsInstance(target["$value"], dict)

    def test_cli_writes_json_and_rejects_unknown_mode(self):
        command = [sys.executable, "scripts/export_design_tokens.py", "--theme", "studio"]
        result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), export_tokens("studio", "comfortable"))
        bad = subprocess.run(command + ["--density", "unknown"], cwd=ROOT, capture_output=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertEqual(bad.stdout, b"")


if __name__ == "__main__":
    unittest.main()
