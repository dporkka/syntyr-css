"""Regression contracts for complete, honest matrix reporting."""
import unittest
from responsive_reporting import record_case, summarize


class ResponsiveReportingTest(unittest.TestCase):
    def test_failure_does_not_prevent_later_cases(self):
        results = []
        def broken():
            raise AssertionError("overflow")
        record_case(results, "chromium", "catalog.html", (320, 568, 1), broken)
        record_case(results, "chromium", "crm.html", (320, 568, 1), lambda: None)
        self.assertEqual([r["status"] for r in results], ["fail", "pass"])
        self.assertEqual(results[0]["error"], "overflow")
        self.assertEqual(summarize(results), {"pass": 1, "fail": 1, "blocked": 0})

    def test_blocked_engine_is_not_passed(self):
        self.assertEqual(summarize([{"status": "blocked"}]),
                         {"pass": 0, "fail": 0, "blocked": 1})

    def test_block_remaining_preserves_completed_cases(self):
        from responsive_reporting import block_remaining
        results = []
        viewports = [(320, 568, 1), (390, 844, 1)]
        record_case(results, "chromium", "a.html", viewports[0], lambda: None)
        block_remaining(results, "chromium", ["a.html", "b.html"], viewports, RuntimeError("context unavailable"))
        self.assertEqual(summarize(results), {"pass": 1, "fail": 0, "blocked": 3})
        self.assertEqual(len({(c["page"], c["width"]) for c in results}), 4)
