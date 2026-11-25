"""Generate equivalent, no-runtime-JS CSS framework comparison fixtures.

Optional external compilers live only in benchmarks/frameworks/. This script
never fetches a CDN or silently replaces missing framework CSS with hand CSS.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks/frameworks"
FRAMEWORKS = ("syntyr", "plain", "pure", "tailwind", "uno", "daisyui")
FIXTURES = ("marketing", "dashboard")

# Semantic DOM is identical in all variants. Class names intentionally differ,
# to exercise each library as used by a developer rather than adding no-op CSS.
DEFAULT = {
    "page": "bench-page",
    "shell": "bench-shell",
    "header": "bench-header",
    "title": "bench-title",
    "subtle": "bench-muted",
    "grid": "bench-grid",
    "card": "bench-card",
    "stat": "bench-stat",
    "button": "bench-button",
    "form": "bench-form",
    "input": "bench-input",
    "tablebox": "bench-table-wrap",
    "table": "bench-table",
    "badge": "bench-badge",
    "cell": "bench-cell",
    "hero": "bench-hero",
    "section": "bench-section",
}
STYLES = {
    "plain": DEFAULT,
    "pure": {**DEFAULT, "button": "pure-button pure-button-primary",
             "form": "pure-form bench-form", "table": "pure-table pure-table-horizontal bench-table"},
    "syntyr": {
        "page": "syn-root syn-page", "shell": "syn-shell",
        "header": "syn-header", "title": "syn-heading", "subtle": "syn-muted",
        "grid": "syn-kpi-grid", "card": "syn-app-card", "stat": "syn-stat-value",
        "button": "syn-button syn-button--primary",
        "form": "syn-form", "input": "syn-input",
        "tablebox": "syn-table-wrap", "table": "syn-table",
        "badge": "syn-status syn-status--success",
        "cell": "bench-cell",
        "hero": "syn-hero", "section": "syn-stack",
    },
}
UTILITIES = {
    "page": "min-h-screen bg-slate-50 text-slate-900 font-sans",
    "shell": "mx-auto max-w-6xl px-5 py-8",
    "header": "mb-8 flex flex-wrap items-center justify-between gap-5 py-6",
    "title": "text-3xl font-semibold tracking-tight",
    "subtle": "text-sm text-slate-500",
    "grid": "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4",
    "card": "rounded-xl border border-slate-200 bg-white p-5 shadow-sm",
    "stat": "mt-2 text-3xl font-semibold",
    "button": "inline-block rounded-lg bg-indigo-700 px-4 py-2 font-medium text-white",
    "form": "flex flex-wrap items-center gap-3",
    "input": "rounded-lg border border-slate-300 bg-white px-3 py-2",
    "tablebox": "overflow-x-auto",
    "table": "w-full border-collapse text-left text-sm",
    "badge": "inline-block rounded-full bg-green-100 px-2 py-1 text-xs text-green-800",
    "cell": "border-b border-slate-200 px-3 py-5",
    "hero": "mb-8 rounded-xl bg-slate-900 p-8 text-white",
    "section": "my-8",
}
STYLES["tailwind"] = UTILITIES
STYLES["uno"] = UTILITIES
# daisyUI is a genuine Tailwind plugin; semantic classes are kept alongside
# Tailwind layout utilities where the plugin does not prescribe a composition.
STYLES["daisyui"] = {
    "page": "min-h-screen bg-base-200 text-base-content",
    "shell": "mx-auto max-w-6xl px-5 py-8",
    "header": "mb-8 flex flex-wrap items-center justify-between gap-5 py-6",
    "title": "text-3xl font-semibold",
    "subtle": "text-sm opacity-70",
    "grid": "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4",
    "card": "card border border-base-300 bg-base-100 p-5 shadow-sm",
    "stat": "stat-value",
    "button": "btn btn-primary",
    "form": "flex flex-wrap items-center gap-3",
    "input": "input",
    "tablebox": "overflow-x-auto",
    "table": "table table-zebra",
    "badge": "badge badge-success",
    "cell": "px-3 py-5",
    "hero": "rounded-xl bg-neutral p-8 text-neutral-content",
    "section": "my-8",
}

# Plain reference & Pure's layout fallback intentionally share structure.
# Pure's buttons/tables/forms are genuine Pure components, not emulated.
BASE_CSS = """
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,sans-serif;color:#0f172a;background:#f8fafc}
.bench-shell{max-width:1152px;margin:auto;padding:32px 20px}
.bench-header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:20px;margin-bottom:32px}
.bench-title{font-size:30px;font-weight:650;letter-spacing:-.02em;margin:0}
.bench-muted{color:#64748b;font-size:14px}
.bench-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.bench-card{border:1px solid #e2e8f0;border-radius:12px;background:white;padding:20px;box-shadow:0 1px 2px #0f172a0a}
.bench-stat{font-size:30px;font-weight:650;margin:8px 0 0}
.bench-button{display:inline-block;background:#4338ca;color:white;border:0;border-radius:8px;padding:9px 16px;text-decoration:none;font:inherit;cursor:pointer}
.bench-form{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.bench-input{border:1px solid #cbd5e1;border-radius:8px;padding:9px 12px;background:white;font:inherit}
.bench-table-wrap{overflow-x:auto}
.bench-table{width:100%;border-collapse:collapse;font-size:14px;text-align:left}
.bench-table th,.bench-table td{padding:12px;border-bottom:1px solid #e2e8f0}
.bench-table th{font-weight:600}
.bench-badge{display:inline-block;border-radius:999px;background:#dcfce7;color:#166534;font-size:12px;padding:3px 9px}
.bench-hero{background:#0f172a;color:white;border-radius:12px;padding:32px;margin-bottom:32px}
.bench-section{margin:32px 0}
.bench-hero>h2{margin:8px 0;line-height:1.2;font-size:28px}
.bench-hero>p{margin:8px 0}
.bench-card h3{font-size:18px;margin:0 0 8px}
.bench-card p{margin:6px 0 10px}
@media(max-width:800px){.bench-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:450px){.bench-grid{grid-template-columns:1fr}.bench-shell{padding:20px 12px}}
"""
PURE_ADAPTER = """
/* Pure.css supplies the component styles; only layout primitives are custom. */
.pure-table.bench-table{width:100%;font-size:14px}
.pure-button-primary{background:#4338ca;color:#fff;border-radius:8px}
.pure-form input[type=search]{border-radius:8px}
"""


def make_page(framework: str, fixture: str, *, rows: int = 120) -> str:
    if framework not in FRAMEWORKS or fixture not in FIXTURES or not 0 <= rows <= 20000:
        raise ValueError("Use a known framework/fixture and 0 <= rows <= 20000")
    css = STYLES[framework]

    def attr(role: str, *, anchor: str | None = None) -> str:
        result = f'class="{css[role]}"'
        if anchor:
            result += f' data-bench-anchor="{anchor}"'
        return result

    header = (f'<header {attr("header", anchor="header")}>'
              '<div><p>STUDIO / BENCHMARK</p>'
              f'<h1 {attr("title")}>Performance benchmark</h1></div>'
              '<nav aria-label="Primary">'
              '<a href="#details">Details</a> &nbsp; <a href="#contact">Contact</a>'
              '</nav></header>')
    form = (f'<form {attr("form")} action="#details" method="get" id="contact">'
            '<label for="query">Search campaigns</label>'
            f'<input {attr("input")} id="query" name="query" type="search" placeholder="Search" />'
            f'<button {attr("button")} type="submit">Search</button></form>')
    if fixture == "marketing":
        hero = (f'<section {attr("hero", anchor="hero")}>'
                '<p>PRODUCT / ANALYTICS</p><h2>Make complex work simpler</h2>'
                '<p>Shared content and structure, different styling implementations.</p>'
                f'<a {attr("button")} href="#details">Available now</a></section>')
        cards = "".join(
            f'<article {attr("card", anchor="first-card" if i == 0 else None)}>'
            f'<h3>Capability {i+1:02d}</h3>'
            '<p>Reliable workflows and clear reporting across teams.</p>'
            f'<span {attr("badge")}>Available</span></article>'
            for i in range(8)
        )
        main = (hero + f'<section {attr("section")} id="details"><h2>Features</h2>'
                f'<div {attr("grid")}>{cards}</div></section>' + form)
    else:
        cards = "".join(
            f'<article {attr("card", anchor="first-card" if i == 0 else None)}>'
            f'<p {attr("subtle")}>METRIC {i+1:02d}</p>'
            f'<p {attr("stat")}>{(i+1)*1742:,}</p></article>'
            for i in range(4)
        )
        record_rows = "".join(
            '<tr><th ' + attr("cell") + ' scope="row">Customer ' + f'{i:04d}</th>'
            f'<td {attr("cell")}>Campaign {i:04d}</td>'
            f'<td {attr("cell")}><span {attr("badge")}>Active</span></td>'
            f'<td {attr("cell")}>{(i+1)*164:,}</td></tr>'
            for i in range(rows)
        )
        table = (f'<section {attr("section")} id="details">'
                 '<h2>Recent campaigns</h2>'
                 f'<div {attr("tablebox", anchor="table")}>'
                 f'<table {attr("table")}><caption>Campaign revenue report</caption>'
                 f'<thead><tr><th {attr("cell")} scope="col">Customer</th><th {attr("cell")} scope="col">Campaign</th>'
                 f'<th {attr("cell")} scope="col">Status</th><th {attr("cell")} scope="col">Revenue</th></tr></thead>'
                 f'<tbody>{record_rows}</tbody></table></div></section>')
        main = f'<section {attr("grid")}>{cards}</section>' + table + form
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Framework benchmark / {fixture}</title>'
            f'<link rel="stylesheet" href="../{framework}.css"></head>'
            f'<body {attr("page")} data-syn-theme="studio">'
            f'<main {attr("shell")}>{header}{main}</main></body></html>\n')


class _Signature(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events = []

    def handle_starttag(self, tag, attrs):
        # Layout structure and meaningful attributes, not the styling API.
        attrs = tuple((k, v) for k, v in attrs if k not in ("class", "href")
                      and not (tag == "body" and k == "data-syn-theme"))
        self.events.append(("start", tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        self.events.append(("end", tag))

    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.events.append(("text", value))


def structural_signature(html: str) -> tuple:
    parser = _Signature()
    parser.feed(html)
    return tuple(parser.events)


def prepare_css(framework: str, output: Path, root: Path = ROOT) -> Path:
    """Bundle genuine distribution CSS. Never silently mock missing libraries."""
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"{framework}.css"
    if framework == "syntyr":
        inputs = [root / "dist/syntyr.core.css", root / "dist/syntyr.recipes.css"]
        css = "\n".join(item.read_text(encoding="utf8") for item in inputs)
    elif framework == "plain":
        css = BASE_CSS
    elif framework == "pure":
        pure = root / "benchmarks/frameworks/node_modules/purecss/build/pure-min.css"
        if not pure.is_file():
            raise FileNotFoundError("Pure CSS package unavailable: run npm ci in benchmarks/frameworks")
        css = pure.read_text(encoding="utf8") + "\n" + BASE_CSS + PURE_ADAPTER
    elif framework in ("tailwind", "uno", "daisyui"):
        src = output / f"{framework}.compiled.css"
        if not src.is_file():
            raise FileNotFoundError(f"{framework} compiled output missing: run npm run build in benchmarks/frameworks")
        css = src.read_text(encoding="utf8")
        if framework == "uno":
            reset = root / "benchmarks/frameworks/node_modules/@unocss/reset/tailwind.css"
            if not reset.is_file():
                raise FileNotFoundError("UnoCSS reset unavailable: run npm ci in benchmarks/frameworks")
            css = reset.read_text(encoding="utf8") + "\n" + css
    else:
        raise ValueError(f"Unknown framework {framework}")
    destination.write_text(css, encoding="utf8")
    return destination


def generate(output: Path, *, rows: int, frameworks: tuple[str, ...] = FRAMEWORKS) -> None:
    if not 0 <= rows <= 20000 or any(item not in FRAMEWORKS for item in frameworks):
        raise ValueError("Unknown framework or invalid row count")
    for framework in frameworks:
        directory = output / framework
        directory.mkdir(parents=True, exist_ok=True)
        for fixture in FIXTURES:
            (directory / f"{fixture}.html").write_text(
                make_page(framework, fixture, rows=rows), encoding="utf8")
    # Building generated Tailwind / Uno outputs is a separate explicit step.
    for framework in frameworks:
        if framework in ("syntyr", "plain"):
            prepare_css(framework, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BENCH / "generated")
    parser.add_argument("--rows", type=int, default=120)
    parser.add_argument("--css", action="store_true",
                        help="After npm run build, finalize compiled Tailwind/Uno stylesheets")
    args = parser.parse_args()
    try:
        if args.css:
            for framework in FRAMEWORKS:
                prepare_css(framework, args.output)
        else:
            generate(args.output, rows=args.rows)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    print(f"Fixtures ready in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
