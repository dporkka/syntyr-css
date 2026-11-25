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

@unittest.skipUnless(os.environ.get("SYNTYR_HTML_INSPECTOR"), "Configure optional inspector")
class SourcePlanIntegrationTests(unittest.TestCase):
    def test_exact_patches_and_combined_validation(self):
        from agent_mcp.html_inspector import plan_source_patches
        source = '<!-- café -->\r\n' + HTML
        report = inspect_markup(source, CANDIDATE, "button")
        ops = [{"element_id": e["element_id"], "selector": "button",
                "from": "syn-button--primary", "to": "syn-button--outline"}
               for e in report["elements"]]
        plan = plan_source_patches(source, CANDIDATE, report["document_sha256"], ops)
        self.assertTrue(plan["preview_only"])
        self.assertTrue(plan["validation"]["valid"])
        self.assertEqual(len(plan["patches"]), 2)
        expected = source.replace("syn-button--primary", "syn-button--outline")
        data = source.encode()
        for p in reversed(plan["patches"]):
            self.assertEqual(data[p["start_byte"]:p["end_byte"]], p["expected"].encode())
            data = data[:p["start_byte"]] + p["replacement"].encode() + data[p["end_byte"]:]
        self.assertEqual(data, expected.encode())
        self.assertEqual(plan["result_sha256"], hashlib.sha256(data).hexdigest())
        self.assertIn("syn-button--outline", plan["unified_diff"])
        self.assertIn(r"\ No newline at end of file", plan["unified_diff"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_bytes(source.encode())
            req = Path(directory) / "plan.json"
            req.write_text(json.dumps({"document_sha256": report["document_sha256"], "operations": ops}))
            cli = subprocess.run([sys.executable, str(ROOT / "scripts/syntyr_agent.py"), "plan-html",
                                  "--source-patches", "--release", CANDIDATE, "--request", str(req), str(path)],
                                 capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(cli.stdout), plan)
            self.assertEqual(path.read_bytes(), source.encode())

    def test_invalid_existing_contract_is_reported(self):
        from agent_mcp.html_inspector import plan_source_patches
        source = HTML + '<div class="syn-unknown-class"></div>'
        report = inspect_markup(source, CANDIDATE, "button")
        ops = [{"element_id": report["elements"][0]["element_id"], "selector": "button",
                "from": "syn-button--primary", "to": "syn-button--outline"}]
        plan = plan_source_patches(source, CANDIDATE, report["document_sha256"], ops)
        self.assertFalse(plan["validation"]["valid"])
        self.assertIn("unknown-class", [d["code"] for d in plan["validation"]["diagnostics"]])

    def test_ambiguous_source_rejects_whole_plan(self):
        from agent_mcp.html_inspector import plan_source_patches
        source = HTML + '<button class="syn-button syn-button&#45;&#45;primary">Three</button>'
        report = inspect_markup(source, CANDIDATE, "button")
        ops = [{"element_id": e["element_id"], "selector": "button",
                "from": "syn-button--primary", "to": "syn-button--outline"}
               for e in report["elements"]]
        with self.assertRaises(CatalogError):
            plan_source_patches(source, CANDIDATE, report["document_sha256"], ops)

@unittest.skipUnless(os.environ.get("SYNTYR_HTML_INSPECTOR"), "Configure optional inspector")
class GuardedApplyTests(unittest.TestCase):
    def test_approved_candidate_only_and_no_overwrite(self):
        from agent_mcp.html_inspector import plan_source_patches
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "page.html"
            output = root / "candidate.html"
            request = root / "plan.json"
            source.write_bytes(HTML.encode())
            report = inspect_markup(HTML, CANDIDATE, "button")
            ops = [{"element_id": e["element_id"], "selector": "button",
                    "from": "syn-button--primary", "to": "syn-button--outline"}
                   for e in report["elements"]]
            request.write_text(json.dumps({"document_sha256": report["document_sha256"], "operations": ops}))
            plan = plan_source_patches(HTML, CANDIDATE, report["document_sha256"], ops)
            self.assertTrue(plan["combined_dom_verified"])
            command = [sys.executable, str(ROOT / "scripts/syntyr_agent.py"),
                       "apply-html", "--release", CANDIDATE, "--request", str(request),
                       "--output", str(output), str(source)]
            for extra in ([], ["--approve-result-sha256", "0"*64]):
                proc = subprocess.run(command+extra, capture_output=True, text=True)
                self.assertNotEqual(proc.returncode, 0)
                self.assertFalse(output.exists())
            approved = command+["--approve-result-sha256", plan["result_sha256"]]
            proc = subprocess.run(approved, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout+proc.stderr)
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), plan["result_sha256"])
            self.assertEqual(source.read_bytes(), HTML.encode())
            alias = root / "alias.html"
            alias.symlink_to(source)
            linked = approved.copy()
            linked[linked.index(str(output))] = str(alias)
            self.assertNotEqual(subprocess.run(linked, capture_output=True).returncode, 0)
            self.assertEqual(source.read_bytes(), HTML.encode())
            original_output = output.read_bytes()
            proc = subprocess.run(approved, capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(output.read_bytes(), original_output)
            output.unlink()
            source.write_bytes((HTML+" ").encode())
            proc = subprocess.run(approved, capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(output.exists())

@unittest.skipUnless(os.environ.get("SYNTYR_HTML_INSPECTOR"), "Configure optional inspector")
class UnicodeProofTests(unittest.TestCase):
    def test_combined_proof_accepts_eight_long_unicode_selectors(self):
        from agent_mcp.html_inspector import plan_source_patches
        names = ["𐀀" * 240 + str(i) for i in range(8)]
        source = "".join(f'<button id="{name}" class="syn-button syn-button--primary">Button</button>'
                         for name in names)
        report = inspect_markup(source, CANDIDATE, "button")
        ops = [{"element_id": e["element_id"], "selector": "#" + name,
                "from": "syn-button--primary", "to": "syn-button--outline"}
               for e, name in zip(report["elements"], names)]
        plan = plan_source_patches(source, CANDIDATE, report["document_sha256"], ops)
        self.assertTrue(plan["combined_dom_verified"])
        self.assertEqual(len(plan["patches"]), 8)
        self.assertEqual(plan["result_sha256"], hashlib.sha256(
            source.replace("syn-button--primary", "syn-button--outline").encode()).hexdigest())
