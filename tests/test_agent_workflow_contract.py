"""Contract tests for the optional, no-JavaScript agent workflow UI."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

from scripts import build

ROOT = Path(__file__).resolve().parents[1]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class AgentWorkflowContractTests(unittest.TestCase):
    def test_optional_css_distribution_does_not_expand_core(self):
        self.assertEqual(build.distributions()["syntyr.agent.css"], ("agent.css",))
        self.assertIn("agent.css", build.distributions()["syntyr.all.css"])
        self.assertNotIn("agent.css", build.distributions()["syntyr.core.css"])
        exports = json.loads((ROOT / "package.json").read_text())["exports"]
        self.assertEqual(exports["./agent.css"], "./dist/syntyr.agent.css")
        self.assertEqual(exports["./agent-workflow.json"], "./metadata/agent-workflow.v1.json")
        source = (ROOT / "src/agent.css").read_text()
        self.assertIn("@layer syn.components", source)
        self.assertIn(".syn-agent-run", source)
        self.assertIn(".syn-agent-approval", source)
        self.assertIn('data-syn-state="awaiting-approval"', source)
        self.assertEqual((ROOT / "dist/syntyr.agent.css").read_text(), build.assemble(("agent.css",)))

    def test_machine_readable_contract_is_a_safe_allowlist(self):
        contract = json.loads((ROOT / "metadata/agent-workflow.v1.json").read_text())
        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(contract["runtime_requirement"], "none")
        self.assertEqual(contract["stylesheet"], "syntyr.agent.css")
        self.assertEqual(contract["states"], [
            "pending", "running", "awaiting-approval", "completed", "failed", "canceled"
        ])
        self.assertEqual(contract["host_responsibilities"]["authorization"], "required")
        self.assertEqual(contract["host_responsibilities"]["csrf_protection"], "required")
        self.assertEqual(contract["host_responsibilities"]["audit_log"], "required")
        self.assertNotIn("execute", contract)
        components = json.loads((ROOT / "metadata/components.json").read_text())["components"]
        item = next(c for c in components if c["name"] == "Agent workflow")
        self.assertEqual(item["module"], "syntyr.agent.css")
        self.assertIn("syn-agent-approval", item["classes"])

    def test_example_is_semantic_and_requires_explicit_human_approval(self):
        html = (ROOT / "examples/agent-workflow.html").read_text()
        parsed = Markup()
        parsed.feed(html)
        self.assertFalse(any(tag == "script" for tag, _ in parsed.tags))
        self.assertTrue(any(tag == "ol" and "syn-agent-steps" in attrs.get("class", "")
                            for tag, attrs in parsed.tags))
        self.assertTrue(any(tag == "form" and attrs.get("method") == "post" and
                            attrs.get("action", "").startswith("/agent-runs/")
                            for tag, attrs in parsed.tags))
        self.assertTrue(any(tag == "button" and attrs.get("type") == "submit"
                            for tag, attrs in parsed.tags))
        self.assertIn("awaiting-approval", html)
        self.assertIn("syn-agent-outcome", html)
        self.assertIn("aria-labelledby", html)
        self.assertNotIn("onload=", html)
        self.assertNotIn("onclick=", html)
        self.assertNotIn("javascript:", html)


if __name__ == "__main__":
    unittest.main()
