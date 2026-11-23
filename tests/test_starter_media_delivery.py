"""Publishing contract: no 404 for browser starter and raster export modules."""
import unittest
from pathlib import Path
from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]

class StarterMediaDeliveryTests(unittest.TestCase):
    def test_starter_module_is_allowlisted_and_builder_controls_exist(self):
        files = source_files()
        self.assertIn("docs/page-builder-starters.mjs", files)
        page = files["docs/page-builder.html"].decode()
        self.assertIn('id="builder-starter"', page)
        self.assertIn('id="builder-apply-starter"', page)
        self.assertIn("createStarterPage", files["docs/page-builder-starters.mjs"].decode())
        js = files["docs/page-builder.js"].decode()
        self.assertIn('replaceBlockImage', js)
        self.assertIn('getImageAssetBytes', js)
        self.assertIn('image/png,image/jpeg,image/webp', js)

if __name__ == "__main__":
    unittest.main()
