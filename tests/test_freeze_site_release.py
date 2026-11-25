"""Release freezing must be fail-closed, explicit and non-destructive."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseFreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="syntyr-freeze-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ("scripts", "dist", "site-releases"):
            (self.root / name).mkdir()
        shutil.copyfile(ROOT / "scripts/freeze_site_release.py",
                        self.root / "scripts/freeze_site_release.py")
        shutil.copyfile(ROOT / "scripts/release_approval.py",
                        self.root / "scripts/release_approval.py")
        (self.root / "scripts/build.py").write_text(
            "from pathlib import Path\n"
            "def distributions():\n"
            "    return {'syntyr.core.css': (), 'syntyr.all.css': ()}\n"
            "if __name__ == '__main__':\n"
            "    assert (Path(__file__).resolve().parents[1] / 'dist/syntyr.core.css').read_bytes() == b'fresh'\n",
            encoding="utf-8",
        )
        (self.root / "VERSION").write_text("0.3.0-alpha.5\n")
        for name in ("syntyr.core.css", "syntyr.all.css"):
            (self.root / "dist" / name).write_bytes(b"fresh")
        old = "0.3.0-alpha.4"
        (self.root / "site-releases" / old).mkdir()
        (self.root / "site-releases" / old / "syntyr.core.css").write_bytes(b"immutable-old")
        self.manifest_path = self.root / "site-releases/manifest.json"
        self.original_manifest = {old: {
            "syntyr.core.css": hashlib.sha256(b"immutable-old").hexdigest()
        }}
        self.manifest_path.write_text(json.dumps(self.original_manifest) + "\n")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c",
                        "user.email=test@example.invalid", "commit", "-q", "-m", "fixture"],
                       cwd=self.root, check=True)
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                         cwd=self.root, text=True).strip()
        (self.root / "release").mkdir()
        from scripts.release_approval import REQUIRED_CHECKS
        approval = {
            "version": "0.3.0-alpha.5",
            "commit": commit,
            "checks": {
                name: {"status": "pass", "reviewer": "Synthetic fixture",
                       "evidence": f"synthetic-test:{name}"}
                for name in REQUIRED_CHECKS
            },
        }
        (self.root / "release/release-approval.json").write_text(json.dumps(approval))

    def run_freeze(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/freeze_site_release.py"), *args],
            cwd=self.root, text=True, capture_output=True,
        )

    def test_default_is_non_mutating_preflight(self):
        result = self.run_freeze()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())
        self.assertEqual(json.loads(self.manifest_path.read_text()),
                         self.original_manifest)

    def test_explicit_check_is_non_mutating(self):
        result = self.run_freeze("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("READY", result.stdout)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())

    def test_stale_dist_refuses_mutation(self):
        (self.root / "dist/syntyr.core.css").write_bytes(b"stale")
        result = self.run_freeze("--apply")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())
        self.assertEqual(json.loads(self.manifest_path.read_text()),
                         self.original_manifest)

    def test_corrupted_published_release_refuses_mutation(self):
        old = self.root / "site-releases/0.3.0-alpha.4/syntyr.core.css"
        old.write_bytes(b"corrupted")
        result = self.run_freeze("--apply")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())
        self.assertEqual(json.loads(self.manifest_path.read_text()),
                         self.original_manifest)

    def test_apply_freezes_allowlisted_css_only(self):
        (self.root / "dist/syntyr.untracked.css").write_bytes(b"not-for-public-release")
        result = self.run_freeze("--apply")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        release = self.root / "site-releases/0.3.0-alpha.5"
        self.assertEqual({p.name for p in release.iterdir()},
                         {"syntyr.core.css", "syntyr.all.css"})
        manifest = json.loads(self.manifest_path.read_text())
        self.assertEqual(manifest["0.3.0-alpha.4"], self.original_manifest["0.3.0-alpha.4"])
        for name in ("syntyr.core.css", "syntyr.all.css"):
            self.assertEqual(manifest["0.3.0-alpha.5"][name],
                             hashlib.sha256((release / name).read_bytes()).hexdigest())
        second = self.run_freeze("--apply")
        self.assertNotEqual(second.returncode, 0, second.stdout)

    def test_apply_requires_a_separate_approval_record(self):
        (self.root / "release/release-approval.json").unlink()
        result = self.run_freeze("--apply")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("cannot read approval", result.stderr)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())

    def test_apply_rejects_approval_for_another_commit(self):
        path = self.root / "release/release-approval.json"
        evidence = json.loads(path.read_text())
        evidence["commit"] = "0" * 40
        path.write_text(json.dumps(evidence))
        result = self.run_freeze("--apply")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("commit does not match", result.stderr)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())

    def test_apply_rejects_dirty_tracked_source(self):
        (self.root / "VERSION").write_text("0.3.0-alpha.5\n\n")
        result = self.run_freeze("--apply")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("Tracked source differs", result.stderr)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())

    def run_direct(self, python_code):
        return subprocess.run([sys.executable, "-c", python_code],
                              cwd=self.root, capture_output=True, text=True)

    def test_direct_api_rejects_commit_that_is_not_head(self):
        path = self.root / "release/release-approval.json"
        evidence = json.loads(path.read_text())
        evidence["commit"] = "f" * 40
        path.write_text(json.dumps(evidence))
        code = """
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "scripts"))
from freeze_site_release import freeze
freeze(Path.cwd(), apply=True, commit="f" * 40)
"""
        result = self.run_direct(code)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())

    def test_checkout_change_during_preflight_blocks_snapshot(self):
        code = """
from pathlib import Path
import json
import subprocess
import sys
sys.path.insert(0, str(Path.cwd() / "scripts"))
import freeze_site_release as f
original = f.preflight
def switch_head(root):
    result = original(root)
    subprocess.run(["git", "-c", "user.name=Test", "-c",
        "user.email=test@example.invalid", "commit", "-q", "--allow-empty",
        "-m", "mid-flight checkout"], cwd=root, check=True)
    approved = root / "release/release-approval.json"
    record = json.loads(approved.read_text())
    record["commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    approved.write_text(json.dumps(record))
    return result
f.preflight = switch_head
f.freeze(Path.cwd(), apply=True)
"""
        result = self.run_direct(code)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.root / "site-releases/0.3.0-alpha.5").exists())


if __name__ == "__main__":
    unittest.main()
