"""Opt-in Chromium/Firefox contrast + keyboard smoke for docs-only CodeMirror.

Usage (locally installed Playwright browsers and pinned axe-core required):
  python tests/playground_contrast_browser.py --axe-file /tmp/axe-4.10.3.min.js
"""
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
THEMES = ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal")


def run(browser, engine, axe_file: Path):
    page = browser.new_page(viewport={"width": 390, "height": 800})
    try:
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((ROOT / "docs/playground.html").as_uri())
        page.locator("#playground-editor-mount .cm-editor").wait_for(state="visible")
        scroller = page.locator(".cm-scroller")
        assert scroller.get_attribute("role") == "region"
        assert scroller.get_attribute("aria-label") == "Scrollable HTML editor"
        assert scroller.evaluate("e => e.tabIndex === 0")
        scroller.focus()
        assert scroller.evaluate("e => document.activeElement === e")
        assert scroller.evaluate("e => getComputedStyle(e).outlineStyle !== 'none'")
        page.add_script_tag(path=str(axe_file))
        for theme in THEMES:
            page.locator("body").evaluate(
                "(e, name) => e.setAttribute('data-syn-theme', name)", theme)
            tokens = page.evaluate("""() => {
                const tag = [...document.querySelectorAll('.cm-activeLine span')]
                    .find(e => e.textContent === 'section');
                const s = document.createElement('span');
                s.style.color = 'var(--syn-text)';
                document.body.append(s);
                const result = {tag: getComputedStyle(tag).color,
                    token: getComputedStyle(s).color,
                    weight: getComputedStyle(tag).fontWeight};
                s.remove();
                return result;
            }""")
            assert tokens["tag"] == tokens["token"], (engine, theme, tokens)
            assert int(tokens["weight"]) >= 600, (engine, theme, tokens)
            audit = page.evaluate("""async () => axe.run(document, {
                runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}
            })""")
            violations = [(v["id"], [n["target"] for n in v["nodes"]])
                          for v in audit["violations"]]
            assert not violations, (engine, theme, violations)
        page.locator(".cm-content").fill('<div class="syn-panel">Updated</div>')
        assert page.locator("#playground-markup").input_value() == \
            '<div class="syn-panel">Updated</div>'
        assert not errors, (engine, errors)
    finally:
        page.close()
    context = browser.new_context(java_script_enabled=False)
    try:
        fallback = context.new_page()
        fallback.goto((ROOT / "docs/playground.html").as_uri())
        assert fallback.locator("#playground-markup").is_visible()
        assert not fallback.locator("#playground-editor-mount").is_visible()
    finally:
        context.close()
    print(engine, "PASS", len(THEMES), "themes + editor sync + no-JS fallback")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--axe-file", type=Path, required=True)
    args = parser.parse_args()
    assert args.axe_file.is_file(), args.axe_file
    with sync_playwright() as playwright:
        for engine in ("chromium", "firefox"):
            browser = getattr(playwright, engine).launch(headless=True)
            try:
                run(browser, engine, args.axe_file)
            finally:
                browser.close()


if __name__ == "__main__":
    main()
