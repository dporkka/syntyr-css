"""Build a tiny, portable, explicitly allowlisted SaaS Admin Starter site.

No npm or network access. Never publish the entire repository as static assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples" / "saas-admin-starter"
DEFAULT_OUTPUT = ROOT / ".saas-admin-public"
MARKER = ".syntyr-admin-manifest.json"
PAGES = ("index.html", "pipeline.html", "customers.html", "billing.html")
STYLES = {
    "../../dist/syntyr.core.css": "assets/syntyr.core.css",
    "../../dist/syntyr.recipes.css": "assets/syntyr.recipes.css",
}


def source_files() -> dict[str, bytes]:
    """Generate the entire public file inventory from reviewed, fixed source paths."""
    files: dict[str, bytes] = {}
    for page in PAGES:
        html = (SOURCE / page).read_text(encoding="utf-8")
        for old, new in STYLES.items():
            expected = f'href="{old}"'
            if html.count(expected) != 1:
                raise ValueError(f"Missing or duplicate required CSS link in {page}: {old}")
            html = html.replace(expected, f'href="{new}"', 1)
        if "<script" in html.lower():
            raise ValueError(f"Unexpected runtime script in {page}")
        if 'name="robots"' not in html:
            html = html.replace("</head>", '  <meta name="robots" content="noindex,follow">\n</head>', 1)
        files[page] = html.encode("utf-8")

    files["styles.css"] = (SOURCE / "styles.css").read_bytes()
    for _, destination in STYLES.items():
        files[destination] = (ROOT / "dist" / Path(destination).name).read_bytes()
    files["README.md"] = (SOURCE / "README.md").read_bytes()
    files["LICENSE"] = (ROOT / "LICENSE").read_bytes()
    files["robots.txt"] = b"User-agent: *\nDisallow: /\n"
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files[MARKER] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return files


def build(output: Path, *, check: bool = False) -> int:
    output = output.absolute()
    resolved = output.resolve()
    if resolved == ROOT or resolved in ROOT.parents:
        raise ValueError("Refusing to publish to the source root or a parent")
    if output.is_symlink():
        raise ValueError(f"Refusing to follow output symlink: {output}")

    files = source_files()
    if check:
        existing = {p.relative_to(output).as_posix(): p.read_bytes()
                    for p in output.rglob("*") if p.is_file()} if output.is_dir() else {}
        if existing != files:
            print("STALE SaaS admin publish output", file=sys.stderr)
            return 1
        print(f"OK SaaS admin static output: {len(files)} allowlisted files")
        return 0

    if output.exists():
        if not output.is_dir() or not (output / MARKER).is_file():
            raise ValueError(f"Refusing to overwrite an unmarked directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    for relative, data in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f"BUILT SaaS admin static output: {len(files)} files at {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return build(args.output, check=args.check)


if __name__ == "__main__":
    sys.exit(main())
