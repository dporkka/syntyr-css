"""Offline contract for the exact-inventory OSV pilot; no network in unit tests."""
from pathlib import Path
import tempfile
import shutil
import subprocess
import unittest

from scripts.audit_non_npm_dependencies import INVENTORIES, advisories, package_inventory

ROOT = Path(__file__).resolve().parents[1]


class NonNpmAuditTest(unittest.TestCase):
    def test_inventory_has_distinct_public_ecosystems_and_pinned_versions(self):
        packages = package_inventory(ROOT)
        self.assertEqual({key[0] for key in packages}, {"crates.io", "Go", "PyPI"})
        self.assertIn(("PyPI", "markdown-it-py", "3.0.0"), packages)
        self.assertIn(("PyPI", "mdurl", "0.1.2"), packages)
        self.assertFalse(any(key[1] == "syntyr-axum-example" for key in packages))
        self.assertFalse(any(key[2].endswith("/go.mod") for key in packages))
        self.assertEqual({path for paths in packages.values() for path in paths}, set(INVENTORIES))

    @unittest.skipUnless(shutil.which("git"), "Tracked-file discovery requires optional Git")
    def test_all_tracked_non_npm_dependency_inventories_are_listed(self):
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        expected = {path for path in paths if Path(path).name in ("Cargo.lock", "go.sum")
                    or Path(path).name.startswith("requirements") and path.endswith(".txt")}
        self.assertEqual(expected, set(INVENTORIES), "Review new public dependency inventory coverage")

    def test_missing_or_unpinned_inventory_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                package_inventory(root)
            for relative in INVENTORIES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            (root / "requirements-docs.txt").write_text("markdown-it-py>=3\n")
            with self.assertRaises(ValueError):
                package_inventory(root)

    def test_batch_preserves_coordinate_mapping_and_pagination(self):
        keys = {("Go", "public/module", "v1.2.3"): {"go.sum"}, ("PyPI", "public-lib", "1.0"): {"requirements.txt"}}
        calls = []

        def fake(queries):
            calls.append(queries)
            if len(calls) == 1:
                return {"results": [{"vulns": [{"id": "GO-1"}], "next_page_token": "next"}, {}]}
            self.assertEqual(len(queries), 1)
            self.assertEqual(queries[0]["package"]["name"], "public/module")
            self.assertEqual(queries[0]["page_token"], "next")
            return {"results": [{"vulns": [{"id": "GO-2"}, {"id": "GO-1"}]}]}

        self.assertEqual(advisories(keys, fake), {("Go", "public/module", "v1.2.3"): {"GO-1", "GO-2"}})

    def test_malformed_incomplete_or_repeated_page_response_fails_closed(self):
        keys = {("PyPI", "public-lib", "1.0"): {"requirements.txt"}}
        for payload in ({}, {"results": []}, {"results": [{"error": "failure"}]},
                        {"results": [{"vulns": [{}]}]}, {"results": [{"next_page_token": "again"}]}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                advisories(keys, lambda _: payload)
        self.assertEqual(advisories(keys, lambda _: {"results": [{}]}), {})

    def test_woodpecker_pilot_runs_offline_contract_then_live_scan(self):
        workflow = (ROOT / ".woodpecker/non-npm-security.yaml").read_text()
        self.assertIn("event: manual", workflow)
        self.assertIn("event: tag", workflow)
        test = "      - python3 -m unittest discover -s tests -p test_non_npm_dependency_audit.py -v"
        scan = "      - python3 scripts/audit_non_npm_dependencies.py"
        self.assertLess(workflow.index(test), workflow.index(scan))
        self.assertNotIn("|| true", workflow)


if __name__ == "__main__":
    unittest.main()
