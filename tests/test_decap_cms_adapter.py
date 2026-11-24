"""A third editor targets the established portable CMS JSON, not a new format."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CMS = ROOT / "examples/cms-starter"


class DecapAdapterTests(unittest.TestCase):
    def test_editor_matches_existing_contract_without_core_dependencies(self):
        config = (CMS / "decap/config.yml").read_text()
        self.assertIn("file: content/pages/home.json", config)
        self.assertIn("format: json", config)
        self.assertIn("typeKey: type", config)
        self.assertIn("publish_mode: editorial_workflow", config)
        for kind in ("hero", "features", "pricing", "faq", "cta"):
            with self.subTest(kind=kind):
                self.assertIn(f"- name: {kind}\n                widget: object", config)
        self.assertEqual(config.count("name: id,"), 5)
        self.assertEqual(config.count("name: button"), 3)
        self.assertNotIn("decap-cms", (ROOT / "package.json").read_text())

    def test_editor_script_is_pinned_and_is_not_shipped_to_site_by_default(self):
        html = (CMS / "decap/index.html").read_text()
        self.assertIn("decap-cms@3.18.0", html)
        source = (ROOT / "scripts/render_cms_starter.py").read_text()
        self.assertIn('source / "admin" / name', source)
        self.assertNotIn('source / "decap" / name', source)


if __name__ == "__main__":
    unittest.main()
