"""Exact-source and detached-signature release evidence contracts."""
import hashlib
import os
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
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                     "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                     "GIT_NAMESPACE", "GIT_REPLACE_REF_BASE", "GIT_PREFIX",
                     "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"):
            os.environ.pop(name, None)
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

    def test_git_replacement_objects_cannot_change_reviewed_source(self):
        (self.root / "LICENSE").write_bytes(b"replacement license\n")
        self.git("add", "LICENSE")
        self.git("commit", "-qm", "replacement")
        replacement = self.git("rev-parse", "HEAD").strip()
        self.git("reset", "--hard", self.commit)
        self.git("replace", self.commit, replacement)
        # A replaced commit can otherwise appear clean with the replacement tree.
        self.git("reset", "--hard", self.commit)
        self.write_archive(b"replacement license\n")
        self.assertEqual(provenance.git_bytes(self.root, self.commit, "LICENSE"),
                         b"test license\n")
        with self.assertRaises(ValueError):
            self.create()

    def test_inherited_git_location_does_not_redirect_source_reads(self):
        with patch.dict(os.environ, {"GIT_DIR": str(self.root / "nonexistent"),
                                    "GIT_INDEX_FILE": str(self.root / "wrong-index")}):
            self.assertEqual(self.create()["commit"], self.commit)

    def test_archive_swap_cannot_validate_different_hashed_bytes(self):
        self.write_archive()
        valid = self.archive.read_bytes()
        self.write_archive(b"tampered license\n")
        tampered = self.archive.read_bytes()
        actual_record = provenance.artifact_record
        calls = 0

        def swap(path, version, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                path.write_bytes(tampered)
            record = actual_record(path, version, **kwargs)
            if calls == 1:
                path.write_bytes(valid)
            return record

        with patch.object(provenance, "artifact_record", side_effect=swap):
            with self.assertRaisesRegex(ValueError, "reviewed Git blob"):
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
