"""Contracts for opt-in editor, Tailwind and design-token interoperability."""
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PALETTES = ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal", "graphite", "midnight", "dim", "obsidian", "amethyst")
COLORS = ("bg", "surface", "surface-hi", "text", "muted", "accent", "accent-2",
          "on-accent", "frame", "frame-strong", "danger", "success", "warning")


class EcosystemAdaptersTest(unittest.TestCase):
    def test_generated_adapters_are_checked_in_and_current(self):
        result = subprocess.run(
            [sys.executable, "scripts/export_ecosystem_adapters.py", "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tailwind_v4_bridge_is_optional_and_uses_live_scoped_tokens(self):
        bridge = (ROOT / "integrations/tailwind/syntyr.theme.css").read_text()
        self.assertIn("@theme inline {", bridge)
        for name in COLORS:
            self.assertIn(f"--color-syntyr-{name}: var(--syn-{name});", bridge)
        self.assertNotIn("@import", bridge)
        self.assertNotIn("@apply", bridge)
        self.assertNotIn("@layer syn", bridge)
        self.assertNotIn("!important", bridge)
        core = (ROOT / "dist/syntyr.core.css").read_text()
        self.assertNotIn("@theme inline", core)

    def test_figma_mode_files_match_real_css_palettes(self):
        from scripts.export_ecosystem_adapters import read_palettes
        css_palettes = read_palettes((ROOT / "src/tokens.css").read_text())
        self.assertEqual(set(css_palettes), set(PALETTES))
        for theme in PALETTES:
            with self.subTest(theme=theme):
                doc = json.loads((ROOT / f"metadata/figma/syntyr-{theme}.tokens.json").read_text())
                self.assertEqual(set(doc), set(COLORS) | {"radius", "cut"})
                for color in COLORS:
                    token = doc[color]
                    self.assertEqual(token["$type"], "color")
                    value = token["$value"]
                    self.assertEqual(value["colorSpace"], "srgb")
                    self.assertEqual(value["hex"].lower(), css_palettes[theme][f"--syn-{color}"].lower())
                    self.assertEqual(value["alpha"], 1)
                    self.assertEqual(len(value["components"]), 3)
                    expected = [int(value["hex"][n:n + 2], 16) / 255 for n in (1, 3, 5)]
                    for actual, target in zip(value["components"], expected):
                        self.assertAlmostEqual(actual, target, places=6)
                for dimension in ("radius", "cut"):
                    item = doc[dimension]
                    self.assertEqual(item["$type"], "dimension")
                    self.assertEqual(item["$value"]["unit"], "px")
                    self.assertGreaterEqual(item["$value"]["value"], 0)

    def test_vscode_extension_bundles_generated_metadata_without_code(self):
        ext = ROOT / "integrations/vscode"
        pkg = json.loads((ext / "package.json").read_text())
        self.assertEqual(pkg["engines"]["vscode"].startswith("^"), True)
        contributes = pkg["contributes"]
        for kind in ("html", "css"):
            paths = contributes[kind]["customData"]
            self.assertEqual(len(paths), 1)
            file = ext / paths[0]
            self.assertTrue(file.is_file(), str(file))
            self.assertEqual(file.read_bytes(), (ROOT / "metadata" / file.name).read_bytes())
        self.assertEqual(set(x["language"] for x in contributes["snippets"]),
                         {"html", "javascriptreact", "typescriptreact"})
        for entry in contributes["snippets"]:
            snippet = ext / entry["path"]
            self.assertEqual(snippet.read_bytes(),
                             (ROOT / "metadata/syntyr.code-snippets").read_bytes())
        self.assertEqual(set(pkg["files"]), {"metadata/", "snippets/", "README.md", "LICENSE"})
        self.assertIn("repository", pkg)
        self.assertEqual((ext / "LICENSE").read_text(), (ROOT / "LICENSE").read_text())
        self.assertIn("Syntyr CSS", (ext / "README.md").read_text())
        self.assertNotIn("main", pkg)
        self.assertNotIn("activationEvents", pkg)
        self.assertNotIn("dependencies", pkg)


if __name__ == "__main__":
    unittest.main()
