"""Verify built Syntyr static pages: self-hosted CSS, deploy-prefix safety, no JS.

Generator-independent: point this at Eleventy, Astro, Jekyll or Zola output.
Hugo's full documentation preview has its own extended link verifier.
Python standard library only; this is an optional build-time QA tool.
"""
from argparse import ArgumentParser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import posixpath


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stylesheets = []
        self.has_script = False
        self.has_root = False
        self.base_href = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        # A script-free page must also reject executable HTML attributes/URLs.
        url_attributes = {"href", "src", "action", "formaction", "xlink:href",
                          "srcset", "poster", "data", "background", "cite"}
        for key, value in attrs:
            value = value or ""
            normalized = "".join(c for c in value if c not in "\t\r\n\f").strip().lower()
            if key.startswith("on") or key == "srcdoc" or (
                    key in url_attributes and "javascript:" in normalized):
                self.has_script = True
        if tag == "base" and self.base_href is None and "href" in attributes:
            self.base_href = attributes["href"]
        if tag == "script":
            script_type = attributes.get("type", "").strip().lower()
            # JSON-LD and inert JSON data blocks are common on static SEO pages.
            if script_type not in {"application/ld+json", "application/json"} or "src" in attributes:
                self.has_script = True
        if "syn-root" in attributes.get("class", "").split():
            self.has_root = True
        if tag == "link" and "stylesheet" in attributes.get("rel", "").lower().split():
            self.stylesheets.append(attributes.get("href", ""))


def verify_static_site(destination: Path, *, base_path: str = "/") -> int:
    """Return verified HTML count; raise AssertionError on contract violations."""
    root = destination.resolve()
    if not root.is_dir():
        raise AssertionError(f"Missing build output: {root}")
    if not base_path.startswith("/") or not base_path.endswith("/") or "//" in base_path:
        raise ValueError("base_path must start and end with / (e.g. /my-site/)")
    pages = sorted(root.rglob("*.html"))
    if not pages:
        raise AssertionError("No generated HTML pages")
    for page_path in pages:
        page = Page()
        page.feed(page_path.read_text(encoding="utf-8"))
        name = page_path.relative_to(root).as_posix()
        if page.has_script:
            raise AssertionError(f"Unexpected JavaScript in {name}")
        if not page.has_root:
            raise AssertionError(f"Missing scoped syn-root in {name}")
        if not page.stylesheets:
            raise AssertionError(f"Missing stylesheet reference in {name}")
        origin = "https://syntyr.invalid"
        document_url = origin + base_path + name
        base_url = document_url
        if page.base_href is not None:
            parsed_base = urlsplit(page.base_href)
            if parsed_base.scheme or parsed_base.netloc or page.base_href.startswith("//"):
                raise AssertionError(f"External document base URL in {name}")
            base_url = urljoin(document_url, page.base_href)
            base_path_on_site = posixpath.normpath(unquote(urlsplit(base_url).path))
            if not (base_path_on_site == base_path.rstrip("/")
                    or base_path_on_site.startswith(base_path)):
                raise AssertionError(f"Document base URL ignores base path in {name}")
        has_syntyr_css = False
        for url in page.stylesheets:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or url.startswith("//"):
                raise AssertionError(f"External stylesheet in {name}: {url}")
            if not parsed.path:
                raise AssertionError(f"Empty stylesheet URL in {name}")
            resolved = urlsplit(urljoin(base_url, url))
            if resolved.scheme != "https" or resolved.netloc != "syntyr.invalid":
                raise AssertionError(f"External stylesheet in {name}: {url}")
            path = posixpath.normpath(unquote(resolved.path))
            if "\\" in path:
                raise AssertionError(f"Invalid stylesheet path in {name}: {url}")
            if not path.startswith(base_path):
                raise AssertionError(f"Stylesheet URL ignores base path in {name}: {url}")
            output_name = path[len(base_path):]
            file_path = (root / output_name).resolve()
            if not file_path.is_relative_to(root) or not file_path.is_file():
                raise AssertionError(f"Missing stylesheet in {name}: {url}")
            has_syntyr_css |= ".syn-root" in file_path.read_text(encoding="utf-8")
        if not has_syntyr_css:
            raise AssertionError(f"Syntyr CSS missing from stylesheets in {name}")
    return len(pages)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="Generated site output directory")
    parser.add_argument("--base-path", default="/", help="Published mount path, including trailing slash")
    args = parser.parse_args()
    pages = verify_static_site(args.destination, base_path=args.base_path)
    print(f"PASS: {pages} static HTML pages; local Syntyr CSS, base URLs and zero browser scripts.")
