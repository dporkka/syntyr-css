"""Dev-only Chromium/Firefox proof: score shown, not populated, placeholders.

Run with Python Playwright installed:
  python tests/visible_placeholder_browser.py
"""
import importlib.util
from pathlib import Path

from playwright.sync_api import sync_playwright

SCRIPT = Path(__file__).with_name("contrast_pixel_triage.py")
spec = importlib.util.spec_from_file_location("contrast_pixel_triage", SCRIPT)
triage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triage)

HTML = """<!doctype html><html><head><style>
input,textarea {display:block;font:16px sans-serif;padding:.6rem;margin:.5rem;
  background-color:#fff;color:#222;border:1px solid #888}
input::placeholder,textarea::placeholder{color:rgb(77,96,121);opacity:1}
#weak::placeholder{color:rgb(245,245,245)}
#gradient{background-image:linear-gradient(white,gray)}
#opaque{opacity:.5}
#hidden{display:none}
</style></head><body>
<input id="empty" placeholder="Search records">
<input id="filled" placeholder="Search records" value="Existing">
<textarea id="notes" placeholder="Write notes"></textarea>
<input id="weak" placeholder="Low contrast">
<input id="gradient" placeholder="Pattern">
<input id="opaque" placeholder="Transparent">
<input id="hidden" placeholder="Hidden">
</body></html>"""

EXPECTED = {
    "empty": "computed_placeholder_above_threshold",
    "filled": "unsampled",
    "notes": "computed_placeholder_above_threshold",
    "weak": "computed_placeholder_below_threshold",
    "gradient": "unsampled",
    "opaque": "unsampled",
    "hidden": "unsampled",
}


def main():
    with sync_playwright() as playwright:
        for engine in ("chromium", "firefox"):
            browser = getattr(playwright, engine).launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 320, "height": 720})
                page.set_content(HTML)
                items = [{"selector": [f"#{name}"], "failure_summary": "contrast",
                          "page": "fixture.html"} for name in EXPECTED]
                measured = page.evaluate(triage.MEASURE_JS, items)
                for item in measured:
                    item["viewport_width"] = 320
                    name = item["selector"][0].removeprefix("#")
                    outcome = triage.score_item(item, object())
                    assert outcome["status"] == EXPECTED[name], (
                        engine, name, outcome, item.get("placeholder"))
                    if name == "filled":
                        assert item.get("placeholder") is None, (
                            engine, "populated input must not produce placeholder evidence")
                    if outcome["status"].startswith("computed_placeholder_"):
                        assert "minimum_sampled_ratio" not in outcome
                print(engine, "PASS", len(EXPECTED), "actual DOM placeholder cases")
                page.close()
            finally:
                browser.close()


if __name__ == "__main__":
    main()
