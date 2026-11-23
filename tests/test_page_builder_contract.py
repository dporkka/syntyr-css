"""Run Syntyr's optional visual builder model checks from the standard test suite."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PageBuilderModelTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is optional for the CSS-only core")
    def test_portable_page_schema_and_export_contract(self):
        result = subprocess.run(
            ["node", "--test", "tests/page_builder_model.test.mjs", "tests/page_builder_gallery.test.mjs",
             "tests/page_builder_sections.test.mjs", "tests/page_builder_zip.test.mjs",
             "tests/site_builder_model.test.mjs", "tests/synced_components.test.mjs"],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
