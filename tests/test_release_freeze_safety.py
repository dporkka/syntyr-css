"""Fail-closed CDN freeze and human release-evidence contracts."""
import json
from pathlib import Path
import unittest

from scripts import release_approval


SHA = "a" * 40
CHECKS = release_approval.REQUIRED_CHECKS


def approved(version="0.3.0-alpha.5", commit=SHA):
    return {
        "version": version,
        "commit": commit,
        "checks": {
            name: {
                "status": "pass",
                "reviewer": "Release reviewer",
                "evidence": f"docs/evidence/{name}.md",
            }
            for name in CHECKS
        },
    }


class ReleaseApprovalTests(unittest.TestCase):
    def test_missing_or_partial_manual_evidence_is_stop_ship(self):
        evidence = approved()
        self.assertEqual(release_approval.validate_approval(evidence, evidence["version"], SHA), [])
        del evidence["checks"]["screen_reader"]
        self.assertTrue(any("screen_reader" in error for error in
                            release_approval.validate_approval(evidence, evidence["version"], SHA)))
        evidence = approved()
        evidence["checks"]["contrast"]["status"] = "pending"
        self.assertTrue(any("contrast" in error for error in
                            release_approval.validate_approval(evidence, evidence["version"], SHA)))
        evidence = approved()
        evidence["checks"]["contrast"]["evidence"] = ""
        self.assertTrue(any("contrast" in error for error in
                            release_approval.validate_approval(evidence, evidence["version"], SHA)))

    def test_version_commit_and_unknown_check_fail(self):
        self.assertTrue(any("version" in error for error in
                            release_approval.validate_approval(approved(version="0.3.0-alpha.4"), "0.3.0-alpha.5", SHA)))
        self.assertTrue(any("commit" in error for error in
                            release_approval.validate_approval(approved(commit="b" * 40), "0.3.0-alpha.5", SHA)))
        evidence = approved()
        evidence["checks"]["unreviewed_extra"] = {"status": "pass", "reviewer": "Someone", "evidence": "x"}
        self.assertTrue(release_approval.validate_approval(evidence, "0.3.0-alpha.5", SHA))

    def test_template_is_not_an_approval(self):
        template = json.loads((Path(__file__).resolve().parents[1] /
                               "docs/release-approval-template.json").read_text())
        self.assertTrue(release_approval.validate_approval(template, "0.3.0-alpha.5", SHA))



if __name__ == "__main__":
    unittest.main()
