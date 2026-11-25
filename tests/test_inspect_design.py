import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.inspect_design import token_graph, token_report, variant_matrix

ROOT = Path(__file__).resolve().parents[1]


class DesignInspectionTests(unittest.TestCase):
    def test_source_graph_tracks_fallbacks_and_ignores_comments_and_strings(self):
        graph = token_graph({"a.css": '''
        .a { --syn-a: var(--syn-b, var(--syn-c)); color: var(--syn-a);
             content: "var(--syn-fake)"; /* --syn-no: var(--syn-fake); */ }
        .b { --syn-a: var(--syn-d); --syn-b: var(--syn-a); }
        '''})
        report = token_report(graph, "--syn-a")
        self.assertEqual(report["depends_on"], ["--syn-b", "--syn-c", "--syn-d"])
        self.assertEqual(report["referenced_by_tokens"], ["--syn-b"])
        self.assertEqual(report["referenced_in"], ["a.css"])
        self.assertNotIn("--syn-fake", graph)
        self.assertNotIn("--syn-no", graph)
        self.assertEqual(report["transitive_dependencies"], ["--syn-b", "--syn-c", "--syn-d"])

    def test_real_focus_ring_source_and_reverse_relationships(self):
        from scripts.inspect_design import source_graph
        graph = source_graph()
        report = token_report(graph, "--syn-focus-ring")
        self.assertIn("--syn-accent", report["depends_on"])
        self.assertIn("src/tokens.css", report["declared_in"])
        self.assertIn("--syn-focus-ring", token_report(graph, "--syn-accent")["referenced_by_tokens"])
        with self.assertRaises(ValueError):
            token_report(graph, "--syn-not-a-real-token")

    def test_matrix_uses_only_curated_variants_and_actual_example_elements(self):
        components = [{"name": "Button", "classes": ["syn-button", "syn-button--primary",
            "syn-button--ghost"], "module": "syntyr.core.css", "elements": ["button"], "notes": "Native"}]
        examples = [{"id": "valid", "html": '<button class="syn-button syn-button--primary">A</button>'},
                    {"id": "split", "html": '<div class="syn-button"></div><div class="syn-button--ghost"></div>'}]
        matrix = variant_matrix(components, examples)
        self.assertEqual(matrix[0]["variants"], [
            {"class": "syn-button--primary", "example_ids": ["valid"]},
            {"class": "syn-button--ghost", "example_ids": []}])
        self.assertEqual(matrix[0]["base_class"], "syn-button")

    def test_cli_returns_real_button_evidence(self):
        run = subprocess.run([sys.executable, "scripts/inspect_design.py", "variants"],
                             cwd=ROOT, capture_output=True, text=True, check=True)
        result = json.loads(run.stdout)
        buttons = next(row for row in result["families"] if row["base_class"] == "syn-button")
        self.assertIn("catalog-buttons-title", buttons["variants"][0]["example_ids"])
        bad = subprocess.run([sys.executable, "scripts/inspect_design.py", "token", "--", "--syn-fake"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("Unknown source token", bad.stderr)
        run = subprocess.run([sys.executable, "scripts/inspect_design.py", "token", "--", "--syn-focus-ring"],
                             cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertIn("--syn-accent", json.loads(run.stdout)["depends_on"])



if __name__ == "__main__":
    unittest.main()
