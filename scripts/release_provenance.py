"""Create exact-commit release ZIP provenance; verify with a trusted SSH signer.

This is maintainer tooling, not release approval or an automatic publisher.
The signer identity, public key and expected commit/version must be trusted
independently of downloaded release assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from zipfile import BadZipFile, ZipFile

if __package__:
    from .package_release import FILES, ROOT
    from .freeze_site_release import VERSION_PATTERN, checked_source_commit
else:
    from package_release import FILES, ROOT
    from freeze_site_release import VERSION_PATTERN, checked_source_commit

REPOSITORY = "https://github.com/dporkka/syntyr-css"
SCHEMA = "syntyr.release-provenance.v1"
NAMESPACE = "syntyr-release"
SHA = re.compile(r"[0-9a-f]{40}")


def git_bytes(root: Path, commit: str, relative: str) -> bytes:
    # Reject non-regular Git objects, including symlinks, in the ZIP allowlist.
    record = subprocess.check_output(
        ["git", "ls-tree", commit, "--", relative], cwd=root
    ).split(b"\t", 1)
    if len(record) != 2 or record[0].split()[:2] != [b"100644", b"blob"]:
        raise ValueError(f"Not a regular tracked file at the reviewed commit: {relative}")
    return subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=root)


def artifact_record(archive: Path, version: str) -> dict:
    if not VERSION_PATTERN.fullmatch(version) or archive.name != f"syntyr-css-{version}.zip":
        raise ValueError("Archive name must match the exact release version")
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("Release ZIP must be a regular file")
    digest = hashlib.sha256()
    size = 0
    with archive.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return {"name": archive.name, "bytes": size, "sha256": digest.hexdigest()}


def make_provenance(root: Path, archive: Path, commit: str) -> dict:
    """Compare every ZIP member against regular, allowlisted Git blobs."""
    if not SHA.fullmatch(commit) or checked_source_commit(root) != commit:
        raise ValueError("Expected commit must be the exact clean checked-out HEAD")
    version = git_bytes(root, commit, "VERSION").decode("utf-8").strip()
    before = artifact_record(archive, version)
    prefix = f"syntyr-css-{version}/"
    expected = {prefix + relative: relative for relative in FILES}
    with ZipFile(archive) as zipped:
        entries = zipped.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(expected) or set(names) != set(expected):
            raise ValueError("ZIP membership differs from the release allowlist")
        for entry in entries:
            source = git_bytes(root, commit, expected[entry.filename])
            if ((entry.external_attr >> 16) & 0o170000 != 0o100000
                    or entry.file_size != len(source)
                    or zipped.read(entry) != source):
                raise ValueError(f"ZIP member differs from the reviewed Git blob: {entry.filename}")
    if checked_source_commit(root) != commit or artifact_record(archive, version) != before:
        raise ValueError("Source or archive changed while producing provenance")
    return {"schema": SCHEMA, "repository": REPOSITORY, "commit": commit,
            "version": version, "artifact": before}


def encode(document: dict) -> bytes:
    return (json.dumps(document, sort_keys=True, indent=2) + "\n").encode("utf-8")


def verify_provenance(archive: Path, manifest: Path, signature: Path,
                      allowed_signers: Path, signer: str, commit: str, version: str) -> None:
    """Require an independently trusted signer and exact source identity."""
    if not SHA.fullmatch(commit) or not signer.strip():
        raise ValueError("Expected full commit SHA and trusted signer are required")
    if not manifest.is_file() or manifest.is_symlink() or manifest.stat().st_size > 16384:
        raise ValueError("Invalid release provenance manifest")
    raw = manifest.read_bytes()
    subprocess.run(["ssh-keygen", "-Y", "verify", "-f", str(allowed_signers),
                    "-I", signer, "-n", NAMESPACE, "-s", str(signature)],
                   input=raw, check=True, capture_output=True)
    expected = {"schema": SCHEMA, "repository": REPOSITORY, "commit": commit,
                "version": version, "artifact": artifact_record(archive, version)}
    if raw != encode(expected):
        raise ValueError("Signed manifest differs from the expected source or artifact")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    create = actions.add_parser("create", help="write unsigned exact-commit provenance")
    create.add_argument("archive", type=Path)
    create.add_argument("manifest", type=Path)
    create.add_argument("--commit", required=True)
    verify = actions.add_parser("verify", help="verify signature, commit, version and archive")
    verify.add_argument("archive", type=Path)
    verify.add_argument("manifest", type=Path)
    verify.add_argument("--signature", type=Path, required=True)
    verify.add_argument("--allowed-signers", type=Path, required=True)
    verify.add_argument("--signer", required=True)
    verify.add_argument("--commit", required=True)
    verify.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        if args.action == "create":
            provenance = make_provenance(ROOT, args.archive, args.commit)
            # No silent replacement of prior evidence or signing input.
            with args.manifest.open("xb") as stream:
                stream.write(encode(provenance))
            print("Created unsigned exact-commit release provenance; signing and approval are separate")
        else:
            verify_provenance(args.archive, args.manifest, args.signature,
                              args.allowed_signers, args.signer, args.commit, args.version)
            print("Verified release signature, exact commit/version and ZIP SHA-256")
    except (OSError, ValueError, BadZipFile, subprocess.CalledProcessError) as error:
        print(f"Release provenance blocked: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
