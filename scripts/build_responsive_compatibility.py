"""Publish a compact, historical responsive evidence report; never raw logs."""
import argparse
from collections import defaultdict
from datetime import date
import hashlib
from html import escape
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
ENGINES = ("chromium", "firefox", "webkit")
STATUSES = ("pass", "fail", "blocked")


def build_report(cases, revision, tested_on):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("An exact tested Git revision is required")
    date.fromisoformat(tested_on)
    seen = set()
    pages = set()
    groups = defaultdict(dict)
    for case in cases:
        engine, page, status = (case[k] for k in ("engine", "page", "status"))
        w, h, scale = (case[k] for k in ("width", "height", "textScale"))
        if (engine not in ENGINES or status not in STATUSES or not isinstance(page, str)
                or not re.fullmatch(r"[A-Za-z0-9_./-]+\.html", page)
                or PurePosixPath(page).is_absolute() or ".." in PurePosixPath(page).parts
                or type(w) is not int or type(h) is not int or min(w,h) <= 0
                or scale not in (1, 1.5, 2)):
            raise ValueError("Invalid test case")
        key = (engine, page, w, h, scale)
        if key in seen:
            raise ValueError("Duplicate test case")
        seen.add(key)
        pages.add(page)
        groups[(w,h,scale)][(engine,page)] = status
    if not pages:
        raise ValueError("Empty evidence")
    matrix = []
    for (w,h,scale), results in sorted(groups.items()):
        engines = {}
        for engine in ENGINES:
            counts = {s: sum(results.get((engine,p)) == s for p in pages) for s in STATUSES}
            missing = len(pages) - sum(counts.values())
            if counts["fail"]:
                status = "fail"
            elif counts["blocked"]:
                status = "blocked"
            elif missing == len(pages):
                status = "not-tested"
            elif missing:
                status = "partial"
            else:
                status = "pass"
            engines[engine] = {"status": status, **counts, "notTested": missing}
        matrix.append({"width":w,"height":h,"textScale":scale,"engines":engines})
    return {"schemaVersion":1,"suite":"published-page-reflow","testedRevision":revision,
            "testedOn":tested_on,"scope":"unreleased source candidate; historical evidence, not release certification",
            "pageCount":len(pages),"pages":sorted(pages),"matrix":matrix}


def render_html(report):
    rows = []
    for row in report["matrix"]:
        cells = []
        for engine in ENGINES:
            result = row["engines"][engine]
            label = result["status"].replace("-", " ").capitalize()
            counts = f'{result["pass"]}/{report["pageCount"]} passed'
            cells.append(f"<td><strong>{label}</strong><br>{counts}</td>")
        rows.append(f'<tr><th scope="row">{row["width"]} × {row["height"]} · {row["textScale"]*100:g}%</th>{"".join(cells)}</tr>')
    revision = escape(report["testedRevision"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Historical Syntyr responsive browser test evidence by viewport and engine.">
<title>Responsive compatibility — Syntyr CSS</title>
<link rel="stylesheet" href="../dist/syntyr.core.css">
<link rel="stylesheet" href="docs.css">
</head>
<body class="syn-root syn-page" data-syn-theme="studio">
<a class="syn-button docs-skip" href="#main">Skip to results</a>
<main class="syn-shell" id="main">
<header class="syn-header"><a class="syn-logo" href="index.html">SYNTYR / CSS</a><a href="accessibility.html">Accessibility methodology</a></header>
<h1 class="syn-title">Responsive compatibility</h1>
<p class="syn-lede">Measured browser layout evidence, not a blanket compatibility promise.</p>
<section class="syn-panel" aria-labelledby="evidence">
<h2 id="evidence">Tested source candidate</h2>
<p>Tested {escape(report["testedOn"])} · {report["pageCount"]} published HTML pages.</p>
<p>Revision <a href="https://github.com/dporkka/syntyr-css/commit/{revision}"><code style="overflow-wrap:anywhere">{revision[:12]}</code></a>. This is historical evidence for that source revision, not the immutable published release or the current deployment.</p>
<p><a href="../metadata/responsive-compatibility.v1.json">Download machine-readable evidence (JSON)</a></p>
<div style="overflow-x:auto;max-inline-size:100%" tabindex="0" role="region" aria-label="Responsive results table">
<table class="syn-table"><caption>Published-page reflow by viewport and engine</caption><thead><tr><th scope="col">CSS pixels / root text</th><th scope="col">Chromium</th><th scope="col">Firefox</th><th scope="col">WebKit</th></tr></thead><tbody>
{"".join(rows)}
</tbody></table>
</div>
<p>Not tested means no case was recorded. Partial means coverage is incomplete. Blocked means execution was prevented. Failure means at least one case failed.</p>
</section>
<section class="syn-panel"><h2>What this measures</h2><p>Page overflow, clipped controls, stylesheet loading and selected mobile touch-target geometry. This is not a WCAG certification, native device test, visual approval, or proof of every component behavior. Browser versions were not recorded in this historical report.</p></section>
</main></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True,
                        help="Repeat for disjoint runs of the same exact revision")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--tested-on", required=True)
    args = parser.parse_args()
    cases = []
    input_hashes = []
    for path in args.input:
        raw = path.read_bytes()
        data = json.loads(raw)
        if data.get("schemaVersion") != 1:
            raise ValueError("Unsupported raw report schema")
        actual = {status: sum(c["status"] == status for c in data["cases"])
                  for status in STATUSES}
        if data.get("summary") != actual:
            raise ValueError("Raw report summary does not match cases")
        cases.extend(data["cases"])
        input_hashes.append(hashlib.sha256(raw).hexdigest())
    report = build_report(cases, args.revision, args.tested_on)
    report["sourceReportSha256"] = sorted(input_hashes)
    (ROOT / "metadata/responsive-compatibility.v1.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    (ROOT / "docs/responsive-compatibility.html").write_text(render_html(report))


if __name__ == "__main__":
    main()
