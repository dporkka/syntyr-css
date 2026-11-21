"""Optional Chromium smoke checks for CSS and WAAPI website animation presets.

Run: PYTHONPATH=/path/to/playwright python3 tests/website_animation_browser.py
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def check(condition, explanation):
    if not condition:
        raise AssertionError(explanation)


def main():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT))
    )
    Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/examples/animation.html"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(url)
                page.locator("#website-animation-controls").wait_for(state="visible")
                check(page.locator('[data-syn-animate]').count() == 15,
                      "All 15 CSS effects should be demonstrated")
                for name in ("fade-in", "fade-out", "slide-up", "slide-down",
                             "slide-left", "slide-right", "zoom-in", "zoom-out",
                             "pop", "bounce", "pulse", "shake", "rotate-in", "flip-in", "rotate"):
                    animation = page.locator(f'[data-syn-animate="{name}"]')
                    active_name = animation.evaluate(
                        "node => getComputedStyle(node).animationName"
                    )
                    check(active_name == f"syn-animate-{name}",
                          f"{name} not activated: {active_name}")
                # Unknown child presets must not inherit a parent's animation.
                inherited = page.evaluate("""() => {
                    const parent = document.createElement('div');
                    parent.dataset.synAnimate = 'bounce';
                    const child = document.createElement('span');
                    child.dataset.synAnimate = 'not-a-preset';
                    parent.append(child);
                    document.body.append(parent);
                    const names = [getComputedStyle(parent).animationName,
                                   getComputedStyle(child).animationName];
                    parent.remove();
                    return names;
                }""")
                check(inherited == ["syn-animate-bounce", "none"],
                      f"Unknown presets must fail closed: {inherited}")
                rotate = page.locator('[data-syn-animate="rotate"]')
                check(rotate.evaluate(
                    "node => getComputedStyle(node).animationDuration"
                ) == "0.6s", "CSS 2× speed should halve a 1200ms rotation to 600ms")
                rotation_frames = rotate.evaluate(
                    "node => node.getAnimations()[0]?.effect.getKeyframes().map(f => f.rotate)"
                )
                check(rotation_frames == ["0deg", "-360deg"],
                      f"CSS rotation should support counterclockwise motion: {rotation_frames}")
                pulse = page.locator('[data-syn-animate="pulse"]')
                bounce = page.locator('[data-syn-animate="bounce"]')
                check(pulse.evaluate(
                    "node => getComputedStyle(node).animationIterationCount"
                ) == "infinite", "CSS infinite loop modifier should work")
                check(bounce.evaluate(
                    "node => getComputedStyle(node).animationIterationCount"
                ) == "3", "CSS finite iteration count should work")
                pulse.evaluate(
                    "node => node.style.setProperty('--syn-animation-play-state','paused')"
                )
                check(pulse.evaluate(
                    "node => getComputedStyle(node).animationPlayState"
                ) == "paused", "CSS playback pause token should work")
                check(page.evaluate(
                    "() => document.documentElement.scrollWidth <= innerWidth + 1"
                ), "Mobile demo should not overflow")

                page.locator("#website-animation-preset").select_option("slide-left")
                page.locator("#website-animation-repeat").select_option("3")
                page.locator("#website-animation-direction").select_option("alternate")
                page.locator("#website-animation-play").click()
                target = page.locator("#website-animation-target")
                timing = target.evaluate("""node => {
                  const a = node.getAnimations()[0];
                  return a && {
                    iterations: a.effect.getTiming().iterations,
                    direction: a.effect.getTiming().direction,
                    translate: a.effect.getKeyframes()[0].translate,
                  };
                }""")
                check(timing and timing["iterations"] == 3 and
                      timing["direction"] == "alternate" and
                      timing["translate"].startswith("0.75rem"),
                      f"WAAPI cycle controls are incorrect: {timing}")
                page.locator("#website-animation-pause").click()
                check(target.evaluate(
                    "node => node.getAnimations()[0]?.playState"
                ) == "paused", "Native pause should work")
                page.locator("#website-animation-resume").click()
                check(target.evaluate(
                    "node => node.getAnimations()[0]?.playState"
                ) == "running", "Native resume should work")
                page.locator("#website-animation-preset").select_option("pulse")
                page.locator("#website-animation-repeat").select_option("infinite")
                page.locator("#website-animation-play").click()
                check(target.evaluate(
                    "node => node.getAnimations()[0]?.effect.getTiming().iterations"
                ) == float("inf"), "Native infinite loop should work")
                page.locator("#website-animation-preset").select_option("rotate")
                page.locator("#website-animation-rotation").select_option("-360")
                page.locator("#website-animation-repeat").select_option("infinite")
                speed_control = page.locator("#website-animation-speed")
                speed_control.evaluate("""node => {
                    node.value = "2";
                    node.dispatchEvent(new Event("input", { bubbles: true }));
                }""")
                page.locator("#website-animation-play").click()
                rotation_info = target.evaluate("""node => {
                    const animation = node.getAnimations()[0];
                    return {
                        speed: animation?.playbackRate,
                        rotations: animation?.effect.getKeyframes().map(frame => frame.rotate),
                        iterations: animation?.effect.getTiming().iterations,
                    };
                }""")
                check(rotation_info["speed"] == 2 and
                      rotation_info["rotations"] == ["0deg", "-360deg"] and
                      rotation_info["iterations"] == float("inf"),
                      f"JS rotation, direction, speed, looping failed: {rotation_info}")
                speed_control.evaluate("""node => {
                    node.value = "0.5";
                    node.dispatchEvent(new Event("input", { bubbles: true }));
                }""")
                check(target.evaluate(
                    "node => node.getAnimations()[0]?.playbackRate"
                ) == 0.5, "Speed slider should adjust live playback rate")
                check(page.locator("#website-animation-speed-value").inner_text() == "0.5×",
                      "Speed output should remain synchronized")
                page.locator("#website-animation-stop").click()
                check(target.evaluate("node => node.getAnimations().length") == 0,
                      "Cancel must restore ordinary CSS")
                check(not errors, f"Browser errors: {errors}")
                page.close()

                reduced = browser.new_page(
                    reduced_motion="reduce", viewport={"width": 320, "height": 700}
                )
                reduced.goto(url)
                reduced.locator("#website-animation-controls").wait_for(state="visible")
                check(all(
                    name == "none" for name in reduced.locator(
                        '[data-syn-animate]'
                    ).evaluate_all(
                        "els => els.map(el => getComputedStyle(el).animationName)"
                    )
                ), "Reduced motion must disable every CSS animation, including loops")
                reduced.locator("#website-animation-repeat").select_option("infinite")
                reduced.locator("#website-animation-play").click()
                check(reduced.locator("#website-animation-target").evaluate(
                    "node => node.getAnimations().length"
                ) == 0, "Reduced motion must suppress JS loops")
                check(reduced.locator("#website-animation-target").is_visible(),
                      "Reduced-motion fallback must preserve content")
                reduced.close()

                no_js = browser.new_page(
                    java_script_enabled=False, reduced_motion="reduce",
                    viewport={"width": 320, "height": 700}
                )
                no_js.goto(url)
                check(no_js.locator("#website-animation-controls").is_hidden(),
                      "Nonfunctional JS controls must be hidden without JS")
                check(no_js.locator("#website-animation-target").is_visible(),
                      "No-JS fallback must preserve content")
                no_js.close()
                print("PASS: 15 CSS presets, rotation, speed, loops, native pause/resume, reduced motion and no-JS")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
