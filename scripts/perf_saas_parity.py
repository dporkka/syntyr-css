"""Opt-in, design-normalized SaaS dashboard benchmark; no consumer dependencies.

Generate the same HTML and functional GET search across four CSS systems.
Run browser, layout, accessibility and source-size checks with optional dev tools.
Calibration CSS is identical for all variants. Measurements are NOT a ranking
of idiomatic unnormalized designs or developer-time productivity.
"""
from __future__ import annotations

import argparse
import hashlib
from contextlib import contextmanager
from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import threading
from urllib.parse import parse_qs, urlsplit

from perf_framework_fixtures import STYLES, prepare_css, structural_signature
from perf_framework_compare import (
    VIEWPORTS, css_sizes, markup_stats, metric_stats, sample, trial_order,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "benchmarks/frameworks/generated"
REFERENCE_CSS = ROOT / "benchmarks/frameworks/saas-parity.css"
FRAMEWORKS = ("syntyr", "tailwind", "daisyui", "plain")
ANCHORS = ("header", "metrics", "search", "table")
ROWS_MAX = 1000

# One data model and one template shared across all four backends.
def filtered_rows(query: str, rows: int) -> list[dict]:
    if not isinstance(rows, int) or not 0 <= rows <= ROWS_MAX:
        raise ValueError(f"rows must be from 0 to {ROWS_MAX}")
    needle = query.strip().casefold()
    values = [
        {"customer": f"Customer {i:04d}", "campaign": f"Campaign {i:04d}",
         "revenue": f"${(i + 1) * 164:,}"}
        for i in range(rows)
    ]
    return [row for row in values
            if needle in (row["customer"] + " " + row["campaign"]).casefold()]


def render_html(framework: str, *, query: str = "", rows: int = 32) -> str:
    if framework not in FRAMEWORKS:
        raise ValueError(f"Unsupported framework: {framework}")
    if len(query) > 100:
        raise ValueError("query too long")
    css = STYLES[framework]
    data = filtered_rows(query, rows)
    def cls(key: str) -> str:
        return escape(css[key], quote=True)
    def part(role: str, key: str, *, anchor: bool = False) -> str:
        return (f'class="{cls(key)}" data-bench-role="{role}"'
                + (f' data-bench-anchor="{role}"' if anchor else ""))
    # All text and semantics (except styling class names) are identical.
    metrics = "".join(
        f'<article {part("metric-card", "card")}>'
        f'<p>Metric {i + 1:02d}</p><p data-bench-role="metric-value">{(i + 1) * 1742:,}</p>'
        '</article>'
        for i in range(4)
    )
    records = "".join(
        '<tr><th scope="row">' + escape(item["customer"]) + '</th>'
        '<td>' + escape(item["campaign"]) + '</td>'
        '<td><span data-bench-role="status">Active</span></td>'
        '<td>' + item["revenue"] + '</td></tr>'
        for item in data
    )
    result = f"{len(data)} of {rows} campaigns"
    table = (
        f'<div {part("table", "tablebox", anchor=True)} tabindex="0" '
        'role="region" aria-label="Scrollable campaign results">'
        f'<table class="{cls("table")}"><caption>Campaign revenue report</caption>'
        '<thead><tr><th scope="col">Customer</th><th scope="col">Campaign</th>'
        '<th scope="col">Status</th><th scope="col">Revenue</th></tr></thead>'
        f'<tbody>{records}</tbody></table></div>'
        if data else '<p data-bench-role="empty">No matching campaigns.</p>'
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>SaaS dashboard parity benchmark</title>'
        f'<link rel="stylesheet" href="../{framework}.css">'
        '<link rel="stylesheet" href="../saas-parity.css"></head>'
        f'<body {part("page", "page")} data-bench-app data-syn-theme="studio">'
        f'<main {part("shell", "shell")}>'
        f'<header {part("header", "header", anchor=True)}>'
        '<div><p>OPERATIONS / DASHBOARD</p>'
        f'<h1 class="{cls("title")}">Campaign overview</h1></div>'
        '<nav aria-label="Primary"><a href="#campaigns">Campaigns</a>'
        ' <a href="#search">Search</a></nav></header>'
        f'<section {part("metrics", "grid", anchor=True)} aria-label="Performance metrics">'
        + metrics + '</section>'
        '<section id="search" data-bench-role="search-section">'
        '<h2>Campaign search</h2>'
        f'<form {part("search", "form", anchor=True)} action="saas.html" method="get">'
        '<label for="q">Search campaigns</label>'
        f'<input class="{cls("input")}" id="q" name="q" type="search" '
        f'value="{escape(query, quote=True)}" maxlength="100" />'
        f'<button class="{cls("button")}" type="submit">Search</button></form>'
        f'<p aria-live="polite" data-bench-role="count">{result}</p></section>'
        '<section id="campaigns" data-bench-role="campaigns"><h2>Campaigns</h2>'
        + table + '</section></main></body></html>\n'
    )


def generate_pages(output: Path, *, rows: int = 32) -> list[Path]:
    result = []
    for framework in FRAMEWORKS:
        path = output / framework / "saas.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_html(framework, rows=rows), encoding="utf8")
        result.append(path)
    output.mkdir(parents=True, exist_ok=True)
    (output / "saas-parity.css").write_bytes(REFERENCE_CSS.read_bytes())
    signatures = [structural_signature(p.read_text(encoding="utf8")) for p in result]
    if len(set(signatures)) != 1:
        raise RuntimeError("Semantic DOM or content differs across frameworks")
    return result


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, rows: int, **kwargs):
        self.rows = rows
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlsplit(self.path)
        sections = parsed.path.strip("/").split("/")
        if len(sections) == 2 and sections[1] == "saas.html":
            if sections[0] not in FRAMEWORKS:
                self.send_error(404)
                return
            query = parse_qs(parsed.query, keep_blank_values=True).get("q", [""])[0]
            if len(query) > 100:
                self.send_error(400)
                return
            contents = render_html(sections[0], query=query, rows=self.rows).encode("utf8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(contents)))
            self.end_headers()
            self.wfile.write(contents)
            return
        super().do_GET()

    def log_message(self, *_args):
        pass


@contextmanager
def local_parity_server(*, rows: int = 32, root: Path = OUTPUT):
    if not 0 <= rows <= ROWS_MAX:
        raise ValueError("invalid row count")
    handler = partial(_Handler, directory=str(root), rows=rows)
    http = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{http.server_address[1]}"
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)


def productivity_metrics(output: Path, *, rows: int) -> dict:
    """Objective structural proxies, explicitly not developer productivity time."""
    result = {}
    for framework in FRAMEWORKS:
        path = output / framework / "saas.html"
        stat = markup_stats(path)
        result[framework] = {
            **stat,
            "requires_compiler_for_framework_css": framework in ("tailwind", "daisyui"),
            "benchmark_shared_calibration_bytes": REFERENCE_CSS.stat().st_size,
            "human_authoring_minutes": None,
            "agent_tokens": None,
            "maintenance_edit_minutes": None,
        }
    return result


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_fingerprints(output: Path) -> dict:
    return {
        "generator_sha256": _sha256(Path(__file__)),
        "compiler_lock_sha256": _sha256(ROOT / "benchmarks/frameworks/package-lock.json"),
        "calibration_sha256": _sha256(REFERENCE_CSS),
        "html_sha256": {
            f: _sha256(output / f / "saas.html") for f in FRAMEWORKS
        },
    }


def visual_anchors_for_rows(rows: int) -> tuple[str, ...]:
    """The empty-state fixture has no table element to measure."""
    if not 0 <= rows <= ROWS_MAX:
        raise ValueError("invalid row count")
    return ANCHORS if rows else ANCHORS[:-1]


def visual_deviations(anchors: dict, *, reference: str = "plain",
                      tolerance: float = .05,
                      required: tuple[str, ...] = ANCHORS) -> list[dict]:
    if not 0 <= tolerance < 1:
        raise ValueError("invalid tolerance")
    baseline = anchors.get(reference, {})
    findings = []
    missing = [name for name in required if name not in baseline]
    for name in missing:
        findings.append({"framework": reference, "anchor": name, "issue": "reference missing"})
    for framework, readings in anchors.items():
        if framework == reference:
            continue
        for anchor, expected in baseline.items():
            actual = readings.get(anchor)
            if actual is None:
                findings.append({"framework": framework, "anchor": anchor, "issue": "missing anchor"})
                continue
            for key in ("width", "height", "background", "font"):
                if key not in actual:
                    findings.append({"framework": framework, "anchor": anchor,
                                     "issue": "missing property", "property": key})
                    continue
                if isinstance(expected[key], (int, float)):
                    delta = abs(actual[key] - expected[key]) / max(abs(expected[key]), 1)
                    different = delta > tolerance
                else:
                    different = actual[key] != expected[key]
                if different:
                    findings.append({"framework": framework, "anchor": anchor,
                                     "property": key, "expected": expected[key],
                                     "actual": actual[key]})
    return findings


def _browser_check(page, base: str, framework: str, *, rows: int,
                   axe_script: Path | None) -> dict:
    from playwright.sync_api import expect
    checks = {}
    page.goto(f"{base}/{framework}/saas.html")
    expect(page.locator('main')).to_have_count(1)
    expect(page.locator('h1')).to_have_count(1)
    expect(page.locator('tbody tr')).to_have_count(rows)
    page.get_by_label("Search campaigns").fill("Customer 0004")
    page.get_by_label("Search campaigns").press("Enter")
    expect(page.locator('tbody tr')).to_have_count(1 if rows > 4 else 0)
    if rows > 4:
        row = page.locator('tbody tr').first
        expect(row).to_contain_text("Customer 0004")
        expect(row).to_contain_text("Campaign 0004")
    expect(page.locator('[data-bench-role="count"]')).to_contain_text(
        f"{1 if rows > 4 else 0} of {rows}")
    page.get_by_label("Search campaigns").fill("no-such-customer")
    page.get_by_role("button", name="Search").click()
    expect(page.get_by_text("No matching campaigns.")).to_be_visible()
    checks["functional_parity"] = "pass"
    page.goto(f"{base}/{framework}/saas.html")
    checks["root_overflow"] = page.evaluate("""() => ({
      scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth
    })""")
    checks["anchors"] = page.evaluate("""() => Object.fromEntries(
      [...document.querySelectorAll('[data-bench-anchor]')].map(el => {
        const rect=el.getBoundingClientRect(), css=getComputedStyle(el);
        return [el.dataset.benchAnchor, {
          width:+rect.width.toFixed(1), height:+rect.height.toFixed(1),
          background:css.backgroundColor, font:css.fontSize
        }];
      })
    )""")
    if axe_script is None:
        checks["axe"] = {"status": "not-run"}
    else:
        page.add_script_tag(path=str(axe_script))
        result = page.evaluate("""async () => {
          const output = await axe.run(document, {
            runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}
          });
          return {
            violations:output.violations.map(x=>({id:x.id,nodes:x.nodes.length})),
            incomplete:output.incomplete.map(x=>({id:x.id,nodes:x.nodes.length}))
          };
        }""")
        checks["axe"] = {"status": "executed", **result}
    return checks


def accessibility_clean(audit: dict) -> bool:
    """Inconclusive axe results need manual review, not a success label."""
    return (audit.get("status") == "executed"
            and not audit.get("violations")
            and not audit.get("incomplete"))


def browser_launch_options(engine: str, webkit_executable: Path | None) -> dict:
    """Only override WebKit launch when the developer explicitly supplies a path."""
    if engine == "webkit" and webkit_executable is not None:
        return {"executable_path": str(webkit_executable)}
    return {}


def benchmark(output: Path, *, rows: int, runs: int, browsers: list[str],
              viewports: list[str], axe_script: Path | None, screenshots: Path | None,
              webkit_executable: Path | None = None) -> dict:
    if runs < 1 or not browsers or not viewports:
        raise ValueError("Require runs and browser/viewport selection")
    if any(v not in VIEWPORTS for v in viewports) or any(b not in
            ("chromium", "firefox", "webkit") for b in browsers):
        raise ValueError("Unknown browser or viewport")
    for name in (*FRAMEWORKS, "saas-parity"):
        stylesheet = output / f"{name}.css"
        if not stylesheet.is_file():
            raise FileNotFoundError(f"Missing genuine stylesheet {name}.css")
        if stylesheet.stat().st_size == 0:
            raise ValueError(f"empty framework stylesheet: {name}.css")
    for framework in FRAMEWORKS:
        page = output / framework / "saas.html"
        if not page.is_file() or page.read_text(encoding="utf8") != render_html(
            framework, rows=rows
        ):
            raise ValueError(f"stale {framework} fixture for {rows} rows: rerun --prepare")
    if (output / "saas-parity.css").read_bytes() != REFERENCE_CSS.read_bytes():
        raise ValueError("stale calibration CSS: rerun --prepare")
    if axe_script is not None and not axe_script.is_file():
        raise FileNotFoundError(f"Missing axe-core script: {axe_script}")
    if webkit_executable is not None and not webkit_executable.is_file():
        raise FileNotFoundError(f"Missing developer-only WebKit wrapper: {webkit_executable}")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Use a developer-only environment with Python Playwright") from exc
    report = {
        "scenario": "controlled-saas-dashboard-parity",
        "context": {"host": platform.platform(), "runs_per_variant": runs, "rows": rows,
                    "frameworks": list(FRAMEWORKS), "browsers": browsers, "viewports": viewports},
        "visual_method": "same semantic DOM and content, same additional calibration CSS; compare browser computed anchors, not pixel-identical screenshots",
        "stylesheets": {name: css_sizes(output / f"{name}.css") for name in (*FRAMEWORKS, "saas-parity")},
        "productivity_proxies": productivity_metrics(output, rows=rows),
        "input_fingerprints": {
            **input_fingerprints(output),
            "axe_script_sha256": _sha256(axe_script) if axe_script else None,
        },
        "screenshot_directory": str(screenshots) if screenshots else None,
        "results": [],
        "limitations": [
            "Identical calibration CSS deliberately reduces style differences, so results do not compare default looks or unnormalized idiomatic framework CSS.",
            "Equivalent presentation is tested by computed anchor geometry/font/background and screenshots for review; this is not pixel-level visual equivalence.",
            "No developer/agent time, LLM token cost, or maintainability advantage was measured; class/HTML bytes are only structural proxies.",
            "Server-side search uses one shared Python backend for all four variants; it is not a frontend framework performance comparison.",
            "Synthetic localhost timings and uncompressed resources are not field Core Web Vitals or real-world user productivity.",
            "Accessibility requires manual keyboard/screen reader/zoom/color review; axe automated audits cannot certify WCAG.",
            "Optional test scripts do not run in consumer pages. No required JavaScript or npm runtime dependencies.",
        ],
    }
    with local_parity_server(rows=rows, root=output) as base:
        with sync_playwright() as playwright:
            for name in browsers:
                try:
                    browser = getattr(playwright, name).launch(
                        **browser_launch_options(name, webkit_executable)
                    )
                except Exception as exc:
                    raise RuntimeError(
                        f"{name} launch failed: {str(exc).splitlines()[0]}"
                    ) from exc
                try:
                    report.setdefault("browser_versions", {})[name] = browser.version
                    for viewport in viewports:
                        geometry = {}
                        behavior = {}
                        scores = {f: {"cold": [], "warm": []} for f in FRAMEWORKS}
                        for iteration in range(runs):
                            for f in trial_order(list(FRAMEWORKS), iteration):
                                address = f"{base}/{f}/saas.html"
                                shot = (screenshots / f"{name}-{viewport}-{f}.png"
                                        if screenshots is not None and iteration == 0 else None)
                                values, _ = sample(browser, name, address, viewport, shot)
                                for cache in ("cold", "warm"):
                                    scores[f][cache].append(values[cache])
                                if iteration == 0:
                                    context = browser.new_context(viewport=VIEWPORTS[viewport],
                                                                  reduced_motion="reduce")
                                    try:
                                        page = context.new_page()
                                        behavior[f] = _browser_check(page, base, f, rows=rows,
                                                                    axe_script=axe_script)
                                        geometry[f] = behavior[f]["anchors"]
                                    finally:
                                        context.close()
                        deviations = visual_deviations(geometry, required=visual_anchors_for_rows(rows))
                        failures = [
                            f for f, result in behavior.items()
                            if result["functional_parity"] != "pass" or
                            result["root_overflow"]["scroll"] > result["root_overflow"]["client"] or
                            (result["axe"]["status"] == "executed"
                             and not accessibility_clean(result["axe"]))
                        ]
                        report["results"].append({
                            "browser": name, "viewport": viewport, "functional": behavior,
                            "visual_deviations": deviations, "visual_anchor_parity": not deviations,
                            "gate_pass": not deviations and not failures,
                            "metric_stats": {
                                f: {cache: {key: metric_stats(samples, key) for key in (
                                    "navigation_ms", "fcp_ms", "lcp_ms", "cls",
                                    "style_recalc_ms", "layout_ms", "transfer_bytes")}
                                    for cache, samples in cache_data.items()}
                                for f, cache_data in scores.items()},
                        })
                finally:
                    browser.close()
    report["all_checked_gates_pass"] = all(x["gate_pass"] for x in report["results"])
    report["accessibility_audit_complete"] = all(
        item["axe"]["status"] == "executed"
        for result in report["results"] for item in result["functional"].values()
    )
    report["all_gates_complete_and_pass"] = (
        report["all_checked_gates_pass"] and report["accessibility_audit_complete"]
    )
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generated", type=Path, default=OUTPUT)
    p.add_argument("--rows", type=int, default=32)
    p.add_argument("--prepare", action="store_true",
                   help="Generate four pages and calibration CSS; generate/compile vendor CSS separately")
    p.add_argument("--finalize-css", action="store_true",
                   help="Bundle authentic pinned vendor CSS and copy calibration CSS")
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--browsers", default="chromium,firefox,webkit")
    p.add_argument("--viewports", default="mobile,desktop")
    p.add_argument("--axe", type=Path, help="Local axe-core minified JS for automated audits")
    p.add_argument("--webkit-executable", type=Path,
                   help="Optional test-only wrapper for a locally provisioned WebKit binary")
    p.add_argument("--screenshots", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    if not 0 <= args.rows <= ROWS_MAX:
        p.error("rows out of range")
    try:
        if args.prepare:
            generate_pages(args.generated, rows=args.rows)
            print(f"Generated {len(FRAMEWORKS)} semantic-equivalent pages")
            return 0
        if args.finalize_css:
            for framework in FRAMEWORKS:
                prepare_css(framework, args.generated)
            (args.generated / "saas-parity.css").write_bytes(REFERENCE_CSS.read_bytes())
            print("Bundled actual framework stylesheets and shared reference styles")
            return 0
        report = benchmark(args.generated, rows=args.rows, runs=args.runs,
                           browsers=args.browsers.split(","),
                           viewports=args.viewports.split(","),
                           axe_script=args.axe, screenshots=args.screenshots,
                           webkit_executable=args.webkit_executable)
        payload = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload)
        else:
            print(payload)
        return 0 if report["all_checked_gates_pass"] else 1
    except (OSError, RuntimeError, ValueError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
