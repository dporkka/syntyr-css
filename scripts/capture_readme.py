"""Refresh public README screenshots using optional developer-only Playwright."""
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Capture:
    filename: str
    source: str
    width: int = 1280
    height: int = 800
    full_page: bool = False


CAPTURES = (
    Capture("operations-console.png", "examples/operations-console.html"),
    Capture("flagship-studio.png", "examples/flagship-studio.html"),
    Capture("flagship-noir.png", "examples/flagship-noir.html"),
    Capture("components-desktop.png", "examples/common-ui.html"),
    Capture("components-mobile.png", "examples/common-ui.html", 390, 844),
    Capture("theme-gallery.png", "examples/themes.html", 1280, 800, True),
)


def main():
    # No browser automation dependency is imported by the CSS build or unit tests.
    from playwright.sync_api import sync_playwright

    output = ROOT / "assets/readme"
    output.mkdir(exist_ok=True)
    # Stage the complete set before replacing any committed image.
    with TemporaryDirectory(dir=output) as temp, sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for capture in CAPTURES:
                context = browser.new_context(
                    viewport={"width": capture.width, "height": capture.height},
                    device_scale_factor=1, reduced_motion="reduce",
                    color_scheme="light",
                )
                # The fixtures and CSS must work locally without external assets.
                context.route("**/*", lambda route: route.continue_()
                              if route.request.url.startswith("file:") else route.abort())
                page = context.new_page()
                page.goto((ROOT / capture.source).as_uri(), wait_until="load")
                page.locator("body").wait_for()
                page.evaluate("document.fonts.ready")
                page.screenshot(path=Path(temp) / capture.filename,
                                full_page=capture.full_page, animations="disabled")
                context.close()
                print(f"Captured {capture.filename} from {capture.source}")
        finally:
            browser.close()
        for capture in CAPTURES:
            (Path(temp) / capture.filename).replace(output / capture.filename)


if __name__ == "__main__":
    main()
