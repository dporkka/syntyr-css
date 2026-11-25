"""Preflight or explicitly freeze versioned SYNTYR CDN CSS, without npm dependencies.

The default is read-only. Freezing requires --apply *after* human release
approval; a passing preflight is not a substitute for accessibility, brand or
browser-release gates. Published CSS is immutable and verified before each run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

if __package__:
    from .build import distributions
    from .release_approval import ReleaseBlocked, require_approval
else:
    from build import distributions
    from release_approval import ReleaseBlocked, require_approval

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_published(releases: Path, manifest: dict) -> None:
    """Fail closed if any previously frozen snapshot differs from its manifest."""
    if not isinstance(manifest, dict):
        raise ValueError("Invalid frozen-release manifest")
    for version, entries in manifest.items():
        if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
            raise ValueError(f"Invalid published release version: {version!r}")
        if not isinstance(entries, dict) or not entries:
            raise ValueError(f"Missing asset hashes for published release {version}")
        folder = releases / version
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError(f"Missing or unsafe published release folder: {version}")
        expected_names = set(entries)
        if {p.name for p in folder.iterdir()} != expected_names:
            raise ValueError(f"Frozen release contents differ from manifest: {version}")
        for filename, expected_hash in entries.items():
            if (not isinstance(filename, str) or filename != Path(filename).name
                    or not filename.startswith("syntyr") or not filename.endswith(".css")
                    or not isinstance(expected_hash, str)
                    or not re.fullmatch(r"[0-9a-f]{64}", expected_hash)):
                raise ValueError(f"Invalid manifest entry in {version}: {filename!r}")
            asset = folder / filename
            if not asset.is_file() or asset.is_symlink() or sha256(asset.read_bytes()) != expected_hash:
                raise ValueError(f"Published asset hash mismatch: {version}/{filename}")


def preflight(root: Path) -> tuple[str, Path, dict, dict[str, bytes]]:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Invalid VERSION; expected semver with optional prerelease")
    releases = root / "site-releases"
    manifest_path = releases / "manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("Refusing symlinked release manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_published(releases, manifest)
    if version in manifest or (releases / version).exists():
        raise ValueError(f"Release {version} already frozen; bump VERSION for a new release")

    # Generated CSS may be older than the source; never freeze stale output.
    subprocess.run([sys.executable, str(root / "scripts/build.py"), "--check"],
                   cwd=root, check=True, capture_output=True, text=True)
    css = {}
    for name in sorted(distributions()):
        file = root / "dist" / name
        if not file.is_file() or file.is_symlink():
            raise ValueError(f"Missing or unsafe generated distribution: dist/{name}")
        css[name] = file.read_bytes()
    if not css:
        raise ValueError("No generated CSS distributions to freeze")
    return version, manifest_path, manifest, css


def checked_source_commit(root: Path) -> str:
    """Return the immutable source SHA only when tracked files match it."""
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     cwd=root, text=True).strip()
    tracked_changes = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=root, text=True,
    ).strip()
    if tracked_changes:
        raise ReleaseBlocked("Tracked source differs from the reviewed HEAD commit")
    return actual


def freeze(root: Path, apply: bool = False, *,
           approval_path: Path | None = None, commit: str | None = None) -> None:
    # Bind approval to the source *before* reading generated CSS.
    initial_commit = checked_source_commit(root) if apply else None
    if apply and commit is not None and commit != initial_commit:
        raise ReleaseBlocked("Provided commit does not match the checked-out HEAD")
    version, manifest_path, manifest, css = preflight(root)
    hashes = {name: sha256(contents) for name, contents in css.items()}
    if not apply:
        print(f"READY to freeze {len(css)} CSS files for {version} (read-only preflight; not release approval)")
        return

    if checked_source_commit(root) != initial_commit:
        raise ReleaseBlocked("HEAD changed while collecting the CSS snapshot")
    require_approval(root, version, initial_commit, approval_path)

    target = manifest_path.parent / version
    staged = Path(tempfile.mkdtemp(prefix=f".{version}-stage-", dir=manifest_path.parent))
    manifest_tmp: Path | None = None
    committed = False
    moved = False
    try:
        for name, contents in css.items():
            (staged / name).write_bytes(contents)
        # Prepare the manifest before promoting staged files to the public path.
        new_manifest = dict(manifest)
        new_manifest[version] = hashes
        fd, tempname = tempfile.mkstemp(prefix=".manifest-", suffix=".json",
                                        dir=manifest_path.parent)
        manifest_tmp = Path(tempname)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(new_manifest, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Minimize checkout/commit races before promoting the staged snapshot.
        if checked_source_commit(root) != initial_commit:
            raise ReleaseBlocked("HEAD changed while staging the CSS snapshot")
        staged.rename(target)
        moved = True
        manifest_tmp.replace(manifest_path)
        committed = True
        print(f"Frozen {len(css)} CSS files for {version}; published snapshots unchanged")
    finally:
        if staged.exists():
            shutil.rmtree(staged)
        if manifest_tmp is not None and manifest_tmp.exists():
            manifest_tmp.unlink()
        if moved and not committed and target.exists():
            shutil.rmtree(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true",
                        help="read-only preflight (the default)")
    action.add_argument("--apply", action="store_true",
                        help="freeze the candidate after separate human release approval")
    parser.add_argument("--approval", type=Path,
                        help="JSON release evidence (default release/release-approval.json)")
    args = parser.parse_args()
    try:
        freeze(ROOT, apply=args.apply, approval_path=args.approval)
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"Release freeze blocked: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
