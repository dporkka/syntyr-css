"""Audit the exact npm pack artifact before an authorized release.

This maintainer-only check runs npm in a disposable directory, without
installing anything or adding a Syntyr consumer dependency. It also accepts
a previously created tarball with --archive. No extraction is performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import zlib
from tempfile import TemporaryDirectory

try:
    from scripts.build import all_distributions
except ModuleNotFoundError:  # direct python3 scripts/audit_npm_package.py
    from build import all_distributions

ROOT = Path(__file__).resolve().parents[1]


def expected_files(root: Path) -> dict[str, Path]:
    paths = (
        "package.json", "LICENSE", "README.md",
        "integrations/tailwind/syntyr.theme.css",
        "integrations/shadcn/syntyr.tokens.css",
        "integrations/headless/interactions.css",
        "integrations/htmx/syntyr.htmx.css",
        "integrations/dropdown/menu.mjs",
        "metadata/css-contract.v1.json",
        "metadata/component-gallery.v1.json",
        # Opt-in companions are explicitly exported but never required by CSS.
        "dist/syntyr.animate.mjs",
        "dist/syntyr.animate.d.mts",
        "dist/syntyr.copy.mjs",
        "dist/syntyr.copy.d.mts",
    ) + tuple("dist/" + name for name in all_distributions())
    return {"package/" + name: root / name for name in paths}


def audit_archive(archive: Path, root: Path = ROOT) -> list[str]:
    """Check file membership and bytes; reject links, traversal and duplicates."""
    expected = expected_files(root)
    errors: list[str] = []
    found: dict[str, bytes] = {}
    seen_members: dict[str, str] = {}
    try:
        with tarfile.open(archive, mode="r:gz") as package:
            for member in package:
                parts = PurePosixPath(member.name).parts
                if (not parts or parts[0] != "package" or
                        any(part in (".", "..") for part in parts) or
                        member.name.startswith("/") or "\\" in member.name):
                    errors.append(f"unsafe archive path: {member.name}")
                    continue
                if member.issym() or member.islnk():
                    errors.append(f"unsafe symlink or hardlink: {member.name}")
                    continue
                name = member.name.rstrip("/") if member.isdir() else member.name
                kind = "directory" if member.isdir() else "file" if member.isfile() else "other"
                previous = seen_members.get(name)
                if previous is not None:
                    if previous != kind:
                        errors.append(f"file/directory collision: {name}")
                    else:
                        errors.append(f"duplicate archive entry: {name}")
                    continue
                seen_members[name] = kind
                if member.isdir():
                    continue
                if not member.isfile():
                    errors.append(f"unsafe archive entry type: {member.name}")
                    continue
                if member.name not in expected:
                    errors.append(f"unexpected archive file: {member.name}")
                    continue
                stream = package.extractfile(member)
                if stream is None:
                    errors.append(f"unreadable archive file: {member.name}")
                    continue
                found[member.name] = stream.read()
            # tarfile iteration stops at the tar end marker, before the gzip
            # trailer. Consume the stream to validate gzip CRC and ISIZE.
            trailing = package.fileobj.read()
            if trailing.strip(b"\0"):
                errors.append("unexpected data after tar end marker")
    except (EOFError, OSError, tarfile.TarError, zlib.error) as exc:
        return [f"invalid npm archive: {exc}"]

    for name in sorted(expected.keys() - found.keys()):
        errors.append(f"missing archive file: {name}")
    for name, content in sorted(found.items()):
        try:
            source = expected[name].read_bytes()
        except OSError as exc:
            errors.append(f"missing source file for {name}: {exc}")
            continue
        if content != source:
            errors.append(f"source/archive mismatch: {name}")

    try:
        metadata = json.loads(found["package/package.json"])
        if not isinstance(metadata, dict):
            raise ValueError("package.json must be an object")
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        if metadata.get("version") != version or metadata.get("name") != "@syntyr/css":
            errors.append("package metadata mismatch: name or VERSION")
        for field in ("dependencies", "devDependencies", "peerDependencies",
                      "optionalDependencies", "scripts", "bin", "main"):
            if field in metadata:
                errors.append(f"package metadata unexpectedly declares {field}")
        # Imported CSS must survive tree shaking; optional JS companions remain
        # independently removable. A broadened sideEffects map is a contract change.
        if metadata.get("sideEffects") != ["**/*.css"]:
            errors.append("package metadata sideEffects must be ['**/*.css']")
        exports = metadata.get("exports")
        if not isinstance(exports, dict):
            raise ValueError("exports must be an object")
        def verify_export(public: str, target: object) -> None:
            # Node conditional exports may map types/default to separate files.
            if isinstance(target, dict) and target:
                for condition, destination in target.items():
                    if not isinstance(condition, str) or not condition:
                        errors.append(f"invalid npm export condition: {public}")
                        continue
                    verify_export(f"{public}/{condition}", destination)
                return
            if (not isinstance(target, str) or not target.startswith("./") or
                    "\\" in target or
                    any(part in ("", ".", "..") for part in target[2:].split("/"))):
                errors.append(f"invalid npm export target: {public}")
            elif "package/" + target[2:] not in found:
                errors.append(f"missing npm export target {public}: {target}")
        for public, target in exports.items():
            verify_export(public, target)
    except (KeyError, ValueError, TypeError, OSError) as exc:
        errors.append(f"invalid package metadata: {exc}")
    return errors


def audit_live_pack(root: Path = ROOT) -> list[str]:
    """Run npm pack without writing a tarball into the source checkout."""
    with TemporaryDirectory(prefix="syntyr-npm-audit-") as scratch:
        try:
            result = subprocess.run(
                ["npm", "pack", "--ignore-scripts", "--json", "--pack-destination", scratch],
                cwd=root, check=True, capture_output=True, text=True,
            )
            records = json.loads(result.stdout)
            if not isinstance(records, list) or len(records) != 1:
                return ["npm pack did not return exactly one archive"]
            filename = records[0]["filename"]
            if Path(filename).name != filename or not filename.endswith(".tgz"):
                return ["npm pack returned an unsafe filename"]
            archive = Path(scratch) / filename
            if not archive.is_file():
                return ["npm pack did not produce the reported archive"]
        except (OSError, subprocess.CalledProcessError, ValueError, TypeError, KeyError) as exc:
            return [f"npm pack failed (maintainer-only prerequisite): {exc}"]
        return audit_archive(archive, root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path,
                        help="audit an existing npm tarball instead of running npm pack")
    args = parser.parse_args()
    errors = audit_archive(args.archive, ROOT) if args.archive else audit_live_pack(ROOT)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print("PASS npm tarball: exact allowlist, source-identical CSS and optional JS exports; no unexpected files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
