"""Build fresh independent CMS renderings for semantic and browser parity.

Maintainer-only; assumes the optional Eleventy/Astro lockfiles have been
installed and a reviewed Hugo binary is available. Never publishes a site.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

if __package__:
    from .build_hugo_cms_starter import build as build_hugo
    from .export_site_starter import publish_new_directory
    from .render_cms_starter import render_document
    from .verify_astro_keystatic import verify_public_site
    from .verify_cms_parity import CONTENT, verify_cms_output
else:
    from build_hugo_cms_starter import build as build_hugo
    from export_site_starter import publish_new_directory
    from render_cms_starter import render_document
    from verify_astro_keystatic import verify_public_site
    from verify_cms_parity import CONTENT, verify_cms_output

ROOT = Path(__file__).resolve().parents[1]


def build_fixtures(destination: Path, *, hugo: str = "hugo") -> None:
    destination = destination.expanduser()
    destination = destination.parent.resolve() / destination.name
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    if not destination.parent.is_dir():
        raise ValueError(f"Create the destination parent first: {destination.parent}")
    subprocess.run([sys.executable, "scripts/build.py", "--check"], cwd=ROOT, check=True)
    with TemporaryDirectory(prefix=".syntyr-generator-parity-", dir=destination.parent) as temp:
        staged = Path(temp) / "fixtures"
        reference = staged / "reference"
        css = reference / "css"
        css.mkdir(parents=True)
        document = json.loads(CONTENT.read_text(encoding="utf-8"))
        (reference / "index.html").write_text(render_document(document), encoding="utf-8")
        for name in ("syntyr.core.css", "syntyr.recipes.css"):
            shutil.copyfile(ROOT / "dist" / name, css / name)
        verify_cms_output(reference)

        hugo_output = staged / "syntyr-hugo"
        build_hugo(hugo_output, hugo=hugo)
        eleventy_output = staged / "syntyr-eleventy"
        subprocess.run(["npm", "run", "build", "--", "--output=" + str(eleventy_output)],
                       cwd=ROOT / "examples/eleventy", check=True)
        verify_cms_output(eleventy_output, base_path="/syntyr-eleventy/")

        astro_output = staged / "syntyr-astro-keystatic"
        astro_project = ROOT / "examples/astro-keystatic"
        # Astro moves prerendered assets via rename(2), so its build output
        # must share a filesystem with its project. Copy verified bytes into
        # the fixture staging directory afterwards (which may be on /tmp).
        with TemporaryDirectory(prefix=".syntyr-astro-parity-", dir=astro_project) as astro_temp:
            native_output = Path(astro_temp) / "output"
            subprocess.run(["npm", "run", "build", "--", "--outDir", str(native_output)],
                           cwd=astro_project, check=True)
            verify_public_site(native_output)
            # Deliberately compare to the canonical page, not just Astro's
            # own editor document. Independent fixtures must not drift.
            verify_cms_output(native_output, base_path="/syntyr-astro-keystatic/")
            shutil.copytree(native_output, astro_output)

        if any(path.is_symlink() for path in staged.rglob("*")):
            raise ValueError("Unexpected symlink in built CMS fixtures")
        publish_new_directory(staged, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hugo", default="hugo", help="Reviewed Hugo executable")
    args = parser.parse_args()
    try:
        build_fixtures(args.output, hugo=args.hugo)
    except (OSError, ValueError, AssertionError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Generator parity build failed: {exc}\n")
    print("PASS: four fresh CMS renderings with canonical semantic parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
