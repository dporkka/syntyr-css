"""Offline, deterministic asset audit for three design benchmark pages.

Measures transferred stylesheet/markup sizes, not LCP, browser execution or accessibility.
Run: python3 scripts/design_reference_audit.py [--json]
"""
from __future__ import annotations

import argparse
import gzip
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ("marketing", "crm", "documentation")
SAMPLE_DIR = ROOT / "examples/design-benchmarks"

# Explicit HTML/SVG event handler names: do not treat unrelated "one"/"only" attributes as JS.
# Keep this as a conservative static list for a dependency-free audit.
EVENT_HANDLER_ATTRIBUTES = frozenset("""
onabort onanimationcancel onanimationend onanimationiteration onanimationstart
onauxclick onbeforeinput onbeforematch onbeforetoggle onbeforeunload onblur
oncancel oncanplay oncanplaythrough onchange onclick onclose oncontextmenu
oncopy oncuechange oncut ondblclick ondrag ondragend ondragenter ondragleave
ondragover ondragstart ondrop ondurationchange onemptied onended onerror
onfocus onfocusin onfocusout onformdata onfullscreenchange onfullscreenerror
ongotpointercapture onhashchange oninput oninvalid onkeydown onkeypress
onkeyup onlanguagechange onload onloadeddata onloadedmetadata onloadstart
onlostpointercapture onmessage onmessageerror onmousedown onmouseenter
onmouseleave onmousemove onmouseout onmouseover onmouseup onoffline
ononline onopen onpagehide onpageshow onpaste onpause onplay onplaying
onpointercancel onpointerdown onpointerenter onpointerleave onpointermove
onpointerout onpointerover onpointerrawupdate onpointerup onpopstate
onprogress onratechange onrejectionhandled onreset onresize onscroll
onscrollend onsecuritypolicyviolation onseeked onseeking onselect
onselectionchange onselectstart onslotchange onstalled onstorage onsubmit
onsuspend ontimeupdate ontoggle ontransitioncancel ontransitionend
ontransitionrun ontransitionstart onunhandledrejection onunload onvolumechange
onwaiting onwheel
""".split())

# Ignore CSS comments and quoted strings, then count actual declaration names.
CSS_NON_CODE = re.compile(r'''/\*.*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*' ''', re.DOTALL | re.VERBOSE)
TOKEN_DECLARATION = re.compile(r"(?:^|[;{])\s*(--syn-[\w-]+)\s*:", re.MULTILINE)
CSS_IMPORT_DIRECTIVE = re.compile(r"(?<![\w-])@import\b", re.IGNORECASE)


def reject_imports(css: str, source: str) -> None:
    """Fail closed instead of reporting incomplete totals for imported CSS."""
    code = CSS_NON_CODE.sub("", css)
    if CSS_IMPORT_DIRECTIVE.search(code):
        raise ValueError(f"CSS @import is not supported in offline audit: {source}")



def token_declarations(css_sources: list[str]) -> set[str]:
    return {
        token
        for css in css_sources
        for token in TOKEN_DECLARATION.findall(CSS_NON_CODE.sub("", css))
    }


class Assets(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stylesheets: list[str] = []
        self.scripts: list[str | None] = []
        self.inline_script_bytes = 0
        self.inline_event_handler_bytes = 0
        self.inline_styles: list[str] = []
        self._in_script = False
        self._in_style = False

    def handle_starttag(self, tag: str, pairs: list[tuple[str, str | None]]) -> None:
        attrs = dict(pairs)
        for name, value in pairs:
            if value is not None and name in EVENT_HANDLER_ATTRIBUTES:
                self.inline_event_handler_bytes += len(value.encode("utf-8"))
        if attrs.get("style"):
            self.inline_styles.append(attrs["style"])
        if tag == "link" and "stylesheet" in {token.lower() for token in (attrs.get("rel") or "").split()}:
            self.stylesheets.append(attrs.get("href") or "")
        if tag == "script":
            self.scripts.append(attrs.get("src"))
            self._in_script = True
        if tag == "style":
            self._in_style = True

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self.inline_script_bytes += len(data.encode("utf-8"))
        if self._in_style:
            self.inline_styles.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_script = False
        if tag == "style":
            self._in_style = False


def _local_file(href: str, parent: Path) -> Path:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
        raise ValueError(f"external stylesheet or unsupported URL: {href}")
    if parsed.query or parsed.fragment:
        raise ValueError(f"stylesheet query/fragment is not supported: {href}")
    path = (parent / parsed.path).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError(f"stylesheet escapes repository: {href}")
    if not path.is_file():
        raise FileNotFoundError(f"missing stylesheet: {href}")
    return path


def audit_page(markup: str, parent: Path) -> dict[str, int]:
    assets = Assets()
    assets.feed(markup)
    syntyr = []
    custom = []
    seen_stylesheets: set[Path] = set()
    for href in assets.stylesheets:
        file = _local_file(href, parent)
        if file in seen_stylesheets:
            continue
        seen_stylesheets.add(file)
        data = file.read_bytes()
        reject_imports(data.decode("utf-8"), str(file))
        group = syntyr if file.is_relative_to(ROOT / "dist") else custom
        group.append(data)
    bytes_syntyr = sum(map(len, syntyr))
    bytes_custom = sum(map(len, custom))
    for css in assets.inline_styles:
        reject_imports(css, "inline style")
    inline_css = "\n".join(assets.inline_styles).encode("utf-8")
    bytes_inline_css = sum(len(css.encode("utf-8")) for css in assets.inline_styles)
    gzip_inline_css = len(gzip.compress(inline_css, mtime=0)) if inline_css else 0
    gzip_custom_css = sum(len(gzip.compress(x, mtime=0)) for x in custom)
    runtime_js = assets.inline_script_bytes + assets.inline_event_handler_bytes
    for script in assets.scripts:
        if script:
            parsed = urlsplit(script)
            if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
                raise ValueError(f"external script not included in offline audit: {script}")
            candidate = (parent / parsed.path).resolve()
            if not candidate.is_relative_to(ROOT) or not candidate.is_file():
                raise FileNotFoundError(f"missing script: {script}")
            runtime_js += candidate.stat().st_size

    return {
        "markup_bytes": len(markup.encode("utf-8")),
        "syntyr_css_bytes": bytes_syntyr,
        "syntyr_css_gzip_bytes": sum(len(gzip.compress(x, mtime=0)) for x in syntyr),
        "custom_css_bytes": bytes_custom,
        "custom_css_gzip_bytes": gzip_custom_css,
        "inline_css_bytes": bytes_inline_css,
        "inline_css_gzip_bytes": gzip_inline_css,
        "custom_css_total_bytes": bytes_custom + bytes_inline_css,
        "custom_css_total_gzip_bytes": gzip_custom_css + gzip_inline_css,
        "custom_token_overrides": len(token_declarations(
            [*(x.decode("utf-8") for x in custom), *assets.inline_styles]
        )),
        "runtime_js_bytes": runtime_js,
        "script_tags": len(assets.scripts),
        "external_stylesheets": 0,
        "missing_stylesheets": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable data")
    options = parser.parse_args()
    reports = {name: audit_page((SAMPLE_DIR / f"{name}.html").read_text(encoding="utf-8"), SAMPLE_DIR)
               for name in SAMPLES}
    result = {"method": "source file sizes with deterministic gzip (mtime=0); not browser timings",
              "pages": reports}
    if options.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, report in reports.items():
            print(f"{name}: HTML={report['markup_bytes']} B; "
                  f"Syntyr CSS gzip={report['syntyr_css_gzip_bytes']} B; "
                  f"custom CSS gzip={report['custom_css_total_gzip_bytes']} B "
                  f"(linked={report['custom_css_gzip_bytes']}, inline={report['inline_css_gzip_bytes']}); "
                  f"runtime JS={report['runtime_js_bytes']} B; "
                  f"custom token overrides={report['custom_token_overrides']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
