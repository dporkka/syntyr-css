#!/usr/bin/env python3
"""Export a reviewed, standalone static website archetype.

No network, package manager, external fonts, images, or client-side JavaScript.
The source preview references the repository's dist/ stylesheet; exported sites
receive their own exact CSS snapshot under assets/.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import os
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

if __package__:
    from .verify_static_generators import verify_static_site
else:
    from verify_static_generators import verify_static_site
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "examples/site-starters/saas-marketing"
ROUTES = ("index.html", "pricing/index.html", "about/index.html")
CORE = ROOT / "dist/syntyr.core.css"
STARTER_ROOT = STARTER.parent
# A reviewed, explicit allowlist. Never scan an arbitrary input directory.
STARTER_ROUTES = {
    "saas-marketing": ROUTES,
    "documentation": ("index.html", "guide/index.html", "reference/index.html"),
    "blog": ("index.html", "posts/maintainable-web/index.html", "posts/calm-interfaces/index.html"),
    "portfolio": ("index.html", "projects/fieldwork/index.html", "about/index.html"),
}
SHARED = STARTER_ROOT / "shared/site.css"


class StaticDocument(HTMLParser):
    """Collect local references and IDs from the reviewed starter HTML."""

    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.landmarks = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if len(attrs) != len(attributes):
            raise ValueError(f"Duplicate attributes on <{tag}>")
        if attributes.get("id"):
            name = attributes["id"]
            if name in self.ids:
                raise ValueError(f"Duplicate ID: {name}")
            self.ids.add(name)
        if tag in {"h1", "main", "nav", "header", "footer"}:
            self.landmarks.append(tag)
        # These starters deliberately use only ordinary local references.
        if tag == "base" or "srcset" in attributes or "srcdoc" in attributes:
            raise ValueError(f"Unexpected document base or compound URL on <{tag}>")
        for attribute in ("href", "src", "poster", "action", "formaction"):
            if attribute in attributes:
                self.links.append(attributes[attribute] or "")


def verify_offline_site(root: Path, routes: tuple[str, ...]) -> None:
    """Verify reviewed static-file links and fragments, not arbitrary web apps."""
    expected = set(routes) | {"assets/site.css", "assets/syntyr.core.css", "LICENSE"}
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("Unexpected symlink in export")
    names = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if names != expected:
        raise ValueError(f"Unexpected export inventory: {sorted(names ^ expected)}")
    try:
        verify_static_site(root)
    except AssertionError as exc:
        raise ValueError(str(exc)) from exc
    parsed = {}
    root = root.resolve()
    for route in routes:
        path = root / route
        doc = StaticDocument()
        doc.feed(path.read_text(encoding="utf-8"))
        doc.close()
        if (doc.landmarks.count("main") != 1 or doc.landmarks.count("h1") != 1
                or not {"header", "nav", "footer"}.issubset(doc.landmarks)):
            raise ValueError(f"Missing/duplicate required landmarks in {route}")
        if "main" not in doc.ids or "#main" not in doc.links:
            raise ValueError(f"Missing skip link in {route}")
        parsed[path] = doc
    for page, doc in parsed.items():
        for link in doc.links:
            parts = urlsplit(link)
            decoded_path = unquote(parts.path)
            if (not link or parts.scheme or parts.netloc or decoded_path.startswith("/")
                    or chr(92) in decoded_path or any(ord(c) < 32 for c in link)):
                raise ValueError(f"Nonportable reference in {page.name}: {link}")
            target = (page.parent / decoded_path).resolve() if decoded_path else page
            if not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Missing or escaping target in {page.name}: {link}")
            if parts.fragment and (target not in parsed or unquote(parts.fragment) not in parsed[target].ids):
                raise ValueError(f"Missing fragment in {page.name}: {link}")



def publish_new_directory(staged: Path, destination: Path) -> None:
    """Atomically publish a complete directory without replacing any path."""
    if os.name == "nt":
        staged.rename(destination)  # Windows rename never replaces the target.
        return

    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "linux" and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        at_fdcwd, rename_noreplace = -100, 1
        result = rename(at_fdcwd, os.fsencode(staged), at_fdcwd, os.fsencode(destination), rename_noreplace)
    elif sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        rename = libc.renamex_np
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename_excl = 4
        result = rename(os.fsencode(staged), os.fsencode(destination), rename_excl)
    else:
        raise OSError("Atomic export without overwrite is unavailable on this platform")

    if result != 0:
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise FileExistsError(f"Destination exists; refusing to overwrite: {destination}")
        raise OSError(error, os.strerror(error), destination)


def stage_starter(name: str, staged: Path) -> None:
    """Copy exact allowlisted files, then validate the complete staged website."""
    if name not in STARTER_ROUTES:
        raise ValueError(f"Unknown starter: {name}")
    source = STARTER_ROOT / name
    local_css = source / "assets/site.css" if name == "saas-marketing" else SHARED
    routes = STARTER_ROUTES[name]
    inputs = (CORE, local_css, ROOT / "LICENSE", *(source / route for route in routes))
    for path in inputs:
        if not path.is_file() or path.resolve() != path.absolute():
            raise ValueError(f"Missing or symlinked starter input: {path}")
    (staged / "assets").mkdir(parents=True)
    shutil.copyfile(CORE, staged / "assets/syntyr.core.css")
    shutil.copyfile(local_css, staged / "assets/site.css")
    shutil.copyfile(ROOT / "LICENSE", staged / "LICENSE")
    for route in routes:
        depth = len(Path(route).parts) - 1
        original_href = "../" * (depth + 3) + "dist/syntyr.core.css"
        portable_href = "../" * depth + "assets/syntyr.core.css"
        text = (source / route).read_text(encoding="utf-8")
        rewrites = [(original_href, portable_href)]
        if name != "saas-marketing":
            rewrites.append(("../" * (depth + 1) + "shared/site.css",
                             "../" * depth + "assets/site.css"))
        for original, replacement in rewrites:
            if text.count(f'href="{original}"') != 1:
                raise ValueError(f"Unexpected stylesheet reference in {route}")
            text = text.replace(f'href="{original}"', f'href="{replacement}"', 1)
        if 'name="robots"' not in text:
            if text.count("</head>") != 1:
                raise ValueError(f"Unexpected document head in {route}")
            text = text.replace("</head>", '  <meta name="robots" content="noindex,follow">\n</head>', 1)
        target = staged / route
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))
    verify_offline_site(staged, routes)


def export_starter(name: str, destination: Path) -> Path:
    destination = destination.expanduser()
    # Resolve the parent only: the requested leaf may be a dangling symlink.
    destination = destination.parent.resolve() / destination.name
    if destination.is_symlink() or destination.exists():
        raise FileExistsError(f"Destination exists; refusing to overwrite: {destination}")
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"Create the output parent directory first: {destination.parent}")
    # Stage and validate before publishing: no partial export or overwritten site.
    with tempfile.TemporaryDirectory(prefix=".syntyr-site-", dir=destination.parent) as work:
        staged = Path(work) / "site"
        stage_starter(name, staged)
        publish_new_directory(staged, destination)
    return destination


def export_saas_marketing(destination: Path) -> Path:
    """Compatibility entrypoint for the existing Waypoint deploy script."""
    return export_starter("saas-marketing", destination)


def check_starter(name: str, destination: Path) -> None:
    """Read-only, byte-exact check against the current candidate source."""
    if destination.is_symlink() or not destination.is_dir():
        raise ValueError("Expected a regular exported site directory")
    with tempfile.TemporaryDirectory(prefix="syntyr-starter-check-") as work:
        staged = Path(work) / "site"
        stage_starter(name, staged)
        verify_offline_site(destination, STARTER_ROUTES[name])
        for path in staged.rglob("*"):
            if path.is_file():
                actual = destination / path.relative_to(staged)
                if actual.read_bytes() != path.read_bytes():
                    raise ValueError(f"Export differs from source: {actual.relative_to(destination)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export or check a portable Syntyr site starter")
    parser.add_argument("--output", type=Path, required=True, help="New directory; never overwrites an existing path")
    parser.add_argument("--starter", choices=STARTER_ROUTES, default="saas-marketing")
    parser.add_argument("--check", action="store_true", help="Check exact bytes without overwriting")
    args = parser.parse_args()
    try:
        if args.check:
            check_starter(args.starter, args.output)
            print(f"OK {args.starter}: deterministic standalone export")
            return 0
        result = export_starter(args.starter, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Export failed: {exc}\n")
    print(f"Exported standalone site to {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
