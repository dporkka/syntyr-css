"""Package audited, dependency-free Syntyr vertical website starters.

The source HTML references the repository's CSS distributions for local previews.
Zips replace those references with portable bundled CSS assets.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples" / "industry-sites"
SITE_NAMES = ("field-service", "professional-practice", "saas-developer")
CORE_HREF = "../../../dist/syntyr.core.css"
SITE_HREF = "../site.css"


def _store(archive: ZipFile, name: str, content: bytes) -> None:
    entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    entry.compress_type = ZIP_DEFLATED
    entry.external_attr = 0o100644 << 16
    archive.writestr(entry, content)


def package_sites(output_dir: Path) -> dict[str, Path]:
    """Build one self-contained zip per reviewed template; no globbed private files."""
    core = (ROOT / "dist" / "syntyr.core.css").read_bytes()
    shared = (SOURCE / "site.css").read_bytes()
    readme = (SOURCE / "README.md").read_bytes()
    license_text = (ROOT / "LICENSE").read_bytes()
    output_dir.mkdir(parents=True, exist_ok=True)
    packages: dict[str, Path] = {}
    # Finish every archive before replacing any existing package.
    with TemporaryDirectory(dir=output_dir, prefix=".syntyr-") as temp_dir:
        staging = Path(temp_dir)
        for site in SITE_NAMES:
            pages = sorted((SOURCE / site).glob("*.html"))
            if not pages or not (SOURCE / site / "index.html").is_file():
                raise ValueError(f"Missing index page for {site}")
            destination = output_dir / f"syntyr-{site}.zip"
            with ZipFile(staging / destination.name, "w") as zip_file:
                _store(zip_file, "assets/syntyr.core.css", core)
                _store(zip_file, "assets/site.css", shared)
                _store(zip_file, "README.md", readme)
                _store(zip_file, "LICENSE", license_text)
                for page in pages:
                    html = page.read_text(encoding="utf-8")
                    if html.count(CORE_HREF) != 1 or html.count(SITE_HREF) != 1:
                        raise ValueError(f"Unexpected stylesheet references in {page}")
                    html = html.replace(CORE_HREF, "assets/syntyr.core.css")
                    html = html.replace(SITE_HREF, "assets/site.css")
                    _store(zip_file, page.name, html.encode("utf-8"))
            packages[site] = destination
        for destination in packages.values():
            (staging / destination.name).replace(destination)
    return packages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".build" / "industry-sites")
    args = parser.parse_args()
    for site, path in package_sites(args.output).items():
        print(f"{site}: {path}")


if __name__ == "__main__":
    main()
