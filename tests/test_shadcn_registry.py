"""Fail-closed contracts for the optional copy-owned universal registry."""
from pathlib import Path
from scripts.build_shadcn_registry import DEFAULT_REGISTRY_URL
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
MANIFEST = json.loads((ROOT / "blocks/manifest.json").read_text(encoding="utf-8"))
MODULES = {"core": "syntyr.core.css", "recipes": "syntyr.recipes.css",
           "geometry": "syntyr.geometry.css", "symbols": "syntyr.symbols.css",
           "viz": "syntyr.viz.css", "geo": "syntyr.geo.css", "motion": "syntyr.motion.css",
           "effects": "syntyr.effects.css", "utilities": "syntyr.utilities.css"}


class UniversalRegistryTests(unittest.TestCase):
    def test_generated_registry_is_current_and_deterministic(self):
        result = subprocess.run([sys.executable, "scripts/build_shadcn_registry.py", "--check"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_free_blocks_and_css_modules_have_explicit_targets(self):
        index = json.loads((REGISTRY / "registry.json").read_text(encoding="utf-8"))
        names = {item["name"] for item in index["items"]}
        block_ids = {item["id"] for item in MANIFEST["blocks"]}
        self.assertEqual(names, block_ids | set(MODULES))
        self.assertEqual(index["$schema"], "https://ui.shadcn.com/schema/registry.json")
        self.assertEqual(index["name"], "syntyr")
        self.assertEqual(index["homepage"], "https://github.com/dporkka/syntyr-css")
        for item in index["items"]:
            self.assertEqual(item["type"], "registry:item")
            self.assertEqual(item["dependencies"], [])
            self.assertGreaterEqual(len(item["files"]), 2)
            self.assertEqual(item["files"][-1]["path"], "LICENSE")
            self.assertEqual(item["files"][-1]["target"], "~/syntyr/LICENSE")
            self.assertEqual(item["files"][0]["type"], "registry:file")
            self.assertTrue(item["files"][0]["target"].startswith("~/syntyr/"))
            payload = json.loads((REGISTRY / "r" / (item["name"] + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(payload["name"], item["name"])
            self.assertEqual(payload["type"], "registry:item")
            self.assertEqual(payload["files"][0]["target"], item["files"][0]["target"])
            self.assertIn("content", payload["files"][0])
            self.assertEqual(payload["files"][-1]["content"],
                             (ROOT / "LICENSE").read_text(encoding="utf-8"))
            self.assertNotIn("<script", payload["files"][0]["content"].lower())
            self.assertEqual(payload["dependencies"], [])
            self.assertEqual(payload["registryDependencies"], item.get("registryDependencies", []))
            self.assertEqual(payload["meta"]["syntyrVersion"],
                             (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        for item in MANIFEST["blocks"]:
            payload = json.loads((REGISTRY / "r" / (item["id"] + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(payload["registryDependencies"],
                             [DEFAULT_REGISTRY_URL + "/" + name + ".json" for name in item["modules"]])
            self.assertEqual(payload["files"][0]["content"],
                             (ROOT / "blocks/snippets" / (item["id"] + ".html")).read_text(encoding="utf-8"))

    def test_public_registry_is_explicitly_allowlisted(self):
        from scripts.build_cloudflare_site import source_files
        files = source_files()
        self.assertIn("registry/registry.json", files)
        for item in MANIFEST["blocks"]:
            self.assertIn("registry/r/" + item["id"] + ".json", files)
        self.assertNotIn("blocks/manifest.json", files)
        self.assertFalse(any(path.startswith("blocks/snippets/") for path in files))


class NativeStepTests(unittest.TestCase):
    def test_stepper_is_scoped_and_native(self):
        css = (ROOT / "src/components/patterns.css").read_text(encoding="utf-8")
        self.assertIn("&.syn-steps", css)
        self.assertIn("&.syn-step", css)
        self.assertIn('aria-current="step"', css)
        self.assertIn('data-syn-state="complete"', css)
        self.assertIn("syn-steps--vertical", css)
        self.assertIn("@container syn-region", css)

    def test_stepper_has_scriptless_example_and_docs(self):
        source = (ROOT / "examples/workflow-steps.html").read_text(encoding="utf-8")
        self.assertIn('<ol class="syn-steps"', source)
        self.assertIn('aria-current="step"', source)
        self.assertIn('data-syn-state="complete"', source)
        self.assertNotIn("<script", source)
        self.assertNotIn("javascript:", source)
        docs = (ROOT / "docs/components.md").read_text(encoding="utf-8")
        self.assertIn("Workflow steps", docs)
        self.assertIn("syn-steps--vertical", docs)
        self.assertIn("application", docs.lower())


if __name__ == "__main__":
    unittest.main()
