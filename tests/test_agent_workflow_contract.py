"""Contract tests for the core CSS, no-JavaScript agent workflow UI."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class AgentWorkflowContractTests(unittest.TestCase):
    def test_machine_readable_contract_is_a_safe_allowlist(self):
        contract = json.loads((ROOT / "metadata/agent-workflow.v1.json").read_text())
        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(contract["runtime_requirement"], "none")
        self.assertEqual(contract["stylesheet"], "syntyr.core.css")
        self.assertEqual(contract["states"], [
            "pending", "running", "awaiting-approval", "completed", "failed", "canceled"
        ])
        self.assertEqual(contract["host_responsibilities"]["authorization"], "required")
        self.assertEqual(contract["host_responsibilities"]["csrf_protection"], "required")
        self.assertEqual(contract["host_responsibilities"]["audit_log"], "required")
        self.assertNotIn("execute", contract)

    def test_example_is_semantic_and_requires_explicit_human_approval(self):
        html = (ROOT / "examples/agent-workflow.html").read_text()
        parsed = Markup()
        parsed.feed(html)
        self.assertFalse(any(tag == "script" for tag, _ in parsed.tags))
        plan, = (attrs for tag, attrs in parsed.tags if tag == "ol")
        self.assertIn("syn-steps", plan["class"].split())
        self.assertEqual(plan["role"], "list")
        self.assertTrue(plan["aria-label"])
        steps = [attrs for tag, attrs in parsed.tags if tag == "li"]
        self.assertEqual([step.get("data-syn-state") for step in steps],
                         ["complete", "complete", None, None])
        self.assertEqual([step.get("aria-current") for step in steps],
                         [None, None, "step", None])
        self.assertTrue(any(tag == "form" and attrs.get("method") == "post" and
                            attrs.get("action", "").startswith("/agent-runs/")
                            for tag, attrs in parsed.tags))
        decisions = {attrs.get("value") for tag, attrs in parsed.tags
                     if tag == "button" and attrs.get("type") == "submit"
                     and attrs.get("name") == "decision"}
        self.assertEqual(decisions, {"approve", "reject"})
        self.assertIn('aria-labelledby="agent-outcome-title"', html)
        self.assertNotIn("onload=", html)
        self.assertNotIn("onclick=", html)
        self.assertNotIn("javascript:", html)


if __name__ == "__main__":
    unittest.main()
