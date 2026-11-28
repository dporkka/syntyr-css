"""Check a portable CMS landing page against the canonical native HTML renderer.

Intentionally narrow: compare the existing CMS recipe, not arbitrary sites.
Ignore formatting, CSS bundler filenames and optional HTML end tags; preserve
semantic structure, exact decoded text, attributes and deployment-local links.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import re
from itertools import zip_longest
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

if __package__:
    from .render_cms_starter import load_validated_document, render_document
    from .verify_static_generators import verify_static_site
else:
    from render_cms_starter import load_validated_document, render_document
    from verify_static_generators import verify_static_site

CONTENT = Path(__file__).resolve().parents[1] / "examples/cms-starter/content/pages/home.json"
OPTIONAL_END = frozenset(("html", "body"))
OPTIONAL_CONTENT_END = frozenset(("p", "li"))
# HTML permits a paragraph end to be omitted before these block starts.
# The verifier handles the bounded native CMS vocabulary, not arbitrary HTML.
PARAGRAPH_END_START = frozenset((
    "address", "article", "aside", "blockquote", "details", "div", "dl", "dt", "dd",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4",
    "h5", "h6", "header", "hgroup", "hr", "li", "main", "menu", "nav", "ol", "p",
    "pre", "search", "section", "table", "ul",
))
VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input",
                  "link", "meta", "param", "source", "track", "wbr"))


def normalized_text(value: str) -> str:
    return re.sub(r"[ \t\n\r\f]+", " ", value).strip(" ")


def local_link(value: str, base_path: str) -> str:
    """Remove only the declared mount prefix, never a foreign path/origin."""
    parts = urlsplit(value)
    if parts.scheme or parts.netloc or not parts.path.startswith("/"):
        return value
    if any(unquote(segment) in (".", "..") for segment in parts.path.split("/")):
        raise AssertionError(f"CMS link contains a traversal segment: {value}")
    segments = parts.path.split("/", base_path.count("/"))
    prefix = "/".join(segments[:-1]) + "/"
    if len(segments) != base_path.count("/") + 1 or unquote(prefix) != base_path:
        raise AssertionError(f"CMS link ignores base path: {value}")
    return urlunsplit(("", "", "/" + segments[-1], parts.query, parts.fragment))


class Signature(HTMLParser):
    def __init__(self, base_path: str):
        super().__init__(convert_charrefs=True)
        self.base_path = base_path
        self.events = []
        self.pending = []
        self.body = False
        self.head_closed = False
        self.body_closed = False
        self.html_closed = False
        self.title = False
        self.metadata = []
        self.open_elements = []

    def flush(self):
        # Static CMS fields use normal HTML whitespace behavior.
        text = normalized_text("".join(self.pending))
        if text:
            self.events.append(("text", text))
        self.pending.clear()

    def close_optional_content(self):
        """Materialize an omitted content end at its actual boundary."""
        tag = self.open_elements.pop()
        self.events.append(("end", tag))

    def handle_starttag(self, tag, attrs):
        if self.body_closed:
            # Browsers reprocess markup after </body> or </html> in the
            # body; treating it as metadata would hide visible changes.
            raise AssertionError(f"CMS parity mismatch: Unexpected <{tag}> after document body")
        if self.head_closed and not self.body and tag != "body":
            # Unexpected markup can start an implicit browser body. The
            # bounded CMS output requires an explicit body boundary.
            raise AssertionError(f"CMS parity mismatch: Unexpected <{tag}> before document body")
        attributes = dict(attrs)
        if len(attrs) != len(attributes):
            raise AssertionError(f"Duplicate attributes on <{tag}>")
        if tag == "base":
            self.metadata.append(("base", attributes.get("href")))
        if tag == "html":
            self.metadata.append(("lang", attributes.get("lang")))
        if tag == "meta" and attributes.get("name") == "description":
            self.metadata.append(("description", attributes.get("content")))
        if tag == "title" and not self.body:
            self.title = True
        if tag == "body":
            self.body = True
        if not self.body:
            return
        self.flush()
        if self.open_elements and self.open_elements[-1] == "p" and tag in PARAGRAPH_END_START:
            self.close_optional_content()
        if self.open_elements and self.open_elements[-1] == "li" and tag == "li":
            self.close_optional_content()
        if "class" in attributes:
            attributes["class"] = " ".join(sorted((attributes["class"] or "").split()))
        if tag == "a" and "href" in attributes:
            attributes["href"] = local_link(attributes["href"] or "", self.base_path)
        self.events.append(("start", tag, tuple(sorted(attributes.items()))))
        if tag not in VOID:
            self.open_elements.append(tag)

    def handle_endtag(self, tag):
        if self.body_closed:
            if tag == "html" and not self.html_closed:
                self.html_closed = True
                return
            raise AssertionError(f"CMS parity mismatch: Unexpected </{tag}> after document body")
        if self.head_closed and not self.body:
            raise AssertionError(f"CMS parity mismatch: Unexpected </{tag}> before document body")
        if tag == "head" and not self.body:
            self.head_closed = True
        if self.title and tag == "title":
            self.metadata.append(("title", normalized_text("".join(self.pending))))
            self.pending.clear()
            self.title = False
        if self.body:
            self.flush()
            # Omitted p/li ends are implicit when their containing element
            # ends. Explicit ends still produce an event at their real location,
            # so moving text outside a styled paragraph/item cannot pass.
            if tag in self.open_elements or tag == "html":
                while (self.open_elements and self.open_elements[-1] != tag
                       and self.open_elements[-1] in OPTIONAL_CONTENT_END):
                    self.close_optional_content()
            if self.open_elements and self.open_elements[-1] == tag:
                self.open_elements.pop()
            if tag not in OPTIONAL_END and tag not in VOID:
                self.events.append(("end", tag))
            if tag in OPTIONAL_END:
                self.body = False
                self.body_closed = True
                self.html_closed = tag == "html"

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def finish(self):
        self.flush()
        while self.open_elements and self.open_elements[-1] in OPTIONAL_CONTENT_END:
            self.close_optional_content()

    def handle_data(self, data):
        if self.body_closed and normalized_text(data):
            raise AssertionError("CMS parity mismatch: Unexpected text after document body")
        if self.head_closed and not self.body and not self.body_closed and normalized_text(data):
            raise AssertionError("CMS parity mismatch: Unexpected text before document body")
        if self.body or self.title:
            self.pending.append(data)


def signature(markup: str, base_path: str) -> list:
    parser = Signature(base_path)
    parser.feed(markup)
    parser.close()
    parser.finish()
    return sorted(parser.metadata, key=repr) + parser.events


def verify_cms_output(destination: Path, *, base_path: str = "/",
                      content_path: Path = CONTENT) -> int:
    """Validate the public landing page; compare its semantic output to JSON."""
    document = load_validated_document(content_path)
    count = verify_static_site(destination, base_path=base_path,
                               required_css_markers=(".syn-button", ".syn-site-hero"))
    if count != 1 or not (destination / "index.html").is_file():
        raise AssertionError("Expected exactly one public CMS landing page")
    expected = signature(render_document(document), "/")
    actual = signature((destination / "index.html").read_text(encoding="utf-8"), base_path)
    for index, (want, got) in enumerate(zip_longest(expected, actual)):
        if want != got:
            raise AssertionError(f"CMS parity mismatch at event {index}: expected {want!r}, got {got!r}")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--base-path", default="/")
    parser.add_argument("--content", type=Path, default=CONTENT)
    args = parser.parse_args()
    verify_cms_output(args.destination, base_path=args.base_path, content_path=args.content)
    print("PASS: portable CMS HTML matches the canonical renderer; local CSS and zero browser JS.")
