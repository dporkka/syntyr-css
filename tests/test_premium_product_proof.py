"""Public Pro and Studio evidence must be genuine approved images only, not private code."""
from pathlib import Path
import re
import unittest

from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]
PROOFS = (
    ("pro", "pro-work-orders-studio.webp", "Pro work-order queue"),
    ("studio", "studio-saas-home.webp", "Studio B2B SaaS homepage"),
)


class PremiumProductProofTests(unittest.TestCase):
    def test_each_premium_product_page_has_real_independent_visual_proof(self):
        published = source_files()
        for product, filename, alt in PROOFS:
            with self.subTest(product=product):
                page = (ROOT / "docs" / f"{product}.html").read_text(encoding="utf-8")
                image = ROOT / "docs/previews" / filename
                self.assertTrue(image.is_file())
                self.assertEqual(image.read_bytes()[:4], b"RIFF")
                self.assertEqual(image.read_bytes()[8:12], b"WEBP")
                self.assertIn(f'src="previews/{filename}"', page)
                self.assertIn(f'alt="{alt}', page)
                self.assertIn('loading="lazy"', page)
                self.assertIn(f'<link rel="canonical" href="https://syntyr-css.pages.dev/docs/{product}.html">', page)
                self.assertIn(f'<meta property="og:image" content="https://syntyr-css.pages.dev/docs/previews/{filename}">', page)
                self.assertIn('<meta name="twitter:card" content="summary_large_image">', page)
                self.assertIn(f"docs/previews/{filename}", published)
                self.assertIn("static screenshot", page.lower())
                self.assertIn("fictional", page.lower())
                self.assertIn("not for sale", page.lower())
                self.assertNotIn("application/ld+json", page)

    def test_agent_index_identifies_available_static_proof_without_promising_sales(self):
        index = (ROOT / "llms.txt").read_text(encoding="utf-8")
        for product, filename, _ in PROOFS:
            with self.subTest(product=product):
                item = next(line for line in index.splitlines()
                            if f"[Syntyr {product.title()} concept]" in line)
                self.assertIn("static screenshot", item.lower())
                self.assertIn("fictional", item.lower())
                self.assertIn(filename, item)
                self.assertIn("not for sale", item.lower())
                self.assertIn("no premium source", item.lower())

    def test_approved_raster_allowlist_is_exact_and_private_source_excluded(self):
        published = source_files()
        original = {
            "studio-overview.webp", "grid-resources.webp", "noir-billing.webp",
            "studio-editor.webp", "studio-settings.webp", "grid-detail.webp",
            "noir-team.webp", "grid-sign-in.webp",
        }
        expected = {"docs/previews/" + x for x in original}
        expected.update("docs/previews/" + filename for _, filename, _ in PROOFS)
        self.assertEqual({p for p in published if p.startswith("docs/previews/")}, expected)
        self.assertFalse(any(p.startswith(("products/", "private/", "premium-dist/", "business/")) for p in published))
        for product, _, _ in PROOFS:
            html = (ROOT / "docs" / f"{product}.html").read_text(encoding="utf-8")
            self.assertIsNone(re.search(r'<(?:script|form)\b', html, re.I))


if __name__ == "__main__":
    unittest.main()
