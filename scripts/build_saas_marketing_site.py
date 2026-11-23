#!/usr/bin/env python3
"""Build a repeatable, strictly allowlisted SaaS marketing deployment.

Keeps the existing no-overwrite standalone exporter intact. No npm, network
calls, runtime JavaScript, credentials, or broad repository directory publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from export_site_starter import export_saas_marketing

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy/saas-marketing"
OUTPUT = DEPLOY / ".public"
MARKER = ".syntyr-marketing-manifest.json"
ROUTES = ("index.html", "pricing/index.html", "about/index.html")
ASSETS = ("assets/syntyr.core.css", "assets/site.css")
OTHER = ("README.md", "LICENSE", "robots.txt")
EXPECTED = frozenset((*ROUTES, *ASSETS, *OTHER, MARKER))


def source_files() -> dict[str, bytes]:
    """Build an isolated copy of reviewed sources; enumerate every public byte."""
    with tempfile.TemporaryDirectory(prefix="syntyr-marketing-build-") as temp:
        site = Path(temp) / "site"
        export_saas_marketing(site)
        files = {name: (site / name).read_bytes() for name in (*ROUTES, *ASSETS)}

    for route in ROUTES:
        html = files[route].decode("utf-8")
        if "<script" in html.lower():
            raise ValueError(f"Unexpected JavaScript in static template: {route}")
        if 'name="robots"' not in html:
            if html.count("</head>") != 1:
                raise ValueError(f"Unexpected document head: {route}")
            html = html.replace("</head>", '  <meta name="robots" content="noindex,follow">\n</head>', 1)
        files[route] = html.encode("utf-8")

    files["README.md"] = (DEPLOY / "README.md").read_bytes()
    files["LICENSE"] = (ROOT / "LICENSE").read_bytes()
    files["robots.txt"] = b"User-agent: *\nDisallow: /\n"

    index = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files[MARKER] = (json.dumps(index, sort_keys=True, indent=2) + "\n").encode("utf-8")
    assert set(files) == EXPECTED
    return files


def build(output: Path, *, check: bool = False) -> int:
    output = output.absolute()
    # Reject symlinks before resolve; even dangling links must not be followed.
    if output.is_symlink():
        raise ValueError(f"Refusing symlink destination: {output}")
    resolved = output.resolve()
    if resolved == ROOT or resolved in ROOT.parents:
        raise ValueError("Refusing output at source root or parent directory")

    files = source_files()
    if check:
        actual = {p.relative_to(output).as_posix(): p.read_bytes()
                  for p in output.rglob("*") if p.is_file()} if output.is_dir() else {}
        if actual != files:
            print("STALE SaaS marketing deployment output", file=sys.stderr)
            return 1
        print(f"OK SaaS marketing site: {len(files)} allowlisted files")
        return 0

    if output.exists():
        marker = output / MARKER
        if not output.is_dir() or marker.is_symlink() or not marker.is_file():
            raise ValueError(f"Refusing to overwrite unrelated directory: {output}")
        try:
            recorded = json.loads(marker.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ValueError(f"Unrecognized previous deployment marker: {output}") from exc
        actual_names = {p.relative_to(output).as_posix()
                        for p in output.rglob("*") if p.is_file()}
        if (set(recorded) != EXPECTED - {MARKER}
                or actual_names != EXPECTED
                or any(p.is_symlink() for p in output.rglob("*"))):
            raise ValueError(f"Unexpected files in previous deployment: {output}")
        shutil.rmtree(output)

    output.mkdir(parents=True)
    for relative, data in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f"BUILT SaaS marketing site: {len(files)} files at {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT,
                        help="Publish folder (default: deploy/saas-marketing/.public)")
    parser.add_argument("--check", action="store_true", help="Verify exact deterministic output")
    args = parser.parse_args()
    try:
        return build(args.output, check=args.check)
    except (ValueError, OSError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
