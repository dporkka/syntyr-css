"""Dev-only browser smoke tests for new forms and optional Radix style hooks.

Run with Playwright + all three browsers installed; not a consumer dependency.
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "examples/form-composition.html").as_uri()
ADAPTER = ROOT / "integrations/radix/states.css"


def run():
    with sync_playwright() as p:
        for name in ("chromium", "firefox", "webkit"):
            options = {}
            if name == "webkit" and os.environ.get("SYNTYR_WEBKIT_EXECUTABLE"):
                options["executable_path"] = os.environ["SYNTYR_WEBKIT_EXECUTABLE"]
            browser = getattr(p, name).launch(**options)
            for width in (320, 900):
                page = browser.new_page(viewport={"width": width, "height": 850})
                page.goto(URL)
                assert page.get_by_label("Account name").count() == 1, (name, width, "label")
                assert page.get_by_label("Monthly budget (USD)").count() == 1, (name, width, "unit")
                field = page.locator(".syn-field").first
                assert field.evaluate("(e) => getComputedStyle(e).display") == "grid", (name, width, "scoped field")
                page.locator("body").evaluate("(e) => e.classList.remove('syn-root')")
                assert field.evaluate("(e) => getComputedStyle(e).display") != "grid", (name, width, "unscoped CSS leaked")
                page.locator("body").evaluate("(e) => e.classList.add('syn-root')")
                row = page.locator(".syn-field-row").first
                columns = row.evaluate("(element) => getComputedStyle(element).gridTemplateColumns").split()
                assert len(columns) == (1 if width == 320 else 2), (name, width, columns)
                input_rect = page.locator("#budget").bounding_box()
                assert input_rect and input_rect["x"] >= -1 and input_rect["x"] + input_rect["width"] <= width + 1, (name, width, input_rect)
                if width == 320:
                    search = page.locator("#search-q")
                    submit = page.get_by_role("button", name="Search")
                    ordinary_field = search.bounding_box()
                    ordinary_button = submit.bounding_box()
                    assert ordinary_button["x"] >= ordinary_field["x"] + ordinary_field["width"] - 2, (
                        name, "ordinary connected controls should stay inline")
                    for font_size in (32, 48, 64):
                        page.evaluate("(size) => document.documentElement.style.fontSize = size + 'px'", font_size)
                        field_box = search.bounding_box()
                        button_box = submit.bounding_box()
                        group_box = page.locator(".syn-input-group").first.bounding_box()
                        assert field_box["width"] >= group_box["width"] - 2, (
                            name, font_size, "enlarged search field should use full row", field_box, group_box)
                        assert button_box["y"] >= field_box["y"] + field_box["height"] - 2, (
                            name, font_size, "submit should stack below search field")
                        assert field_box["height"] < 4 * font_size, (
                            name, font_size, "search field text wraps into excessively tall control", field_box)
                        assert button_box["x"] + button_box["width"] <= width + 1, (
                            name, font_size, "submit overflows viewport", button_box)
                    page.evaluate("document.documentElement.style.fontSize = ''")
                    # A translated action must not consume the searchbox or clip
                    # the page. The native input/addon recipe remains unchanged.
                    long_submit = page.locator(".syn-input-group > .syn-button").first
                    long_submit.evaluate(
                        "(el) => { el.textContent = 'Rechercher parmi tous les éléments actuellement disponibles dans notre compte'; }"
                    )
                    field_box = search.bounding_box()
                    button_box = long_submit.bounding_box()
                    assert field_box["width"] >= 9 * 16, (name, "long label compressed search input")
                    assert button_box["y"] >= field_box["y"] + field_box["height"] - 2, (
                        name, "long translated action must wrap below search")
                    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), (
                        name, "translated action overflows page")
                    page.locator("body").evaluate("(el) => { el.dir = 'rtl'; }")
                    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), (
                        name, "RTL translated action overflows page")
                    page.locator("body").evaluate("(el) => { el.removeAttribute('dir'); }")
                if width == 900:
                    page.get_by_label("Account name").fill("Syntyr")
                    page.get_by_role("button", name="Search").click()
                    assert "q=Syntyr" in page.url, (name, page.url)
                    page.add_style_tag(path=str(ADAPTER))
                    page.evaluate("""() => {
                      const button = document.createElement("button");
                      button.id = "radix-toggle"; button.className = "syn-button";
                      button.setAttribute("data-state", "on");
                      button.textContent = "Pin";
                      document.body.append(button);
                    }""")
                    def bg():
                        return page.locator("#radix-toggle").evaluate("(e) => getComputedStyle(e).backgroundColor")
                    baseline = bg()
                    page.evaluate('document.body.classList.add("syn-radix")')
                    page.wait_for_function(
                        "(baseline) => getComputedStyle(document.querySelector('#radix-toggle')).backgroundColor !== baseline",
                        arg=baseline,
                    )
                    assert bg() != baseline, (name, "root adapter failed")
                    page.evaluate('document.body.classList.remove("syn-radix"); document.querySelector("#radix-toggle").remove(); document.body.insertAdjacentHTML("beforeend", \'<div class="syn-radix"><button id="radix-toggle" class="syn-button" data-state="on">Pin</button></div>\')')
                    page.wait_for_function(
                        "(baseline) => getComputedStyle(document.querySelector('#radix-toggle')).backgroundColor !== baseline",
                        arg=baseline,
                    )
                    assert bg() != baseline, (name, "nested adapter failed")
                    page.evaluate("""() => {
                        document.querySelector('.syn-radix').classList.remove('syn-radix');
                    }""")
                    page.wait_for_function(
                        "(baseline) => getComputedStyle(document.querySelector('#radix-toggle')).backgroundColor === baseline",
                        arg=baseline,
                    )
                    page.evaluate("document.querySelector('#radix-toggle').classList.add('syn-radix')")
                    page.wait_for_function(
                        "(baseline) => getComputedStyle(document.querySelector('#radix-toggle')).backgroundColor !== baseline",
                        arg=baseline,
                        timeout=1500,
                    )
                    assert bg() != baseline, (name, "same-element adapter failed")
                page.close()
            browser.close()
            print("PASS", name, "form layout 320/900, native form GET, root/nested/same-element Radix states")


if __name__ == "__main__":
    run()
