"""Commercial research page safeguards for real, non-sale Console Kit previews."""
import unittest
from pathlib import Path

from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = (
    ("studio-overview.webp", "Studio dashboard"),
    ("grid-resources.webp", "Grid resource index"),
    ("noir-billing.webp", "Noir billing overview"),
    ("studio-editor.webp", "Studio create/edit form"),
    ("studio-settings.webp", "Studio settings"),
    ("grid-detail.webp", "Grid resource detail"),
    ("noir-team.webp", "Noir team management"),
    ("grid-sign-in.webp", "Grid sign-in"),
)


class CommercialPreviewTests(unittest.TestCase):
    def test_preview_uses_actual_locally_hosted_screen_images(self):
        page = (ROOT / "docs/console-kit.html").read_text(encoding="utf-8")
        for filename, alt in PREVIEWS:
            with self.subTest(filename=filename):
                path = ROOT / "docs/previews" / filename
                self.assertTrue(path.is_file(), f"Missing screen capture {filename}")
                self.assertEqual(path.read_bytes()[:4], b"RIFF")
                self.assertEqual(path.read_bytes()[8:12], b"WEBP")
                self.assertIn(f'src="previews/{filename}"', page)
                self.assertIn(f'alt="{alt}', page)
        self.assertIn('loading="lazy"', page)
        self.assertIn("STATIC / SAMPLE DATA", page)

    def test_only_original_console_and_two_premium_approved_previews_are_distributed(self):
        site = source_files()
        published = sorted(p for p in site if p.startswith("docs/previews/"))
        # The Console gallery remains exactly eight approved captures. Two
        # additional premium *marketing screenshots* have separate product pages.
        approved_premium_proofs = ("pro-work-orders-studio.webp", "studio-saas-home.webp")
        expected = sorted("docs/previews/" + filename for filename, _ in PREVIEWS)
        expected += ["docs/previews/" + filename for filename in approved_premium_proofs]
        self.assertEqual(published, sorted(expected))
        self.assertFalse(any(p.startswith("business/") for p in site))
        self.assertFalse(any(p.startswith("private/") for p in site))

    def test_preview_is_explicitly_not_checkout_or_live_application(self):
        page = (ROOT / "docs/console-kit.html").read_text(encoding="utf-8")
        for phrase in ("NOT AVAILABLE FOR PURCHASE", "private prototype",
                       "not a purchase form", "synthetic data", "No payment is being accepted"):
            self.assertIn(phrase.lower(), page.lower())
        self.assertNotIn('href="/checkout"', page)
        self.assertNotIn("<script", page.lower(), "Public preview must remain static")
        self.assertIn("MIT", page, "Keep OSS licensing distinct from paid concepts")
        self.assertIn("console-kit-feedback.yml", page)

    def test_feedback_qualifies_real_buyers_without_collecting_public_secrets(self):
        issue_form = (ROOT / ".github/ISSUE_TEMPLATE/console-kit-feedback.yml").read_text(encoding="utf-8")
        self.assertIn("public", issue_form.lower())
        self.assertIn("previous-ui-purchase", issue_form)
        self.assertIn("current-project", issue_form)
        self.assertIn("integration-blocker", issue_form)
        self.assertIn("No sale or preorder", issue_form)



if __name__ == "__main__":
    unittest.main()
