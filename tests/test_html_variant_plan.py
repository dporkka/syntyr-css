"""Transactional preview planning through the real optional inspector."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent_mcp.catalog import CANDIDATE, PUBLISHED, CatalogError
from agent_mcp.html_inspector import inspect_markup, plan_variants

ROOT = Path(__file__).resolve().parents[1]
HTML = '<button class="syn-button syn-button--primary">One</button><button class="syn-button syn-button--primary">Two</button>'

class PlanBoundaryTests(unittest.TestCase):
    def test_requires_candidate(self):
        with self.assertRaisesRegex(CatalogError, "candidate"):
            plan_variants(HTML, PUBLISHED, "a"*64, [])

    def test_rejects_empty_and_oversized_operations(self):
        for ops in ([], [{}]*9):
            with self.assertRaisesRegex(CatalogError, "1 to 8"):
                plan_variants(HTML, CANDIDATE, hashlib.sha256(HTML.encode()).hexdigest(), ops)

@unittest.skipUnless(os.environ.get("SYNTYR_HTML_INSPECTOR"), "Configure optional inspector")
class PlanIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.report = inspect_markup(HTML, CANDIDATE, "button")
        self.digest = self.report["document_sha256"]
        self.ops = [{"element_id": e["element_id"], "selector": "button",
                     "from": "syn-button--primary", "to": "syn-button--outline"}
                    for e in self.report["elements"]]

    def test_multi_operation_plan_and_determinism(self):
        plan = plan_variants(HTML, CANDIDATE, self.digest, self.ops)
        self.assertEqual(plan, plan_variants(HTML, CANDIDATE, self.digest, self.ops))
        self.assertTrue(plan["preview_only"])
        self.assertEqual(len(plan["changes"]), 2)
        self.assertEqual([c["element_id"] for c in plan["changes"]], [o["element_id"] for o in self.ops])
        self.assertTrue(all(c["after"] == "syn-button syn-button--outline" for c in plan["changes"]))

    def test_rejects_duplicate_target_and_invalid_second_operation(self):
        for ops in ([self.ops[0],self.ops[0]], [self.ops[0],{**self.ops[1],"to":"syn-button--unknown"}]):
            with self.assertRaises(CatalogError):
                plan_variants(HTML, CANDIDATE, self.digest, ops)

    def test_stale_digest_rejected(self):
        with self.assertRaises(CatalogError):
            plan_variants(HTML+" ", CANDIDATE, self.digest, self.ops)

    def test_cli_preserves_crlf_and_input_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"page.html"
            data = (HTML+"\r\n").encode()
            path.write_bytes(data)
            base=[sys.executable,str(ROOT/"scripts/syntyr_agent.py")]
            inspection=subprocess.run(base+["inspect-html","--release",CANDIDATE,"--selector","button",str(path)],capture_output=True,text=True,check=True)
            report=json.loads(inspection.stdout)
            self.assertEqual(report["document_sha256"],hashlib.sha256(data).hexdigest())
            request=Path(directory)/"plan.json"
            request.write_text(json.dumps({"document_sha256":report["document_sha256"],"operations":self.ops}))
            run=subprocess.run(base+["plan-html","--release",CANDIDATE,"--request",str(request),str(path)],capture_output=True,text=True,check=True)
            self.assertEqual(len(json.loads(run.stdout)["changes"]),2)
            self.assertEqual(path.read_bytes(),data)
