"""Regression tests for the anonymized design-partner evidence scorecard."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commercial_pilot_report import load_rows, summarize  # noqa: E402


FIELDS = [
    "slot", "target_segment", "channel", "respondent", "status",
    "contacted_at", "interviewed_at", "intent", "paid_commitment", "notes",
]


def row(slot, status="not_contacted", intent="", commitment="", respondent="", notes=""):
    return {
        "slot": str(slot).zfill(2), "target_segment": "Go/templ",
        "channel": "", "respondent": respondent, "status": status,
        "contacted_at": "", "interviewed_at": "", "intent": intent,
        "paid_commitment": commitment, "notes": notes,
    }


class CommercialPilotReportTests(unittest.TestCase):
    def test_empty_seed_is_not_treated_as_revenue_or_validation(self):
        rows = load_rows(ROOT / "business/design-partner-pilot.csv")
        report = summarize(rows)
        self.assertEqual(report["slots"], 10)
        self.assertEqual(report["invited_total"], 0)
        self.assertEqual(report["interviews_completed"], 0)
        self.assertEqual(report["documented_commitments"], 0)
        self.assertEqual(report["purchase_evidence"], "not_collected")
        self.assertEqual(report["decision"], "needs_10_qualified_interviews")

    def test_progress_counts_interviewed_respondents_without_claiming_sales(self):
        rows = [
            row(1, "interviewed", "would_buy", "documented"),
            row(2, "interviewed", "maybe"),
            row(3, "declined"),
            row(4, "accepted"),
            row(5, "invited"),
            row(6),
        ]
        report = summarize(rows)
        self.assertEqual(report["invited_total"], 5)
        self.assertEqual(report["interviews_completed"], 2)
        self.assertEqual(report["would_buy"], 1)
        self.assertEqual(report["documented_commitments"], 1)
        self.assertEqual(report["purchase_evidence"], "not_collected")
        self.assertNotIn("revenue", report)
        self.assertNotIn("conversion_rate", report)

    def test_completed_interview_target_never_implies_checkout_ready(self):
        rows = [row(i, "interviewed", "would_buy") for i in range(1, 11)]
        report = summarize(rows)
        self.assertEqual(report["decision"], "review_commitments_and_launch_gates")
        self.assertEqual(report["documented_commitments"], 0)

    def test_invalid_data_is_rejected_instead_of_silently_counted(self):
        cases = [
            [row(1), row(1)],
            [row(1, "invented")],
            [row(1, "interviewed", "definitely")],
            [row(1, "invited", "would_buy")],
            [row(1, "interviewed", "would_buy", "yes")],
            [row(1, "accepted", "would_buy", "documented")],
        ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                summarize(rows)

    def test_private_csv_has_no_personal_details_in_json_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.csv"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerow(row(1, "interviewed", "would_buy", respondent="private name", notes="private context"))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/commercial_pilot_report.py"),
                 "--csv", str(path), "--json"],
                capture_output=True, text=True, check=True,
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["interviews_completed"], 1)
            self.assertNotIn("private name", result.stdout)
            self.assertNotIn("private context", result.stdout)

    def test_public_seed_does_not_contain_personal_details(self):
        rows = load_rows(ROOT / "business/design-partner-pilot.csv")
        self.assertTrue(all(not r["respondent"] and not r["notes"] for r in rows))


if __name__ == "__main__":
    unittest.main()
