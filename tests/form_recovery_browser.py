"""Developer-only native form reflow, readonly and error-recovery browser checks.

Run: python tests/form_recovery_browser.py [chromium firefox webkit]
Requires locally installed Playwright; not a consumer dependency.
"""
from pathlib import Path
import re
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEMO = (ROOT / "examples/form-composition.html").as_uri()


def rendered(page, selector, prop):
    return page.locator(selector).evaluate(
        "(node, prop) => getComputedStyle(node).getPropertyValue(prop).trim()", prop
    )


def verify(browser, engine):
    page = browser.new_page(viewport={"width": 320, "height": 850})
    page.goto(DEMO)
    field = page.locator("#workspace-id")
    assert field.get_attribute("readonly") is not None
    assert rendered(page, "#workspace-id", "border-top-style") == "dashed"
    assert rendered(page, "#workspace-id", "background-color") != rendered(
        page, "#workspace-name", "background-color"
    ), f"{engine}: readonly should be visibly distinct"
    field.focus()
    assert page.evaluate("document.activeElement.id") == "workspace-id"
    assert page.evaluate(
        "new FormData(document.querySelector('form.syn-form')).get('workspace_id')"
    ) == "WS-1042", "readonly form value must submit"
    assert page.get_by_label("Workspace ID (read only)").count() == 1

    for size in (16, 32, 48, 64):
        page.evaluate("(s) => document.documentElement.style.fontSize = s + 'px'", size)
        box = field.bounding_box()
        assert box and box["x"] >= -1 and box["x"] + box["width"] <= 321, (
            engine, size, "readonly field overflows", box
        )
    page.close()

    docs = (ROOT / "docs/component-recipes.md").read_text()
    section = docs.split("## 5. Server-rendered error recovery", 1)[1]
    markup = re.search(r"```html\n(.*?)\n```", section, re.S).group(1)
    css = (ROOT / "dist/syntyr.core.css").read_text()
    recipes = (ROOT / "dist/syntyr.recipes.css").read_text()
    semantic = (ROOT / "dist/syntyr.semantic.css").read_text()
    page = browser.new_page(viewport={"width": 390, "height": 850})
    page.set_content(f"<style>{css}\n{recipes}\n{semantic}</style>" + markup)
    field = page.locator("#account-email")
    assert field.get_attribute("aria-invalid") == "true"
    assert page.get_by_role("region", name="There is a problem").count() == 1
    page.get_by_role("link", name="Enter a valid email address").click()
    assert page.evaluate("document.activeElement.id") == "account-email"
    assert field.input_value() == "not-an-email"
    assert page.evaluate("new FormData(document.querySelector('form')).get('email')") == "not-an-email"
    # An invalid field must have the theme's danger border (not just ARIA).
    assert field.evaluate("""(node) => {
      const ghost = document.createElement('span');
      ghost.style.color = 'var(--syn-danger)';
      node.parentElement.append(ghost);
      const danger = getComputedStyle(ghost).color;
      ghost.remove();
      return getComputedStyle(node).borderTopColor === danger;
    }"""), f"{engine}: error border must use the danger token"
    # Distinct styles for classless semantic readonly fields.
    page.set_content(
        f"<style>{css}\n{semantic}</style>"
        '<div class="syn-root syn-semantic" data-syn-theme="noir">'
        '<label for="native-id">Reference ID</label>'
        '<input id="native-id" name="ref" value="ABC-42" readonly>'
        '<input id="native-edit" name="edit" value="ABC-42">'
        '</div>'
    )
    assert rendered(page, "#native-id", "border-top-style") == "dashed", (
        engine, "semantic readonly must be distinct"
    )
    assert rendered(page, "#native-edit", "border-top-style") == "solid"
    page.locator("#native-id").focus()
    assert page.evaluate("document.activeElement.id") == "native-id"
    page.close()

    # Simulated forced-colors preserves border visibility; this is NOT an
    # OS-native high-contrast or screen-reader conformance claim.
    page = browser.new_page(viewport={"width": 390, "height": 850})
    page.emulate_media(forced_colors="active")
    page.goto(DEMO)
    assert rendered(page, "#workspace-id", "border-top-style") == "dashed"
    assert rendered(page, "#workspace-id", "border-top-width") != "0px"
    page.close()
    print(f"PASS {engine}: readonly focus/FormData, 4x root text, errors and forced colors")


def main():
    engines = sys.argv[1:] or ["chromium", "firefox"]
    with sync_playwright() as p:
        for engine in engines:
            browser = getattr(p, engine).launch(headless=True)
            try:
                verify(browser, engine)
            finally:
                browser.close()


if __name__ == "__main__":
    main()
