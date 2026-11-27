"""Public reporting must never imply coverage that was not executed."""
import unittest
import json
from pathlib import Path
from scripts.build_responsive_compatibility import build_report, render_html

SHA = "a" * 40
DATE = "2026-11-25"
VIEW = {"width": 320, "height": 568, "textScale": 1}


class ResponsiveCompatibilityTests(unittest.TestCase):
    def case(self, engine="chromium", status="pass", page="docs/example.html"):
        return {"engine": engine, "page": page, "status": status, **VIEW}

    def test_missing_engine_is_not_tested(self):
        report = build_report([self.case()], SHA, DATE)
        row = report["matrix"][0]
        self.assertEqual(row["engines"]["chromium"]["status"], "pass")
        self.assertEqual(row["engines"]["webkit"]["status"], "not-tested")

    def test_partial_matrix_cannot_pass(self):
        report = build_report([self.case(), self.case("firefox"),
                               self.case(page="docs/other.html")], SHA, DATE)
        self.assertEqual(report["matrix"][0]["engines"]["firefox"]["status"], "partial")

    def test_failed_and_blocked_are_distinct_and_errors_not_public(self):
        cases = [self.case(status="fail"), self.case("webkit", "blocked")]
        cases[0]["error"] = "private local path"
        report = build_report(cases, SHA, DATE)
        self.assertEqual(report["matrix"][0]["engines"]["chromium"]["status"], "fail")
        self.assertEqual(report["matrix"][0]["engines"]["webkit"]["status"], "blocked")
        self.assertNotIn("private local path", str(report))
        self.assertIn("not a WCAG certification", render_html(report))

    def test_duplicate_case_rejected(self):
        with self.assertRaises(ValueError):
            build_report([self.case(), self.case()], SHA, DATE)


    def test_checked_in_dashboard_matches_public_metadata(self):
        root = Path(__file__).resolve().parents[1]
        report = json.loads((root / "metadata/responsive-compatibility.v1.json").read_text())
        self.assertEqual((root / "docs/responsive-compatibility.html").read_text(),
                         render_html(report))
        self.assertEqual(len(report["pages"]), report["pageCount"])
        for row in report["matrix"]:
            for result in row["engines"].values():
                self.assertEqual(sum(result[k] for k in ("pass", "fail", "blocked", "notTested")),
                                 report["pageCount"])
