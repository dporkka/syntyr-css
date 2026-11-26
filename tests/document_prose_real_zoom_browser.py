"""Opt-in Chromium tab-zoom regression; not manual accessibility certification.

Requires a full Chromium/Chrome for Testing binary with extension support and
developer-only Playwright. A fresh temporary profile and a local test-only
extension use the browser's actual tab zoom API (not CSS zoom or font scaling).
Neither the extension nor Playwright ships with Syntyr.
"""
import json
import os
from pathlib import Path
import tempfile

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PALETTES = ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal")


def main():
    with tempfile.TemporaryDirectory(prefix="syntyr-tab-zoom-") as tmp:
        work = Path(tmp)
        extension = work / "extension"
        extension.mkdir()
        (extension / "manifest.json").write_text(json.dumps({
            "manifest_version": 3,
            "name": "Syntyr local browser zoom regression",
            "version": "1.0",
            "permissions": ["tabs"],
            "background": {"service_worker": "worker.js"},
        }), encoding="utf-8")
        (extension / "worker.js").write_text(
            "chrome.runtime.onInstalled.addListener(() => {});\n", encoding="utf-8")
        opts = {"executable_path": os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE"]} if (
            "PLAYWRIGHT_CHROMIUM_EXECUTABLE" in os.environ) else {"channel": "chromium"}
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(work / "profile"), headless=True, no_viewport=True,
                args=["--headless=new", "--window-size=1280,900",
                      f"--disable-extensions-except={extension}",
                      f"--load-extension={extension}"],
                **opts,
            )
            try:
                worker = (context.service_workers[0] if context.service_workers else
                          context.wait_for_event("serviceworker", timeout=15000))
                page = context.pages[0]
                page.goto((ROOT / "examples/document-starter.html").as_uri())
                assert page.locator("script").count() == 0
                baseline = page.evaluate(
                    "() => ({width:innerWidth, dpr:devicePixelRatio,"
                    "font:getComputedStyle(document.documentElement).fontSize})")
                assert baseline["width"] >= 1280, baseline
                for factor in (2, 4):
                    actual = worker.evaluate("""async factor => {
                        const [tab] = await chrome.tabs.query({active:true,currentWindow:true});
                        await chrome.tabs.setZoom(tab.id, factor);
                        return await chrome.tabs.getZoom(tab.id);
                    }""", factor)
                    assert abs(actual - factor) < .01, (factor, actual)
                    # Verify real browser zoom affected the viewport and device
                    # pixel ratio, without author CSS changing root font size.
                    page.wait_for_function("""({base, factor}) =>
                        Math.abs(innerWidth - base.width/factor) <= 2 &&
                        Math.abs(devicePixelRatio - base.dpr*factor) < .02""",
                        arg={"base": baseline, "factor": factor}, timeout=5000)
                    assert page.evaluate("getComputedStyle(document.documentElement).fontSize") == baseline["font"]
                    for palette in PALETTES:
                        page.locator("main").evaluate("(e, p) => e.dataset.synTheme = p", palette)
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), (factor, palette)
                        assert page.locator("#prose img").evaluate(
                            "e => e.width <= e.parentElement.clientWidth + 1"), (factor, palette)
                        pre = page.get_by_role("region", name="Configuration code")
                        pre.focus()
                        assert pre.evaluate("e => document.activeElement === e")
                        assert pre.evaluate("e => e.scrollWidth > e.clientWidth")
                        pre.evaluate("e => e.scrollTo({left:0, behavior:'instant'})")
                        page.keyboard.press("ArrowRight")
                        try:
                            page.wait_for_function(
                                "document.querySelector('pre.chroma').scrollLeft > 0", timeout=3000)
                        except Exception as exc:
                            raise AssertionError((factor, palette, pre.evaluate(
                                """e => ({focused:document.activeElement===e, width:e.clientWidth,
                                scroll:e.scrollWidth, left:e.scrollLeft, rect:e.getBoundingClientRect().toJSON(),
                                viewport:[innerWidth,innerHeight], overflow:getComputedStyle(e).overflowX})"""))) from exc
                        inventory = page.get_by_role("region", name="Inventory")
                        inventory.focus()
                        assert inventory.evaluate("e => document.activeElement === e")
                        assert inventory.get_by_role("table").count() == 1
                    print(f"PASS Chromium actual {round(actual * 100)}% tab zoom: "
                          f"{page.evaluate('innerWidth')} CSS px; 7 palettes, "
                          "keyboard code scroll and named table region", flush=True)
            finally:
                context.close()


if __name__ == "__main__":
    main()
