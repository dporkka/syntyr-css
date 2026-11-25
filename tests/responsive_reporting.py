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
