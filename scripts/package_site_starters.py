"""Build/check versioned, deterministic offline starter ZIPs from the source candidate.

No publishing, signing, network, npm or paid products. Uses the reviewed
starter export allowlist, never a recursive repository archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZIP_STORED, ZipFile, ZipInfo

if __package__:
    from .export_site_starter import STARTER_ROUTES, publish_new_directory, stage_starter
    from .freeze_site_release import VERSION_PATTERN
else:
    from export_site_starter import STARTER_ROUTES, publish_new_directory, stage_starter
    from freeze_site_release import VERSION_PATTERN

ROOT = Path(__file__).resolve().parents[1]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_packages(staged: Path) -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Invalid candidate VERSION")
    subprocess.run([sys.executable, str(ROOT / "scripts/build.py"), "--check"],
                   cwd=ROOT, check=True)
    staged.mkdir()
    manifest = {"format": 1, "version": version, "packages": {}}
    with tempfile.TemporaryDirectory(prefix="syntyr-starter-pack-") as temp:
        for name, routes in sorted(STARTER_ROUTES.items()):
            site = Path(temp) / name
            stage_starter(name, site)
            entries = sorted((*routes, "assets/site.css", "assets/syntyr.core.css", "LICENSE"))
            filename = f"syntyr-starter-{name}-{version}.zip"
            output = staged / filename
            hashes = {}
            with ZipFile(output, mode="x", compression=ZIP_STORED) as archive:
                for entry in entries:
                    data = (site / entry).read_bytes()
                    info = ZipInfo(entry, date_time=(1980, 1, 1, 0, 0, 0))
                    # Fixed Unix regular-file metadata; stored bytes avoid zlib-version drift.
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, data)
                    hashes[entry] = sha256(data)
            data = output.read_bytes()
            manifest["packages"][name] = {
                "filename": filename,
                "bytes": len(data),
                "sha256": sha256(data),
                "files": hashes,
            }
    (staged / "manifest.json").write_bytes(
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )


def package_starters(destination: Path, *, check: bool = False) -> None:
    destination = destination.expanduser()
    destination = destination.parent.resolve() / destination.name
    if destination.is_symlink():
        raise ValueError("Refusing symlinked package directory")
    if check:
        if not destination.is_dir():
            raise ValueError("Expected an existing package directory")
    elif destination.exists():
        raise FileExistsError("Package destination exists; refusing to overwrite")
    if not destination.parent.is_dir():
        raise ValueError("Create the destination parent first")
    with tempfile.TemporaryDirectory(prefix=".syntyr-package-",
                                     dir=None if check else destination.parent) as temp:
        staged = Path(temp) / "packages"
        build_packages(staged)
        if not check:
            publish_new_directory(staged, destination)
            return
        expected = {path.name for path in staged.iterdir()}
        actual = {path.name for path in destination.iterdir()}
        if actual != expected:
            raise ValueError(f"Package inventory mismatch: {sorted(expected ^ actual)}")
        for filename in sorted(expected):
            path = destination / filename
            if path.is_symlink() or not path.is_file() or path.read_bytes() != (staged / filename).read_bytes():
                raise ValueError(f"Package differs from source candidate: {filename}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Check exact package bytes without overwriting")
    args = parser.parse_args()
    try:
        package_starters(args.output, check=args.check)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Starter package rejected: {exc}\n")
    print(f"PASS: {'verified' if args.check else 'created'} candidate starter packages at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
