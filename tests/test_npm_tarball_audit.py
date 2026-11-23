"""Verify the actual npm archive, not only package.json declarations."""
from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from scripts.audit_npm_package import audit_archive, expected_files

ROOT = Path(__file__).resolve().parents[1]


def archive_with(changes=None, extra=None, *, duplicate=None, symlink=None, directory_collision=None):
    payloads = {name: source.read_bytes() for name, source in expected_files(ROOT).items()}
    for name, value in (changes or {}).items():
        if value is None:
            payloads.pop(name, None)
        else:
            payloads[name] = value
    if extra:
        payloads.update(extra)
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tar:
        def add_colliding_directory():
            info = tarfile.TarInfo("package/dist/syntyr.core.css")
            info.type = tarfile.DIRTYPE
            tar.addfile(info)
        if directory_collision == "before":
            add_colliding_directory()
        for name, data in payloads.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        if directory_collision == "after":
            add_colliding_directory()
        if duplicate:
            data = payloads[duplicate]
            info = tarfile.TarInfo(duplicate)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        if symlink:
            info = tarfile.TarInfo(symlink)
            info.type = tarfile.SYMTYPE
            info.linkname = "package/package.json"
            tar.addfile(info)
    return out.getvalue()


class NpmTarballAuditTests(unittest.TestCase):
    def check(self, contents):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "test.tgz"
            archive.write_bytes(contents)
            return audit_archive(archive, ROOT)

    def test_public_agent_index_exposes_real_tarball_audit(self):
        index = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("docs/package-managers.md", index)
        self.assertIn("audit_npm_package.py", index)

    def test_clean_archive_is_complete(self):
        self.assertEqual(self.check(archive_with()), [])

    def test_current_conditional_exports_and_metadata_are_in_audit_allowlist(self):
        package_files = expected_files(ROOT)
        for path in (
            "package/integrations/headless/interactions.css",
            "package/integrations/htmx/syntyr.htmx.css",
            "package/integrations/dropdown/menu.mjs",
            "package/metadata/css-contract.v1.json",
            "package/metadata/component-gallery.v1.json",
            "package/metadata/agent-workflow.v1.json",
            "package/dist/syntyr.agent.css",
            "package/dist/syntyr.animate.mjs",
            "package/dist/syntyr.animate.d.mts",
            "package/dist/syntyr.copy.mjs",
            "package/dist/syntyr.copy.d.mts",
        ):
            self.assertIn(path, package_files)

    def test_rejects_missing_optional_htmx_stylesheet(self):
        errors = self.check(archive_with(changes={"package/integrations/htmx/syntyr.htmx.css": None}))
        self.assertTrue(any("missing" in err.lower() and "syntyr.htmx.css" in err for err in errors), errors)

    def test_rejects_missing_conditional_js_export(self):
        errors = self.check(archive_with(changes={"package/dist/syntyr.animate.mjs": None}))
        self.assertTrue(any("missing" in err.lower() and "syntyr.animate.mjs" in err
                            for err in errors), errors)

    def test_missing_exported_stylesheet_fails(self):
        errors = self.check(archive_with(changes={"package/dist/syntyr.core.css": None}))
        self.assertTrue(any("missing" in err.lower() and "syntyr.core.css" in err for err in errors), errors)

    def test_rejects_hidden_implementation_or_secret_file(self):
        errors = self.check(archive_with(extra={"package/.env": b"not-a-real-secret"}))
        self.assertTrue(any("unexpected" in err.lower() and ".env" in err for err in errors), errors)

    def test_rejects_modified_source_bytes(self):
        errors = self.check(archive_with(changes={"package/dist/syntyr.core.css": b"altered"}))
        self.assertTrue(any("mismatch" in err.lower() and "syntyr.core.css" in err for err in errors), errors)

    def test_rejects_duplicate_member(self):
        errors = self.check(archive_with(duplicate="package/package.json"))
        self.assertTrue(any("duplicate" in err.lower() for err in errors), errors)

    def test_rejects_symlink(self):
        errors = self.check(archive_with(symlink="package/dist/evil.css"))
        self.assertTrue(any("symlink" in err.lower() for err in errors), errors)

    def test_rejects_traversal(self):
        errors = self.check(archive_with(extra={"package/../private.txt": b"unsafe"}))
        self.assertTrue(any("unsafe archive path" in err.lower() for err in errors), errors)

    def test_rejects_corrupt_gzip_crc(self):
        data = bytearray(archive_with())
        data[-8] ^= 0xFF
        errors = self.check(bytes(data))
        self.assertTrue(any("invalid npm archive" in err for err in errors), errors)

    def test_rejects_truncated_gzip_trailer(self):
        errors = self.check(archive_with()[:-6])
        self.assertTrue(any("invalid npm archive" in err for err in errors), errors)

    def test_rejects_file_directory_collision_both_orders(self):
        for order in ("before", "after"):
            with self.subTest(order=order):
                errors = self.check(archive_with(directory_collision=order))
                self.assertTrue(any("collision" in err for err in errors), errors)

    def test_rejects_nonzero_data_hidden_after_tar_end_marker(self):
        # A second parser could continue into data after the tar end marker.
        payload = gzip.compress(gzip.decompress(archive_with()) + b"hidden-member-payload")
        errors = self.check(payload)
        self.assertTrue(any("unexpected data after tar end marker" in err for err in errors), errors)

    def test_rejects_malformed_trailing_gzip_member_without_crashing(self):
        # Valid gzip followed by a gzip header whose DEFLATE block type is invalid.
        invalid_member = bytes.fromhex("1f8b0800000000000003") + b"\x06" + b"\x00" * 8
        errors = self.check(archive_with() + invalid_member)
        self.assertTrue(any("invalid npm archive" in err for err in errors), errors)

    def test_rejects_non_object_export_map_without_crashing(self):
        errors = self.check(archive_with(changes={
            "package/package.json": b'{"name":"@syntyr/css","exports":[]}',
        }))
        self.assertTrue(any("metadata" in err.lower() for err in errors), errors)

    def test_css_side_effects_contract_is_required(self):
        original = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        for invalid in (None, False, [], ["**/*.js"]):
            with self.subTest(side_effects=invalid):
                modified = dict(original)
                if invalid is None:
                    modified.pop("sideEffects", None)
                else:
                    modified["sideEffects"] = invalid
                errors = self.check(archive_with(changes={
                    "package/package.json": json.dumps(modified).encode("utf-8"),
                }))
                self.assertTrue(
                    any("sideEffects" in error for error in errors), errors
                )

    def test_rejects_bad_package_metadata_in_tarball(self):
        errors = self.check(archive_with(changes={"package/package.json": b'{"name": "something-else"}'}))
        self.assertTrue(any("mismatch" in err.lower() or "metadata" in err.lower() for err in errors), errors)


if __name__ == "__main__":
    unittest.main()
