"""The manual-review queue must not silently drop or approve audit findings."""
import copy
import unittest

from contrast_review_queue import build_queue


class ReviewQueueTests(unittest.TestCase):
    def setUp(self):
        self.item = {"page": "example.html", "selector": ["#label"], "failure_summary": "gradient"}
        self.axe = {"pages": [{"page": "example.html", "incomplete": [
            dict(self.item, rule="color-contrast"),
            dict(self.item, selector=["#icon"], rule="aria-label")
        ]}]}
        self.base = {"viewport_widths": [320, 1280], "source_commit": "audit", "observations": [
            dict(self.item, viewport_width=320, status="unsampled"),
            dict(self.item, viewport_width=1280, status="sampled_above_threshold",
                 minimum_sampled_ratio=5.2, threshold=4.5)
        ]}
        self.followup = {"viewport_widths": [320, 1280], "source_commit": "followup", "observations": [
            dict(self.item, viewport_width=320, status="sampled_above_threshold",
                 prior_status="unsampled", minimum_sampled_ratio=6.1, threshold=4.5)
        ]}

    def test_complete_review_queue_is_pending_even_after_automated_pass(self):
        row, = build_queue(self.axe, self.base, self.followup)
        self.assertEqual(row["priority"], "3_text_review")
        self.assertEqual(row["minimum_margin"], .7)
        self.assertEqual(row["sample_width"], 1280)
        self.assertEqual(row["reinspected_widths"], "320")
        self.assertEqual(row["audit_commit"], "audit")
        self.assertEqual(row["reinspection_commit"], "followup")
        self.assertEqual(row["review_status"], "pending")
        self.assertEqual(row["reviewer"], "")
        self.assertEqual(row["manual_measurement_and_evidence"], "")

    def test_unresolved_sample_is_prioritized_without_reinspection(self):
        row, = build_queue(self.axe, self.base)
        self.assertEqual(row["priority"], "1_unresolved_sample")

    def test_computed_placeholder_failure_is_flagged(self):
        self.base["observations"][0]["status"] = "computed_placeholder_below_threshold"
        self.followup["observations"][0]["prior_status"] = "computed_placeholder_below_threshold"
        self.assertEqual(build_queue(self.axe, self.base)[0]["priority"], "1_unresolved_sample")
        self.assertEqual(build_queue(self.axe, self.base, self.followup)[0]["priority"], "3_text_review")

    def test_missing_duplicate_unrelated_and_unknown_observations_fail_closed(self):
        cases = (self.base["observations"][:1],
                 self.base["observations"] + self.base["observations"][:1],
                 self.base["observations"] + [dict(self.item, viewport_width=390, status="unsampled")],
                 [dict(self.base["observations"][0], status="mystery"), self.base["observations"][1]])
        for observations in cases:
            with self.subTest(observations=observations), self.assertRaises(ValueError):
                build_queue(self.axe, dict(self.base, observations=observations))

    def test_reinspection_cannot_replace_unflagged_or_unrelated_sample(self):
        for item in (dict(self.followup["observations"][0], viewport_width=1280,
                          prior_status="sampled_above_threshold"),
                     dict(self.followup["observations"][0], selector=["#unrelated"]),
                     dict(self.followup["observations"][0], prior_status="narrow_margin")):
            with self.subTest(item=item), self.assertRaises(ValueError):
                build_queue(self.axe, self.base, dict(self.followup, observations=[item]))

    def test_duplicate_axe_target_rejected(self):
        axe = copy.deepcopy(self.axe)
        axe["pages"][0]["incomplete"].append(axe["pages"][0]["incomplete"][0])
        with self.assertRaises(ValueError):
            build_queue(axe, self.base)

    def test_non_text_requires_graphics_review(self):
        observations = [dict(o, status="non_text") for o in self.base["observations"]]
        row, = build_queue(self.axe, dict(self.base, observations=observations))
        self.assertEqual(row["priority"], "2_graphics_review")
        self.assertEqual(row["review_status"], "pending")


if __name__ == "__main__":
    unittest.main()
