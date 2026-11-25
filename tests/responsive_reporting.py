"""Dependency-free reporting shared by responsive browser checks."""


def record_case(results, engine, page, viewport, run):
    width, height, scale = viewport
    case = {"engine": engine, "page": page, "width": width,
            "height": height, "textScale": scale, "status": "pass"}
    try:
        run()
    except Exception as exc:
        case.update(status="fail", error=str(exc) or type(exc).__name__)
    results.append(case)
    return case


def summarize(results):
    return {status: sum(case["status"] == status for case in results)
            for status in ("pass", "fail", "blocked")}


def block_remaining(results, engine, pages, viewports, exc):
    """Preserve already executed cases; record every unexecuted case once."""
    completed = {(c["page"], c["width"], c["height"], c["textScale"])
                 for c in results if c["engine"] == engine}
    for width, height, scale in viewports:
        for page in pages:
            if (page, width, height, scale) not in completed:
                results.append({"engine": engine, "page": page, "width": width,
                                "height": height, "textScale": scale,
                                "status": "blocked", "error": str(exc) or type(exc).__name__})
