"""Exact-source and detached-signature release evidence contracts."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import warnings
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

from scripts import release_provenance as provenance


@unittest.skipUnless(shutil.which("git"), "Git is required for release provenance")
class ReleaseProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Release test")
        (self.root / "VERSION").write_text("1.2.3\n")
        (self.root / "LICENSE").write_bytes(b"test license\n")
        self.git("add", "VERSION", "LICENSE")
        self.git("commit", "-qm", "fixture")
        self.commit = self.git("rev-parse", "HEAD").strip()
        self.archive = self.root / "syntyr-css-1.2.3.zip"
        self.manifest = self.root / "provenance.json"
        self.patch = patch.object(provenance, "FILES", ("LICENSE",))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.write_archive()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True)

    def write_archive(self, data=b"test license\n", extra=False, mode=0o100644):
        with ZipFile(self.archive, "w") as archive:
            info = ZipInfo("syntyr-css-1.2.3/LICENSE")
            info.external_attr = mode << 16
            archive.writestr(info, data)
            if extra:
                archive.writestr("syntyr-css-1.2.3/secret", "unexpected")

    def create(self):
        return provenance.make_provenance(self.root, self.archive, self.commit)

    def test_exact_commit_zip_and_deterministic_manifest(self):
        first = self.create()
        self.assertEqual(first["commit"], self.commit)
        self.assertEqual(first["artifact"]["bytes"], self.archive.stat().st_size)
        self.assertEqual(first["artifact"]["sha256"], hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.assertEqual(provenance.encode(first), provenance.encode(self.create()))

    def test_dirty_or_wrong_source_refused(self):
        with self.assertRaises(ValueError):
            provenance.make_provenance(self.root, self.archive, "0" * 40)
        (self.root / "LICENSE").write_bytes(b"local mutation")
        with self.assertRaises(ValueError):
            self.create()

    def test_changed_unexpected_symlink_or_duplicate_members_refused(self):
        for data, extra, mode in ((b"tampered\n", False, 0o100644),
                                  (b"test license\n", True, 0o100644),
                                  (b"test license\n", False, 0o120777)):
            self.write_archive(data, extra, mode)
            with self.subTest(data=data, extra=extra, mode=mode), self.assertRaises(ValueError):
                self.create()

    def test_duplicate_or_missing_member_refused(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(self.archive, "a") as archive:
                archive.writestr("syntyr-css-1.2.3/LICENSE", b"test license\n")
        with self.assertRaises(ValueError):
            self.create()
        with ZipFile(self.archive, "w"):
            pass
        with self.assertRaises(ValueError):
            self.create()

    @unittest.skipUnless(shutil.which("ssh-keygen"), "OpenSSH is optional outside release verification")
    def test_detached_signature_and_exact_artifact_tampering(self):
        key = self.root / "disposable-test-key"
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)], check=True)
        signers = self.root / "trusted-signers"
        signers.write_text("syntyr-test " + key.with_suffix(".pub").read_text())
        self.manifest.write_bytes(provenance.encode(self.create()))
        subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(key), "-n",
                        provenance.NAMESPACE, str(self.manifest)], check=True, capture_output=True)
        signature = self.root / "provenance.json.sig"

        def verify(commit=self.commit, version="1.2.3", identity="syntyr-test"):
            provenance.verify_provenance(self.archive, self.manifest, signature,
                                         signers, identity, commit, version)

        verify()
        with self.assertRaises(subprocess.CalledProcessError):
            verify(identity="not-the-trusted-signer")
        with self.assertRaises(ValueError):
            verify(commit="0" * 40)
        with self.assertRaises(ValueError):
            verify(version="1.2.4")
        original = self.archive.read_bytes()
        self.archive.write_bytes(original + b"tampered")
        with self.assertRaises(ValueError):
            verify()
        self.archive.write_bytes(original)
        self.manifest.write_bytes(self.manifest.read_bytes() + b" ")
        with self.assertRaises(subprocess.CalledProcessError):
            verify()


if __name__ == "__main__":
    unittest.main()
