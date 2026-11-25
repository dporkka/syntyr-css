"""Developer feedback pilot and honest browser-support evidence."""
from pathlib import Path
import csv
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PilotReadinessTests(unittest.TestCase):
    def test_accessibility_matrix_documents_success_and_unverified_gates(self):
        doc = (ROOT / "docs/accessibility.md").read_text()
        self.assertIn("WebKit", doc)
        self.assertIn("v1.65.2-noble", doc)
        self.assertIn("126", doc)
        self.assertIn("168", doc)
        self.assertIn("manual", doc.lower())
        self.assertIn("400%", doc)
        self.assertIn("not equivalent", doc.lower())

    def test_public_design_partner_seed_is_safe_and_progress_can_be_recorded(self):
        with (ROOT / "business/design-partner-pilot.csv").open(newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({row["slot"] for row in rows}), 10)
        self.assertTrue(all(not row["respondent"] and not row["notes"] for row in rows))
        # The public template must permit honest status changes after interviews.
        self.assertTrue(all(row["status"] in {
            "not_contacted", "invited", "accepted", "interviewed", "declined"
        } for row in rows))

    def test_design_partner_pilot_includes_qualification_and_outreach_boundaries(self):
        guide = (ROOT / "business/design-partner-pilot.md").read_text()
        for item in ("Go/templ", "HTMX", "CRM", "10", "$59", "consent", "paid",
                     "https://github.com/dporkka/syntyr-css/issues"):
            self.assertIn(item, guide)
        self.assertIn("not_contacted", guide)

    def test_public_entry_points_show_opt_in_feedback_action(self):
        home = (ROOT / "index.html").read_text()
        gallery = (ROOT / "docs/index.html").read_text()
        for html in (home, gallery):
            self.assertIn("https://github.com/dporkka/syntyr-css/issues/3", html)
        self.assertIn('id="feedback"', gallery)

    def test_kit_preview_cards_use_a_defined_theme_surface(self):
        page = (ROOT / "docs/console-kit.html").read_text()
        self.assertIn('background:var(--syn-surface)', page)
        self.assertNotIn('var(--syn-panel)', page)

    def test_public_kit_copy_truthfully_distinguishes_private_preview_from_sale(self):
        page = (ROOT / "docs/console-kit.html").read_text()
        self.assertIn("PRIVATE PROTOTYPE", page)
        self.assertIn("12 original screen types", page)
        self.assertIn("36 static variants", page)
        self.assertIn("eight screenshots below", page)
        self.assertIn("NOT AVAILABLE FOR PURCHASE", page)
        self.assertNotIn("BUY NOW", page)
        spec = (ROOT / "business/console-kit-spec.md").read_text()
        self.assertIn("private prototype", spec.lower())
        self.assertIn("not for sale", spec.lower())
        pilot = (ROOT / "business/design-partner-pilot.md").read_text()
        self.assertIn("private prototype", pilot.lower())

    def test_kit_page_has_clear_non_sale_feedback_link(self):
        page = (ROOT / "docs/console-kit.html").read_text()
        self.assertIn("NOT AVAILABLE FOR PURCHASE", page)
        self.assertIn("console-kit-feedback.yml", page)
        self.assertIn("https://github.com/dporkka/syntyr-css/issues/3", page)
        self.assertNotIn('href="/checkout"', page)


if __name__ == "__main__":
    unittest.main()
