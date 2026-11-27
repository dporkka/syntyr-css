"""Cross-framework browser benchmark for Syntyr, plain CSS, Pure, Tailwind, Uno, daisyUI, Blades, Bulma.

This benchmark compares idiomatic styling implementations of the same semantic
DOM and text. It does NOT prove visual pixel parity or field Core Web Vitals.
No application runtime JavaScript, external CDN or framework JS is loaded.

Generate fixtures first:
  python3 scripts/perf_framework_fixtures.py
  (cd benchmarks/frameworks && npm ci && npm run build)
  python3 scripts/perf_framework_fixtures.py --css

Run browser metrics with optional developer Playwright:
  python3 scripts/perf_framework_compare.py --runs 10 --screenshots /tmp/syntyr-shots
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
import gzip
import hashlib
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "benchmarks/frameworks/generated"
FRAMEWORKS = ("syntyr", "plain", "pure", "tailwind", "uno", "daisyui", "blades", "bulma")
FIXTURES = ("dashboard", "marketing")
BROWSERS = ("chromium", "firefox", "webkit")
VIEWPORTS = {"mobile": {"width": 390, "height": 844},
             "desktop": {"width": 1365, "height": 900}}
METRICS = ("navigation_ms", "fcp_ms", "lcp_ms", "cls", "style_recalc_ms",
           "layout_ms", "css_requests", "transfer_bytes")


def metric_stats(records: list[dict], metric: str) -> dict:
    numbers = sorted(record[metric] for record in records
                     if record.get(metric) is not None
                     and not isinstance(record[metric], bool))
    if not numbers:
        return {"median": None, "p75": None, "samples": 0}
    rank = (3 * len(numbers) + 3) // 4
    return {"median": round(statistics.median(numbers), 3),
            "p75": numbers[rank - 1], "samples": len(numbers)}


def trial_order(names: list[str], index: int) -> list[str]:
    if not names:
        return []
    index %= len(names)
    return names[index:] + names[:index]


def validate_selection(frameworks: list[str], browsers: list[str],
                       viewports: list[str], runs: int) -> None:
    for selected, supported, name in (
        (frameworks, FRAMEWORKS, "frameworks"),
        (browsers, BROWSERS, "browsers"),
        (viewports, tuple(VIEWPORTS), "viewports"),
    ):
        if not selected or len(selected) != len(set(selected)) or any(
                item not in supported for item in selected):
            raise ValueError(f"Invalid or duplicate {name}: {selected}")
    if runs <= 0:
        raise ValueError("runs must be positive")


def benchmark_provenance(root: Path = ROOT) -> dict:
    """Record immutable inputs, including when checkout metadata is unavailable."""
    lock = root / "benchmarks/frameworks/package-lock.json"
    manifest = root / "benchmarks/frameworks/package.json"
    versions = json.loads(manifest.read_text(encoding="utf8"))["devDependencies"]
    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(["git", "-C", str(root), *args],
                                    check=True, capture_output=True, text=True,
                                    timeout=5)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip()
    status = git("status", "--porcelain")
    return {
        "git_revision": git("rev-parse", "HEAD"),
        "working_tree_dirty": None if status is None else bool(status),
        "benchmark_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "vendor_versions": {
            "blades": versions["@anyblades/blades"],
            "bulma": versions["bulma"],
        },
    }


def markup_stats(path: Path) -> dict:
    """Count generated HTML and class sizes without guessing LLM tokenization."""
    class Inspector(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.classes = []
            self.bytes_in_values = 0

        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key == "class" and value is not None:
                    self.classes.extend(value.split())
                    self.bytes_in_values += len(value.encode("utf-8"))

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)

    source = path.read_bytes()
    reader = Inspector()
    reader.feed(source.decode("utf-8"))
    reader.close()
    return {"html_bytes": len(source), "class_tokens": len(reader.classes),
            "distinct_class_tokens": len(set(reader.classes)),
            "class_attribute_bytes": reader.bytes_in_values}


def css_sizes(path: Path) -> dict:
    source = path.read_bytes()
    try:
        import brotli
        br_size = len(brotli.compress(source))
    except ImportError:
        br_size = None
    return {"raw_bytes": len(source),
            "gzip_bytes": len(gzip.compress(source, mtime=0)),
            "brotli_bytes": br_size}


class _Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.split("?")[0].endswith(".css"):
            self.send_header("Cache-Control", "public, max-age=3600")
        else:
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *_args):
        pass


@contextmanager
def local_server(root: Path):
    server = ThreadingHTTPServer(("127.0.0.1", 0),
                                 partial(_Handler, directory=str(root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


# Injected only by the Playwright test, not application JS.
INIT_JS = """(() => {
  const state = {lcp: null, cls: null, observers: {}};
  window.__syntyrPerf = state;
  if (!('PerformanceObserver' in window)) return;
  const supported = PerformanceObserver.supportedEntryTypes || [];
  const collect = (type, entries) => {
    for (const entry of entries) {
      if (type === 'largest-contentful-paint') state.lcp = entry.startTime;
      if (type === 'layout-shift' && !entry.hadRecentInput) state.cls += entry.value;
    }
  };
  state.flush = () => {
    for (const [type, observer] of Object.entries(state.observers)) {
      collect(type, observer.takeRecords());
    }
  };
  for (const type of ['largest-contentful-paint', 'layout-shift']) {
    if (!supported.includes(type)) continue;
    try {
      const observer = new PerformanceObserver(list => collect(type, list.getEntries()));
      observer.observe({type, buffered: true});
      state.observers[type] = observer;
      if (type === 'layout-shift') state.cls = 0;
    } catch (_) { /* unsupported */ }
  }
})()"""


def cdp_metrics(session) -> dict:
    if session is None:
        return {}
    return {entry["name"]: entry["value"]
            for entry in session.send("Performance.getMetrics")["metrics"]}


def sample(browser, browser_name: str, url: str, viewport: str,
           screenshot: Path | None) -> tuple[dict, dict]:
    context = browser.new_context(viewport=VIEWPORTS[viewport],
                                  reduced_motion="reduce", device_scale_factor=1)
    page = context.new_page()
    page.add_init_script(INIT_JS)
    responses = []
    page.on("response", lambda response: responses.append(response)
            if response.request.resource_type == "stylesheet" else None)
    cdp = None
    if browser_name == "chromium":
        cdp = context.new_cdp_session(page)
        cdp.send("Performance.enable")
    readings, anchors = {}, {}
    try:
        for cache in ("cold", "warm"):
            responses.clear()
            before = cdp_metrics(cdp)
            start = time.perf_counter()
            response = page.goto(url, wait_until="load", timeout=60000)
            if response is None or response.status >= 400:
                raise RuntimeError(f"Navigation failed {url}: {response.status if response else 'no response'}")
            page.evaluate("() => void document.body.offsetHeight")
            page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            navigation = (time.perf_counter() - start) * 1000
            after = cdp_metrics(cdp)
            state = page.evaluate("""() => {
              const paint = performance.getEntriesByType('paint')
                .find(e => e.name === 'first-contentful-paint');
              window.__syntyrPerf?.flush?.();
              const s = window.__syntyrPerf || {};
              const navigation = performance.getEntriesByType('navigation')[0];
              const resources = performance.getEntriesByType('resource');
              return {
                fcp_ms: paint?.startTime ?? null,
                lcp_ms: s.lcp ?? null,
                cls: s.cls ?? null,
                transfer_bytes: (navigation?.transferSize ?? 0) +
                  resources.reduce((n, e) => n + (e.transferSize || 0), 0)
              };
            }""")

            def diff(name):
                if name not in before or name not in after:
                    return None
                return round(max(0, after[name] - before[name]) * 1000, 3)

            readings[cache] = {
                **state,
                "navigation_ms": round(navigation, 3),
                "style_recalc_ms": diff("RecalcStyleDuration"),
                "layout_ms": diff("LayoutDuration"),
                "css_requests": len(responses),
            }
            # Visual evidence is recorded, not falsely declared pixel equivalent.
            if cache == "warm":
                anchors = page.evaluate("""() => Object.fromEntries(
                  [...document.querySelectorAll('[data-bench-anchor]')].map(el => {
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return [el.dataset.benchAnchor, {
                      x: +rect.x.toFixed(1), y: +rect.y.toFixed(1),
                      width: +rect.width.toFixed(1), height: +rect.height.toFixed(1),
                      font: style.fontSize, background: style.backgroundColor
                    }]
                  })
                )""")
                if screenshot:
                    screenshot.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(screenshot), full_page=True,
                                    animations="disabled")
        return readings, anchors
    finally:
        context.close()


def geometry_warnings(anchors: dict, *, reference: str = "plain",
                      tolerance: float = 0.2) -> list[dict]:
    """Surface obvious visual confounding; never claim pixel equivalence."""
    if not 0 <= tolerance < 1:
        raise ValueError("tolerance must be between 0 and 1")
    baseline = anchors.get(reference, {})
    findings = []
    for name, positions in anchors.items():
        if name == reference:
            continue
        for label, expected in baseline.items():
            actual = positions.get(label)
            if actual is None:
                findings.append({"framework": name, "anchor": label,
                                 "issue": "missing anchor"})
                continue
            for dimension in ("width", "height"):
                base = expected[dimension]
                delta = abs(actual[dimension] - base) / max(base, 1)
                if delta > tolerance:
                    findings.append({
                        "framework": name, "anchor": label,
                        "dimension": dimension,
                        "reference": base, "actual": actual[dimension],
                        "relative_difference": round(delta, 3),
                    })
    return findings


def benchmark(output: Path, frameworks: list[str], browsers: list[str],
              viewports: list[str], fixtures: list[str], runs: int,
              screenshots: Path | None) -> dict:
    try:
        from playwright.sync_api import sync_playwright, Error as PlaywrightError
    except ImportError as exc:
        raise RuntimeError("Install optional Python Playwright in a developer virtualenv") from exc

    # Missing artifact is a hard error; no silent fallback to hand-authored CSS.
    for framework in frameworks:
        stylesheet = output / f"{framework}.css"
        if not stylesheet.is_file() or not stylesheet.stat().st_size:
            raise FileNotFoundError(f"Missing stylesheet: {stylesheet}")
        for fixture in fixtures:
            page = output / framework / f"{fixture}.html"
            if not page.is_file():
                raise FileNotFoundError(f"Missing fixture: {page}")

    data = {"context": {"host_os": platform.platform(),
                        "python": sys.version.split()[0],
                        "runs_per_variant": runs,
                        "fixtures": fixtures,
                        "frameworks": frameworks,
                        "provenance": benchmark_provenance(ROOT),
                        "cold": "fresh browser context",
                        "warm": "second navigation in the same context"},
            "stylesheets": {name: css_sizes(output / f"{name}.css")
                            for name in frameworks},
            "markup": {fixture: {name: markup_stats(output / name / f"{fixture}.html")
                                 for name in frameworks} for fixture in fixtures},
            "results": [],
            "limitations": [
                "Synthetic localhost browser benchmark; not field Core Web Vitals, INP, or production ranking.",
                "Markup structure and text match, but idiomatic framework styles are NOT pixel-identical.",
                "Compare screenshots and anchor geometry before drawing design-equivalent conclusions.",
                "Style recalculation and layout timing use Chromium CDP only; absent values are null.",
                "Raw and gzip/Brotli CSS sizes are not HTTP transfer measurements; localhost serves CSS uncompressed.",
                "HTML bytes and class counts are measured source sizes, not LLM token counts or generation cost.",
                "Scripts executed by Playwright are test instrumentation, not application runtime JS.",
                "No synthetic paint-duration estimate: browser trace required for paint-cost conclusions.",
            ]}
    with local_server(output) as base:
        with sync_playwright() as p:
            for browser_name in browsers:
                try:
                    browser = getattr(p, browser_name).launch()
                except PlaywrightError as exc:
                    raise RuntimeError(f"Cannot launch {browser_name}: {str(exc).splitlines()[0]}") from exc
                try:
                    data.setdefault("browser_versions", {})[browser_name] = browser.version
                    for fixture in fixtures:
                        for viewport in viewports:
                            scores = {name: {"cold": [], "warm": []} for name in frameworks}
                            anchors = {}
                            for iteration in range(runs):
                                for framework in trial_order(frameworks, iteration):
                                    url = f"{base}/{framework}/{fixture}.html"
                                    shot = (screenshots / f"{browser_name}-{fixture}-{viewport}-{framework}.png"
                                            if screenshots and iteration == 0 else None)
                                    values, anchor = sample(browser, browser_name, url, viewport, shot)
                                    for cache in ("cold", "warm"):
                                        scores[framework][cache].append(values[cache])
                                    if iteration == 0:
                                        anchors[framework] = anchor
                            data["results"].append({
                                "browser": browser_name, "fixture": fixture, "viewport": viewport,
                                "metrics": {
                                    name: {
                                        cache: {key: metric_stats(rows, key) for key in METRICS}
                                        for cache, rows in entries.items()
                                    } for name, entries in scores.items()},
                                "visual_anchors": anchors,
                                "geometry_warnings": geometry_warnings(anchors,
                                    reference="plain" if "plain" in anchors else frameworks[0]),
                                "visual_parity": "not verified; inspect screenshots and anchors",
                            })
                finally:
                    browser.close()
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", type=Path, default=OUTPUT)
    parser.add_argument("--frameworks", default=",".join(FRAMEWORKS))
    parser.add_argument("--browsers", default="chromium,firefox,webkit")
    parser.add_argument("--viewports", default="mobile,desktop")
    parser.add_argument("--fixtures", default="dashboard,marketing")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    frameworks, browsers, viewports, fixtures = (
        args.frameworks.split(","), args.browsers.split(","),
        args.viewports.split(","), args.fixtures.split(","))
    try:
        validate_selection(frameworks, browsers, viewports, args.runs)
        if not fixtures or len(set(fixtures)) != len(fixtures) or any(
                fixture not in FIXTURES for fixture in fixtures):
            raise ValueError(f"Invalid fixtures: {fixtures}")
        report = benchmark(args.generated, frameworks, browsers, viewports,
                           fixtures, args.runs, args.screenshots)
        serialized = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf8")
            print(f"Wrote benchmark report to {args.output}")
        else:
            print(serialized)
    except (ValueError, RuntimeError, OSError, FileNotFoundError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
