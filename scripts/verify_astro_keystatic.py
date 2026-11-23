"""Verify a Syntyr Astro+Keystatic public export has NO editor or API routes.

The generic generator verifier checks self-hosted stylesheets, deployment-base
paths and no executable inline scripts. This fixture-specific extension also
requires exactly one public HTML entrypoint and rejects editor artifacts.
"""
from __future__ import annotations

import argparse
from pathlib import Path

if __package__:
    from .verify_static_generators import verify_static_site
else:
    from verify_static_generators import verify_static_site

BASE = "/syntyr-astro-keystatic/"
EDITOR_PARTS = frozenset(("keystatic", "admin", "api"))
SCRIPT_SUFFIXES = frozenset((".js", ".mjs", ".cjs"))


def verify_public_site(destination: Path) -> int:
    root = Path(destination).resolve()
    count = verify_static_site(root, base_path=BASE)
    pages = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.html"))
    if pages != ["index.html"]:
        raise AssertionError(f"unexpected HTML route(s) in public output: {pages}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise AssertionError(f"symlink in public output: {path.relative_to(root)}")
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part.lower() in EDITOR_PARTS for part in rel.parts):
            raise AssertionError(f"editor route or artifact in public output: {rel}")
        if path.suffix.lower() in SCRIPT_SUFFIXES:
            raise AssertionError(f"JavaScript asset in static-only output: {rel}")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="Astro dist directory")
    args = parser.parse_args()
    verified = verify_public_site(args.destination)
    print(f"PASS: {verified} HTML page, local CSS, no JS, no Keystatic/editor/API output")
