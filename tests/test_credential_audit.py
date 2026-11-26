"""Optional full-history credential scanner contract with exact exceptions."""
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_repository_secrets.sh"


class CredentialAuditTest(unittest.TestCase):
    def test_exceptions_are_exact_historical_fingerprints(self):
        entries = [line for line in (ROOT / ".gitleaksignore").read_text().splitlines()
                   if line and not line.startswith("#")]
        self.assertEqual(len(entries), len(set(entries)))
        for entry in entries:
            self.assertRegex(entry, r"^[0-9a-f]{40}:[\w./-]+:[\w-]+:\d+$")
        self.assertTrue(entries, "Review historical exceptions explicitly")
        self.assertNotIn(".gitleaks.toml", entries)

    def test_ci_requires_pinned_archive_and_complete_history(self):
        ci = (ROOT / ".woodpecker/credential-security.yaml").read_text()
        self.assertIn("git fetch --unshallow", ci)
        self.assertIn("/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz", ci)
        self.assertRegex(ci, r"[0-9a-f]{64} /tmp/gitleaks.tar.gz \| sha256sum -c")
        self.assertLess(ci.index("sha256sum -c"), ci.index("tar -xzf"))
        wrapper = SCRIPT.read_text()
        self.assertIn("--is-shallow-repository", wrapper)
        self.assertIn("--redact=100", wrapper)
        self.assertIn("--ignore-gitleaks-allow", wrapper)
        self.assertNotIn("--report-path", wrapper)

    @unittest.skipUnless(shutil.which("git") and shutil.which("sh"), "Git/sh are maintainer-only")
    def test_shallow_history_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            self.git(source, "init", "-q")
            self.commit(source, "README", "fixture\n")
            clone = root / "shallow"
            subprocess.run(["git", "clone", "--quiet", "--depth", "1", source.as_uri(), str(clone)], check=True)
            result = subprocess.run(["sh", str(SCRIPT)], cwd=clone, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("fetch full history", result.stderr)

    @unittest.skipUnless(shutil.which("git") and shutil.which("sh") and
                         (os.environ.get("GITLEAKS") or shutil.which("gitleaks")),
                         "Gitleaks is opt-in maintainer tooling")
    def test_synthetic_credential_is_detected_without_echoing_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.git(root, "init", "-q")
            (root / ".gitleaksignore").write_text("")
            # Random token-shaped local-only data; never an issued credential.
            fake = "ghp_" + secrets.token_hex(18)
            self.commit(root, "settings.txt", "token=" + fake + "\n")
            result = subprocess.run(["sh", str(SCRIPT)], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(fake, result.stdout + result.stderr)

    @staticmethod
    def git(root, *args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    def commit(self, root, name, content):
        (root / name).write_text(content)
        self.git(root, "add", name)
        self.git(root, "-c", "user.name=Fixture", "-c", "user.email=test@invalid.example", "commit", "-qm", "fixture")


if __name__ == "__main__":
    unittest.main()
