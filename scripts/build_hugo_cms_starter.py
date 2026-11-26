"""Build a zero-browser-JS Hugo site from Syntyr's existing portable CMS JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit

if __package__:
    from scripts.render_cms_starter import validate_document
    from scripts.verify_cms_parity import verify_cms_output
else:
    from render_cms_starter import validate_document
    from verify_cms_parity import verify_cms_output

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/hugo-cms"
CONTENT = ROOT / "examples/cms-starter/content/pages/home.json"
CSS_ROOT = ROOT / "dist"
DEFAULT_BASE_URL = "https://example.com/syntyr-hugo/"


def _base_path(base_url: str) -> str:
    if not isinstance(base_url, str) or any(c.isspace() or c in (chr(39), chr(34), chr(92)) for c in base_url):
        raise ValueError("Unsafe base URL")
    url = urlsplit(base_url)
    raw_path = url.path or "/"
    path = unquote(raw_path)
    if (url.scheme not in ("http", "https") or not url.hostname or url.username
            or url.password or url.query or url.fragment or not raw_path.endswith("/")
            or "//" in path or chr(92) in path
            or any(part in (".", "..") for part in path.split("/"))):
        raise ValueError("Expected an absolute HTTP(S) site URL ending in /, without traversal")
    return path


def stage_site(destination: Path, *, content_path: Path = CONTENT, css_root: Path = CSS_ROOT,
               base_url: str = DEFAULT_BASE_URL) -> None:
    """Validate untrusted content *before* writing files or launching Hugo."""
    _base_path(base_url)
    # Use the same strict reader as other CMS adapters before Hugo sees JSON.
    if __package__:
        from scripts.render_cms_starter import load_content_json
    else:
        from render_cms_starter import load_content_json
    document = validate_document(load_content_json(content_path))
    destination = Path(destination)
    shutil.copytree(SOURCE, destination, dirs_exist_ok=True)
    config = destination / "hugo.toml"
    config.write_text(config.read_text().replace(DEFAULT_BASE_URL, base_url))
    data_dir = destination / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "home.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    assets = destination / "static/assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("syntyr.core.css", "syntyr.recipes.css"):
        shutil.copyfile(css_root / name, assets / name)


def build(destination: Path, *, hugo: str = "hugo", content_path: Path = CONTENT,
          css_root: Path = CSS_ROOT, base_url: str = DEFAULT_BASE_URL) -> int:
    """Move a verified build into a fresh or empty output directory."""
    destination = Path(destination).absolute()
    if destination.is_symlink() or (destination.exists() and
            (not destination.is_dir() or any(destination.iterdir()))):
        raise ValueError(f"Expected a missing or empty output directory: {destination}")

    with TemporaryDirectory(prefix="syntyr-hugo-") as temp:
        source = Path(temp) / "site"
        stage_site(source, content_path=content_path, css_root=css_root, base_url=base_url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".syntyr-hugo-", dir=destination.parent) as output_temp:
            candidate = Path(output_temp) / "public"
            subprocess.run(
                [hugo, "--source", str(source), "--destination", str(candidate), "--minify"],
                check=True,
            )
            pages = verify_cms_output(candidate, base_path=_base_path(base_url), content_path=content_path)
            # A same-filesystem rename does not replace a nonempty destination.
            candidate.replace(destination)
            return pages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hugo", default="hugo", help="Hugo executable")
    parser.add_argument("--content", type=Path, default=CONTENT, help="CMS JSON input")
    parser.add_argument("--css-root", type=Path, default=CSS_ROOT, help="Built CSS directory")
    parser.add_argument("--output", type=Path, required=True, help="Missing or empty static output directory")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Deployment base URL with trailing /")
    args = parser.parse_args()
    pages = build(args.output, hugo=args.hugo, content_path=args.content, css_root=args.css_root, base_url=args.base_url)
    print(f"PASS: built {pages} Hugo page(s) with local Syntyr CSS at {args.output}")
