"""Interaction recipes must reference real controls, tests and explicit behavior owners."""
import copy
import json
from pathlib import Path
import unittest

from scripts.build_interaction_catalog import load_catalog, render_catalog, validate_catalog
from scripts.build_cloudflare_site import source_files
from scripts.package_release import FILES

ROOT = Path(__file__).resolve().parents[1]


class InteractionRecipeCatalogTests(unittest.TestCase):
    def test_catalog_validates_real_sources_and_rendered_guide_is_current(self):
        catalog = load_catalog()
        validate_catalog(catalog)
        self.assertEqual(catalog["source_version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(catalog["release_status"], "unreleased-source-candidate")
        recipes = catalog["recipes"]
        self.assertGreaterEqual(len(recipes), 8)
        self.assertEqual(len({r["id"] for r in recipes}), len(recipes))
        self.assertEqual({r["kind"] for r in recipes}, {"native", "headless"})
        output = (ROOT / "docs/interaction-recipes.md").read_text(encoding="utf-8")
        self.assertEqual(output, render_catalog(catalog))
        self.assertIn("does not certify accessibility", output)
        self.assertIn("unreleased alpha.5", output)
        self.assertIn("React Aria", output)
        self.assertIn("No JavaScript", output)
        self.assertIn("server-side", output)

    def test_catalog_fails_closed_on_untrusted_paths_missing_markers_and_duplicates(self):
        catalog = load_catalog()
        for field, value in (("source", "../../.env"), ("test_file", "https://example.com/x"),
                             ("docs", "/etc/passwd"), ("css", ["../../secret.css"])):
            with self.subTest(field=field):
                bad = copy.deepcopy(catalog)
                bad["recipes"][0][field] = value
                with self.assertRaises(ValueError):
                    validate_catalog(bad)
        bad = copy.deepcopy(catalog)
        bad["source_version"] = "0.0.0"
        with self.assertRaises(ValueError):
            validate_catalog(bad)
        bad = copy.deepcopy(catalog)
        bad["recipes"][1]["id"] = bad["recipes"][0]["id"]
        with self.assertRaises(ValueError):
            validate_catalog(bad)
        bad = copy.deepcopy(catalog)
        bad["recipes"][0]["source_markers"] = ["not-an-existing-widget-XYZ"]
        with self.assertRaises(ValueError):
            validate_catalog(bad)

    def test_first_class_public_distribution_and_zero_core_runtime(self):
        files = source_files()
        self.assertIn("metadata/interaction-recipes.json", set(files))
        self.assertIn("docs/interaction-recipes.md", set(files))
        self.assertIn("docs/interaction-recipes.html", set(files))
        for name in ("metadata/interaction-recipes.json", "docs/interaction-recipes.md"):
            self.assertIn(name, FILES)
        self.assertIn("docs/interaction-recipes.md", (ROOT / "llms.txt").read_text())
        self.assertIn("docs/interaction-recipes.md", (ROOT / "README.md").read_text())
        self.assertIn("docs/interaction-recipes.md", (ROOT / "scripts/build_agent_docs.py").read_text())
        self.assertFalse(list((ROOT / "src").rglob("*.js")))
        package = json.loads((ROOT / "package.json").read_text())
        self.assertNotIn("dependencies", package)
        self.assertNotIn("react-aria-components", str(package))

    def test_native_browser_matrix_is_an_active_release_gate(self):
        from tests.test_ci_contract import active_workflow_command_position
        workflow = (ROOT / ".woodpecker/browser.yaml").read_text()
        command = "python3 tests/interaction_recipe_browser.py --browsers chromium firefox webkit"
        self.assertGreaterEqual(active_workflow_command_position(workflow, command), 0)
        self.assertLess(
            active_workflow_command_position(workflow, "python3 tests/browser_matrix.py --browsers chromium firefox webkit"),
            active_workflow_command_position(workflow, command),
        )

    def test_catalog_native_and_headless_have_different_verification_and_fallbacks(self):
        for recipe in load_catalog()["recipes"]:
            with self.subTest(recipe=recipe["id"]):
                self.assertTrue(recipe["keyboard"])
                self.assertTrue(recipe["fallback"])
                self.assertTrue(recipe["source_markers"])
                self.assertTrue(recipe["test_markers"])
                if recipe["kind"] == "native":
                    self.assertEqual(recipe["test_file"], "tests/interaction_recipe_browser.py")
                else:
                    self.assertEqual(recipe["test_file"], "examples/headless-react/tests/interactions.spec.ts")


if __name__ == "__main__":
    unittest.main()
