import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.export_design_tokens import export_tokens
from scripts.reconcile_design_tokens import reconcile

ROOT = Path(__file__).resolve().parents[1]


class TokenReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.expected = export_tokens("studio", "compact")
        self.actual = copy.deepcopy(self.expected)

    def test_all_modes_round_trip(self):
        from scripts.export_design_tokens import PALETTES, DENSITIES
        for theme in PALETTES:
            for density in DENSITIES:
                tokens = export_tokens(theme, density)
                self.assertEqual(reconcile(tokens, tokens), [])

    def test_edited_literal_and_alias_are_reported_by_path(self):
        self.actual["foundation"]["control-height"]["$value"]["value"] = 3
        self.actual["semantic"]["border-focus"]["$value"] = "{palette.accent-2}"
        self.assertEqual([d["path"] for d in reconcile(self.actual, self.expected)],
                         ["foundation.control-height", "semantic.border-focus"])

    def test_missing_unknown_wrong_type_and_cycles_are_rejected(self):
        for mutate in (
            lambda t: t["palette"].pop("accent"),
            lambda t: t["palette"].update(unknown=t["palette"]["accent"]),
            lambda t: t["semantic"]["border-focus"].update({"$value": "{foundation.space-1}"}),
            lambda t: t["semantic"]["border-focus"].update({"$value": "{palette.missing}"}),
            lambda t: t["semantic"]["border-focus"].update({"$value": "{semantic.border-focus}"}),
            lambda t: t["foundation"]["control-height"]["$value"].update(value=True),
            lambda t: t["palette"]["accent"]["$value"].update(components=[2, 0, 0]),
            lambda t: t["palette"]["accent"]["$value"].update(hex="#FFFFFF"),
        ):
            with self.subTest(mutate=mutate):
                candidate = copy.deepcopy(self.expected)
                mutate(candidate)
                with self.assertRaises(ValueError):
                    reconcile(candidate, self.expected)

    def test_cli_is_read_only_and_distinguishes_drift_from_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokens.json"
            cmd = [sys.executable, "scripts/reconcile_design_tokens.py",
                   str(path), "--theme", "studio", "--density", "compact"]
            for payload, code in ((self.actual, 0),):
                path.write_text(json.dumps(payload))
                before = path.read_bytes()
                run = subprocess.run(cmd, cwd=ROOT, capture_output=True)
                self.assertEqual(run.returncode, code, run.stderr)
                self.assertEqual(path.read_bytes(), before)
            self.actual["foundation"]["control-height"]["$value"]["value"] = 3
            path.write_text(json.dumps(self.actual))
            run = subprocess.run(cmd, cwd=ROOT, capture_output=True)
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertEqual(json.loads(run.stdout)["changes"][0]["path"], "foundation.control-height")
            path.write_text('{"palette": {}, "palette": {}}')
            self.assertEqual(subprocess.run(cmd, cwd=ROOT, capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
