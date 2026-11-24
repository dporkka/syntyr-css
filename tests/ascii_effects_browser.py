"""Computed-style checks for the ASCII effects gallery."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"], executable_path=os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE"))
    for width in (320, 390, 1280):
        page = browser.new_page(viewport={"width": width, "height": 800})
        page.goto((ROOT / "examples/ascii.html").as_uri())
        assert page.locator("main article").count() == 18
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        animation = page.locator(".syn-ascii--typewriter")
        mask = page.locator(".syn-ascii--gradient").first
        prop = lambda node, key: node.evaluate("(e,k) => getComputedStyle(e)[k]", key)
        assert prop(animation, "animationName") == "syn-ascii-reveal"
        assert prop(animation, "animationIterationCount") == "1"
        assert prop(mask, "maskImage") != "none"
        page.emulate_media(reduced_motion="reduce")
        assert prop(animation, "animationName") == "none"
        assert prop(mask, "maskImage") == "none"
        page.emulate_media(reduced_motion="no-preference", forced_colors="active")
        assert prop(animation, "animationName") == "none"
        assert prop(mask, "maskImage") == "none"
        page.emulate_media(forced_colors="none", media="print")
        assert prop(animation, "animationName") == "none"
        assert prop(mask, "maskImage") == "none"
        page.emulate_media(media="screen")
        page.evaluate("""() => {
            const outside = document.createElement('div');
            outside.className = 'syn-ascii--typewriter';
            outside.setAttribute('aria-hidden','true');
            document.body.classList.remove('syn-root');
            document.body.append(outside);
        }""")
        assert prop(page.locator("body > .syn-ascii--typewriter"), "animationName") == "none"
        page.close()
    browser.close()
print("PASS Chromium: 18 examples, 320/390/1280px reflow, finite motion, reduced motion, forced colors, print and scoping")
