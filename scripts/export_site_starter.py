#!/usr/bin/env python3
"""Export the reviewed Waypoint marketing example as a standalone static website.

No network, package manager, external fonts, images, or client-side JavaScript.
The source preview references the repository's dist/ stylesheet; exported sites
receive their own exact CSS snapshot under assets/.
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "examples/site-starters/saas-marketing"
ROUTES = ("index.html", "pricing/index.html", "about/index.html")
CORE = ROOT / "dist/syntyr.core.css"


def export_saas_marketing(destination: Path) -> Path:
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"Destination exists; refusing to overwrite: {destination}")
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"Create the output parent directory first: {destination.parent}")
    if not CORE.is_file():
        raise FileNotFoundError(f"Missing compiled CSS: {CORE}")
    # Stage files before publishing the directory so a failed validation never
    # leaves a misleading half-exported website at the requested path.
    with tempfile.TemporaryDirectory(prefix=".syntyr-site-", dir=destination.parent) as work:
        staged = Path(work) / "site"
        (staged / "assets").mkdir(parents=True)
        shutil.copyfile(CORE, staged / "assets/syntyr.core.css")
        shutil.copyfile(STARTER / "assets/site.css", staged / "assets/site.css")
        for route in ROUTES:
            depth = len(Path(route).parts) - 1
            original_href = "../" * (depth + 3) + "dist/syntyr.core.css"
            portable_href = "../" * depth + "assets/syntyr.core.css"
            text = (STARTER / route).read_text(encoding="utf-8")
            if text.count(f'href="{original_href}"') != 1:
                raise ValueError(f"Unexpected stylesheet reference in {route}")
            text = text.replace(f'href="{original_href}"', f'href="{portable_href}"', 1)
            target = staged / route
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        # No static generator is required to serve the resulting directory.
        staged.rename(destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the Syntyr SaaS marketing starter")
    parser.add_argument("--output", type=Path, required=True, help="New directory; never overwrites an existing path")
    args = parser.parse_args()
    try:
        result = export_saas_marketing(args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Export failed: {exc}\n")
    print(f"Exported standalone site to {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
