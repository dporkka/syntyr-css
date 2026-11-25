"""Native HTML styling must be semantic, opt-in, accessible and dependency-free."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeSemanticPrimitives(unittest.TestCase):
    def test_all_additional_html_elements_supported_only_in_semantic_mode(self):
        source = (ROOT / "src/semantic.css").read_text()
        for element in ("search", "output", "meter", "kbd", "mark", "figure", "figcaption", "pre"):
            with self.subTest(element=element):
                self.assertIn(f"{element}:not([class])", source)
                self.assertIn(f"{element}[data-syn-semantic]", source)
        self.assertIn(":is(.syn-root.syn-semantic, .syn-root .syn-semantic)", source)
        for element in ("mark:not([class])", "meter:not([class])", "figure:not([class])"):
            self.assertNotIn(element, (ROOT / "dist/syntyr.core.css").read_text())

    def test_mark_colors_use_accessible_theme_pair_and_high_contrast_fallback(self):
        css = (ROOT / "src/semantic.css").read_text()
        self.assertIn("background: var(--syn-accent)", css)
        self.assertIn("color: var(--syn-on-accent)", css)
        forced = css.split("@media (forced-colors: active)")[-1]
        self.assertIn("HighlightText", forced)
        self.assertIn("Highlight", forced)

    def test_noninteractive_semantics_remain_native_and_responsive(self):
        css = (ROOT / "src/semantic.css").read_text()
        self.assertIn("overflow-x: auto", css)
        self.assertIn("max-inline-size: 100%", css)
        self.assertIn("min-inline-size: 0", css)
        self.assertIn("accent-color: var(--syn-accent)", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)

    def test_semantic_preview_contains_accessible_html_without_runtime_js(self):
        html = (ROOT / "examples/native-elements.html").read_text()
        for fragment in ('syn-root syn-page syn-semantic', 'syntyr.semantic.css',
                         '<search', 'aria-label="Search examples"', '<figure',
                         '<figcaption', '<mark', '<kbd', '<meter', '<output', '<pre',
                         'type="submit"', 'method="get"', 'for="native-q"'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, html)
        self.assertNotIn("<script", html.lower())
        self.assertIn("static example", html.lower())

    def test_native_suggestions_and_grouped_disclosures_are_accessible(self):
        html = (ROOT / "examples/native-elements.html").read_text()
        from html.parser import HTMLParser

        class Inputs(HTMLParser):
            def __init__(self):
                super().__init__()
                self.by_id = {}
                self.selects = {}
                self.labels = {}
                self.active_label = None
                self.details_names = []
                self.template_depth = 0
                self.active_select = None
                self.active_group = None
                self.service_groups = []

            def handle_starttag(self, tag, attrs):
                if tag == "template":
                    self.template_depth += 1
                    return
                if self.template_depth:
                    return
                attributes = dict(attrs)
                if tag == "input" and attributes.get("id"):
                    self.by_id[attributes["id"]] = attributes
                elif tag == "select":
                    self.active_select = attributes.get("id")
                    if self.active_select:
                        self.selects[self.active_select] = attributes
                elif tag == "optgroup" and self.active_select == "native-service":
                    self.active_group = {
                        "label": attributes.get("label", "").strip(),
                        "option_count": 0,
                    }
                    self.service_groups.append(self.active_group)
                elif tag == "option" and self.active_group is not None:
                    self.active_group["option_count"] += 1
                elif tag == "label":
                    self.active_label = attributes.get("for")
                    if self.active_label:
                        self.labels[self.active_label] = ""
                elif tag == "details":
                    self.details_names.append(attributes.get("name"))

            def handle_data(self, data):
                if not self.template_depth and self.active_label:
                    self.labels[self.active_label] += data

            def handle_endtag(self, tag):
                if tag == "template":
                    self.template_depth -= 1
                    return
                if self.template_depth:
                    return
                if tag == "label":
                    self.active_label = None
                elif tag == "optgroup":
                    self.active_group = None
                elif tag == "select":
                    self.active_select = None
                    self.active_group = None

        parsed = Inputs()
        parsed.feed(html)
        self.assertEqual(parsed.by_id["native-location"].get("list"), "native-location-list")
        self.assertIn('<datalist id="native-location-list">', html)
        grouped_options = [group for group in parsed.service_groups
                           if group["label"] and group["option_count"] > 0]
        self.assertGreaterEqual(len(grouped_options), 2,
                                "Service select must contain two labeled, populated groups")
        self.assertIn("native-service", parsed.selects,
                      "Service select must exist with the expected ID")
        self.assertTrue(parsed.labels.get("native-service", "").strip(),
                        "Service select needs a visible associated label")
        self.assertEqual(parsed.details_names.count("native-review-sections"), 2)
        self.assertIn('older browsers may leave both open', html)
        self.assertNotIn('<script', html.lower())
        index = (ROOT / "llms.txt").read_text()
        self.assertIn('datalist/optgroup and named disclosure', index)

    def test_native_form_reflow_uses_capped_controls_and_scroll_region(self):
        html = (ROOT / "examples/native-elements.html").read_text()
        css = (ROOT / "src/semantic.css").read_text()
        from html.parser import HTMLParser

        class TableRegion(HTMLParser):
            def __init__(self):
                super().__init__()
                self.div_depth = 0
                self.regions = []
                self.open_regions = []

            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == "div":
                    self.div_depth += 1
                    if "syn-table-wrap" in attributes.get("class", "").split():
                        region = {"depth": self.div_depth, "attrs": attributes,
                                  "contains_table": False}
                        self.regions.append(region)
                        self.open_regions.append(region)
                elif tag == "table" and self.open_regions:
                    self.open_regions[-1]["contains_table"] = True

            def handle_endtag(self, tag):
                if tag == "div":
                    if (self.open_regions and
                            self.open_regions[-1]["depth"] == self.div_depth):
                        self.open_regions.pop()
                    self.div_depth -= 1

        region = TableRegion()
        region.feed(html)
        valid = [entry for entry in region.regions
                 if entry["contains_table"]
                 and entry["attrs"].get("role") == "region"
                 and entry["attrs"].get("aria-label") == "Sample campaign inventory"
                 and entry["attrs"].get("tabindex") == "0"]
        self.assertEqual(len(valid), 1,
                         "The same named, tabbable wrapper must contain the table")

        def declarations_for(unclassed, opted_in):
            # Require the complete opt-in ancestor before parsing declarations.
            import re
            prefix = ":is(.syn-root.syn-semantic, .syn-root .syn-semantic) :where(:is("
            start = css.index(prefix + unclassed)
            opening = css.index("{", start)
            self.assertIn(opted_in, css[start:opening],
                          "The rule must retain the explicit semantic opt-in alternative")
            block = css[opening + 1:css.index("}", opening)]
            return {match.group(1): match.group(2).strip()
                    for match in re.finditer(r"(?<![\w-])([\w-]+)\s*:\s*([^;{}]+);", block)}

        fieldset = declarations_for("fieldset:not([class])", "fieldset[data-syn-semantic]")
        color = declarations_for('input[type="color"]:not([class])',
                                 'input[type="color"][data-syn-semantic]')
        file = declarations_for('input[type="file"]:not([class])',
                                'input[type="file"][data-syn-semantic]')
        self.assertEqual(fieldset.get("padding"), "1rem")
        self.assertEqual(color.get("inline-size"), "min(4rem, 100%)")
        self.assertEqual(color.get("min-inline-size"), "0")
        self.assertEqual(color.get("max-inline-size"), "100%")
        self.assertEqual(file.get("inline-size"), "100%")
        self.assertEqual(file.get("min-inline-size"), "0")
        self.assertEqual(file.get("max-inline-size"), "100%")
        self.assertEqual(file.get("overflow"), "clip")
        media = css.split("@media (max-width: 40rem)", 1)[1].split(
            "@media (forced-colors: active)", 1)[0]
        self.assertIn(":is(.syn-root.syn-semantic, .syn-root .syn-semantic)", media)
        self.assertIn(":is(fieldset:not([class]), fieldset[data-syn-semantic])", media)
        self.assertIn("padding: min(1rem, 5vw)", media)

    def test_demo_is_discoverable_and_published_explicitly(self):
        self.assertIn('href="../examples/native-elements.html"', (ROOT / "docs/index.html").read_text())
        self.assertIn('"native-elements.html"', (ROOT / "scripts/build_cloudflare_site.py").read_text())
        self.assertIn("native-elements.html", (ROOT / "docs/components.md").read_text())
        self.assertIn("native-elements.html", (ROOT / "docs/progressive-enhancement.md").read_text())
        self.assertIn("native_semantic_browser.py", (ROOT / "docs/accessibility.md").read_text())

    def test_source_css_rebuilt_in_semantic_distribution(self):
        css = (ROOT / "src/semantic.css").read_text().strip()
        self.assertEqual(css, (ROOT / "dist/syntyr.semantic.css").read_text().strip())
        self.assertIn(css, (ROOT / "dist/syntyr.all.css").read_text())


    def test_keyboard_scrollable_code_example_is_focusable(self):
        import re
        html = (ROOT / "examples/native-elements.html").read_text()
        open_tag = re.search(r"<pre\b[^>]*>", html)
        self.assertIsNotNone(open_tag)
        self.assertIn('tabindex="0"', open_tag.group())
        self.assertIn('aria-label="SQL query example"', open_tag.group())

    def test_long_kbd_chords_wrap_at_large_text_sizes(self):
        css = (ROOT / "src/semantic.css").read_text()
        block = css[css.index("kbd:not([class])") : css.index("mark:not([class])")]
        self.assertIn("max-inline-size: 100%", block)
        self.assertIn("white-space: normal", block)
        self.assertIn("overflow-wrap: anywhere", block)
        self.assertNotIn("white-space: nowrap", block)

    def test_nested_code_preserves_mark_text_contrast(self):
        css = (ROOT / "src/semantic.css").read_text()
        mark = css[css.index("mark:not([class])"):]
        self.assertIn("code:not([class])", mark)
        self.assertIn("color: inherit", mark)
        self.assertIn("<mark><code>status</code></mark>", (ROOT / "examples/native-elements.html").read_text())

    def test_browser_regression_requires_scrollable_focus_and_nested_contrast(self):
        browser = (ROOT / "tests/native_semantic_browser.py").read_text()
        self.assertIn("scrollWidth > e.clientWidth", browser)
        self.assertIn("getComputedStyle(e).overflowX", browser)
        self.assertIn("scrollLeft", browser)
        self.assertIn("mark code", browser)


    def test_native_file_and_color_controls_bound_width_at_large_text_sizes(self):
        css = (ROOT / "src/semantic.css").read_text()
        file_section = css.split('input[type="file"]:not([class])', 1)[1].split("}", 1)[0]
        for declaration in ("inline-size: 100%", "min-inline-size: 0",
                            "max-inline-size: 100%", "overflow: clip"):
            with self.subTest(declaration=declaration):
                self.assertIn(declaration, file_section)
        color_section = css.split('input[type="color"]:not([class])', 1)[1].split("}", 1)[0]
        for declaration in ("inline-size: min(4rem, 100%)", "min-inline-size: 0",
                            "max-inline-size: 100%"):
            self.assertIn(declaration, color_section)
        self.assertIn("padding: min(1rem, 5vw)", css)
        html = (ROOT / "examples/native-elements.html").read_text()
        self.assertIn('aria-label="Sample campaign inventory"', html)
        self.assertIn('tabindex="0"', html)
        browser = (ROOT / "tests/native_semantic_browser.py").read_text()
        self.assertIn('"400%"', browser)
        self.assertIn('"#design-file"', browser)
        self.assertIn('"#design-color"', browser)

    def test_native_example_is_covered_by_shared_browser_audits(self):
        for script in ("tests/axe_audit.py", "tests/browser_matrix.py", "tests/reflow_test.py"):
            with self.subTest(script=script):
                self.assertIn('"examples/native-elements.html"', (ROOT / script).read_text())


if __name__ == "__main__":
    unittest.main()
