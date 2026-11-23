"""No-runtime visual section picker stays inside optional page-builder tooling."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VisualSectionPickerContractTests(unittest.TestCase):
    def test_public_builder_exposes_accessible_grouping_preview_and_insert_controls(self):
        html = (ROOT / "docs/page-builder.html").read_text()
        for id_ in ("builder-section-use-case", "builder-section-search",
                    "builder-section-category", "builder-section-preview-dialog",
                    "builder-section-preview-frame", "builder-section-preview-add",
                    "builder-section-preview-close", "builder-insert-after"):
            with self.subTest(id=id_):
                self.assertIn(f'id="{id_}"', html)
        self.assertIn('aria-haspopup', (ROOT / "docs/page-builder.js").read_text())
        self.assertIn('sandbox="allow-same-origin"', html)
        self.assertIn('aria-labelledby="builder-section-preview-title"', html)

    def test_browser_only_picker_is_in_static_site_allowlist_not_consumer_css(self):
        from scripts.build_cloudflare_site import source_files
        files = source_files()
        self.assertIn("docs/page-builder-section-picker.mjs", files)
        self.assertIn("docs/page-builder.js", files)
        picker = (ROOT / "docs/page-builder-section-picker.mjs").read_text()
        self.assertNotIn("fetch(", picker)
        self.assertNotIn("innerHTML", picker)
        self.assertNotIn("<script", picker)
        export_model = (ROOT / "docs/page-builder-model.mjs").read_text()
        self.assertIn('href="syntyr.all.css"', export_model)
        self.assertNotIn("page-builder-section-picker", export_model)
        self.assertNotIn("page-builder-section-picker", (ROOT / "package.json").read_text())

    def test_live_preview_does_not_introduce_user_html_or_remote_assets(self):
        js = (ROOT / "docs/page-builder.js").read_text()
        self.assertIn('createBlock(type, "section-picker-preview")', js)
        self.assertIn("sandboxedPreviewHtml(example)", js)
        self.assertIn('sectionPreviewDialog.showModal()', js)
        self.assertIn("addBlockType(previewedSectionType)", js)
        self.assertIn('sectionPreviewFrame.srcdoc = ""', js)
        self.assertIn("event.preventDefault()", js)
        self.assertNotIn("innerHTML =", js)


if __name__ == "__main__":
    unittest.main()
