"""Optional local-only responsive audit. Playwright is a developer dependency."""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from responsive_reporting import record_case, summarize, block_remaining
from responsive_viewports import CANONICAL_VIEWPORTS, PUBLISHED_VIEWPORTS

ENGINES = ("chromium", "firefox", "webkit")


def local_target(url):
    parts = urlsplit(url)
    if (parts.scheme != "http" or parts.hostname not in ("127.0.0.1", "::1", "localhost")
            or parts.username is not None or parts.password is not None or parts.fragment
            or not parts.port):
        raise ValueError("Specify an explicit HTTP loopback URL and port; no credentials or fragments")
    # Match the browser's canonical origin, including the default port.
    host = "[::1]" if parts.hostname == "::1" else parts.hostname
    origin = f"http://{host}" + (f":{parts.port}" if parts.port != 80 else "")
    return origin, (parts.path or "/") + (f"?{parts.query}" if parts.query else "")


def make_report(cases):
    return {"schemaVersion": 1, "suite": "local-responsive-reflow",
            "summary": summarize(cases), "cases": cases,
            "limitations": "Geometry checks only on trusted local development pages; request filtering is best effort, not a security sandbox. No native zoom or WCAG certification."}


def audit(url, engines, stress):
    from playwright.sync_api import sync_playwright
    from published_reflow_browser import check_geometry
    origin, path = local_target(url)
    viewports = PUBLISHED_VIEWPORTS if stress else tuple((w,h,1) for _,w,h in CANONICAL_VIEWPORTS)
    results = []
    with sync_playwright() as pw:
        for engine in dict.fromkeys(engines):
            browser = None
            try:
                browser = getattr(pw, engine).launch(headless=True)
                for w,h,scale in viewports:
                    context = browser.new_context(viewport={"width":w,"height":h}, reduced_motion="reduce", service_workers="block")
                    try:
                        # Restrict ordinary resource requests; not an isolation boundary.
                        def route_request(route):
                            u = urlsplit(route.request.url)
                            if f"{u.scheme}://{u.netloc}" == origin and route.request.method in ("GET","HEAD"):
                                route.continue_()
                            else:
                                route.abort()
                        context.route("**/*", route_request)
                        context.route_web_socket("**/*", lambda ws: ws.close())
                        page = context.new_page()
                        def probe():
                            response = page.goto(origin + path, wait_until="load", timeout=15000)
                            assert response and response.ok, "Navigation failed"
                            assert urlsplit(page.url).netloc == urlsplit(origin).netloc, "Unexpected navigation"
                            check_geometry(page, engine, path, w,h,scale)
                        record_case(results, engine, path, (w,h,scale), probe)
                    finally:
                        context.close()
            except Exception as exc:
                block_remaining(results, engine, [path], viewports, exc)
            finally:
                if browser:
                    browser.close()
    return make_report(results)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--browsers", nargs="+", choices=ENGINES, default=["chromium"])
    parser.add_argument("--stress", action="store_true", help="Include landscape and enlarged root text")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        local_target(args.url)
        report = audit(args.url, args.browsers, args.stress)
    except (ValueError, ImportError) as exc:
        parser.error(str(exc))
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return int(bool(report["summary"]["fail"] or report["summary"]["blocked"]))


if __name__ == "__main__":
    raise SystemExit(main())
