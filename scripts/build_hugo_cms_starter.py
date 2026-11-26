"""Stage or build a zero-browser-JS Hugo site from portable JSON or Markdown."""
from __future__ import annotations

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urljoin, urlsplit

if __package__:
    from scripts.render_cms_starter import validate_document
    from scripts.verify_static_generators import verify_static_site
else:
    from render_cms_starter import validate_document
    from verify_static_generators import verify_static_site

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/hugo-cms"
CONTENT = ROOT / "examples/cms-starter/content/pages/home.json"
PRESETS = ROOT / "examples/hugo-presets"
PRESET_TITLES = {"personal": "Personal portfolio", "business": "Business website",
                 "documentation": "Documentation"}
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
               base_url: str = DEFAULT_BASE_URL, preset: str = "cms") -> None:
    """Validate untrusted content *before* writing files or launching Hugo."""
    _base_path(base_url)
    if preset not in ("cms", *PRESET_TITLES):
        raise ValueError(f"Unknown Hugo preset: {preset}")
    if preset != "cms" and content_path != CONTENT:
        raise ValueError("Custom CMS content is only supported with the cms preset")
    document = None
    if preset == "cms":
        document = json.loads(content_path.read_text(encoding="utf-8"))
        validate_document(document)
    destination = Path(destination)
    shutil.copytree(SOURCE, destination, dirs_exist_ok=True)
    config = destination / "hugo.toml"
    config_text = config.read_text().replace(DEFAULT_BASE_URL, base_url)
    if document is not None:
        data_dir = destination / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "home.json").write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    else:
        config_text = config_text.replace("Syntyr Hugo CMS starter", PRESET_TITLES[preset])
        config_text = config_text.replace("'taxonomy', 'term', '404'", "'taxonomy', 'term'")
        shutil.copytree(PRESETS / preset, destination / "content", dirs_exist_ok=True)
    config.write_text(config_text, encoding="utf-8")
    assets = destination / "static/assets"
    assets.mkdir(parents=True, exist_ok=True)
    checksums = []
    for name in ("syntyr.core.css", "syntyr.recipes.css", "syntyr.semantic.css"):
        target = assets / name
        shutil.copyfile(css_root / name, target)
        checksums.append(f"{hashlib.sha256(target.read_bytes()).hexdigest()}  static/assets/{name}")
    (destination / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    shutil.copyfile(ROOT / "LICENSE", destination / "LICENSE-SYNTYR")


def build(destination: Path, *, hugo: str = "hugo", content_path: Path = CONTENT,
          css_root: Path = CSS_ROOT, base_url: str = DEFAULT_BASE_URL, preset: str = "cms") -> int:
    """Move a verified build into a fresh or empty output directory."""
    destination = Path(destination).absolute()
    if destination.is_symlink() or (destination.exists() and
            (not destination.is_dir() or any(destination.iterdir()))):
        raise ValueError(f"Expected a missing or empty output directory: {destination}")

    with TemporaryDirectory(prefix="syntyr-hugo-") as temp:
        source = Path(temp) / "site"
        stage_site(source, content_path=content_path, css_root=css_root, base_url=base_url, preset=preset)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".syntyr-hugo-", dir=destination.parent) as output_temp:
            candidate = Path(output_temp) / "public"
            subprocess.run(
                [hugo, "--source", str(source), "--destination", str(candidate), "--minify"],
                check=True,
            )
            pages = verify_static_site(candidate, base_path=_base_path(base_url))
            for required in ("index.xml", "sitemap.xml", "robots.txt"):
                if not (candidate / required).is_file():
                    raise AssertionError(f"Missing Hugo SEO output: {required}")
            if preset != "cms":
                verify_preset_links(candidate, base_url=base_url)
            # A same-filesystem rename does not replace a nonempty destination.
            candidate.replace(destination)
            return pages


class _LocalLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        if tag in {"a", "link", "img"}:
            url = values.get("href") or values.get("src")
            if url:
                self.urls.append(url)


def verify_preset_links(destination: Path, *, base_url: str) -> None:
    """Check static navigation, same-origin assets and fragment targets."""
    prefix = _base_path(base_url)
    root = destination.resolve()
    origin = urlsplit(base_url)
    for page in root.rglob("*.html"):
        parser = _LocalLinks()
        parser.feed(page.read_text(encoding="utf-8"))
        path = page.relative_to(root).as_posix()
        document_url = urljoin(base_url, path)
        for href in parser.urls:
            uri = urlsplit(urljoin(document_url, href))
            if (uri.scheme, uri.netloc) != (origin.scheme, origin.netloc):
                continue
            decoded = unquote(uri.path)
            if not decoded.startswith(prefix):
                raise AssertionError(f"Link escapes deployment prefix in {path}: {href}")
            target = (root / decoded[len(prefix):]).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.is_relative_to(root) or not target.is_file():
                raise AssertionError(f"Broken local link in {path}: {href}")
            if uri.fragment and target.suffix == ".html":
                linked = _LocalLinks()
                linked.feed(target.read_text(encoding="utf-8"))
                if unquote(uri.fragment) not in linked.ids:
                    raise AssertionError(f"Broken local fragment in {path}: {href}")


def export_source(destination: Path, **kwargs) -> None:
    """Export a self-contained source directory; never replace existing files."""
    destination = Path(destination).absolute()
    if destination.is_symlink() or destination.exists():
        raise ValueError(f"Expected a missing source output directory: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".syntyr-hugo-source-", dir=destination.parent) as temp:
        candidate = Path(temp) / "site"
        stage_site(candidate, **kwargs)
        candidate.rename(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hugo", default="hugo", help="Hugo executable")
    parser.add_argument("--content", type=Path, default=CONTENT, help="CMS JSON input")
    parser.add_argument("--css-root", type=Path, default=CSS_ROOT, help="Built CSS directory")
    outputs = parser.add_mutually_exclusive_group(required=True)
    outputs.add_argument("--output", type=Path, help="Missing or empty static output directory")
    outputs.add_argument("--source-output", type=Path, help="New directory for a standalone Hugo source tree")
    parser.add_argument("--preset", choices=("cms", *PRESET_TITLES), default="cms")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Deployment base URL with trailing /")
    args = parser.parse_args()
    options = dict(content_path=args.content, css_root=args.css_root, base_url=args.base_url, preset=args.preset)
    if args.source_output:
        export_source(args.source_output, **options)
        print(f"PASS: exported standalone Hugo source at {args.source_output}")
    else:
        pages = build(args.output, hugo=args.hugo, **options)
        print(f"PASS: built {pages} Hugo page(s) with local Syntyr CSS at {args.output}")
