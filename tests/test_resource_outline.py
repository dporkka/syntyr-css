"""Resource outline is a native, optional navigation recipe, not an ARIA tree widget."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return (ROOT / name).read_text(encoding="utf-8")


class ResourceOutlineContract(unittest.TestCase):
    def test_optional_scoped_css_and_accessible_selection(self):
        css = source("src/native-recipes.css")
        self.assertIn(".syn-resource-outline", css)
        self.assertIn(":where(.syn-root.syn-resource-outline, .syn-root .syn-resource-outline)", css)
        self.assertIn('a[aria-current="page"]', css)
        self.assertIn(":focus-visible", css)
        self.assertIn("padding-inline-start:", css)
        self.assertIn("min-block-size: 2.75rem;", css)
        self.assertNotIn(".syn-resource-outline", source("dist/syntyr.core.css"))

    def test_nested_indent_is_capped_for_high_zoom(self):
        css = source("src/native-recipes.css")
        self.assertIn("margin-inline-start: min(var(--syn-outline-indent, .8rem), 2vw);", css)
        self.assertIn("padding-inline-start: min(var(--syn-space-2), 2vw);", css)

    def test_deep_resource_hierarchies_stop_accumulating_indentation(self):
        # Per-level 2vw can still consume the viewport after 20+ nested lists.
        selector = (":where(.syn-root.syn-resource-outline, .syn-root .syn-resource-outline) "
                    + " ".join(["ul"] * 5))
        for file in ("src/native-recipes.css", "dist/syntyr.native-recipes.css"):
            css = source(file)
            self.assertIn(selector + " {", css)
            rule = css.split(selector + " {", 1)[1].split("}", 1)[0]
            self.assertIn("margin-inline-start: 0", rule)
            self.assertIn("padding-inline-start: 0", rule)
            self.assertIn("border-inline-start: 0", rule)

    def test_native_no_js_hierarchy_and_link_navigation(self):
        html = source("examples/resource-outline.html")
        self.assertIn('class="syn-root"', html)
        self.assertIn('class="syn-resource-outline"', html)
        self.assertIn("<nav ", html)
        self.assertIn("<details", html)
        self.assertIn("<summary", html)
        self.assertIn('aria-current="page"', html)
        self.assertIn('href="#campaign-402"', html)
        self.assertNotIn('role="tree"', html)
        self.assertNotIn("<script", html)

    def test_mobile_navigation_exposes_the_same_resource_route(self):
        from html.parser import HTMLParser
        class NavLinks(HTMLParser):
            def __init__(self):
                super().__init__()
                self.nav = None
                self.routes = {"Main navigation": [], "Mobile navigation": []}
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "nav" and attrs.get("aria-label") in self.routes:
                    self.nav = attrs["aria-label"]
                if tag == "a" and self.nav and attrs.get("href"):
                    self.routes[self.nav].append(attrs["href"])
            def handle_endtag(self, tag):
                if tag == "nav":
                    self.nav = None
        parser = NavLinks()
        parser.feed(source("docs/index.html"))
        href = "../examples/resource-outline.html"
        self.assertIn(href, parser.routes["Main navigation"])
        self.assertIn(href, parser.routes["Mobile navigation"])

    def test_offline_release_contains_linked_demo(self):
        from scripts.package_release import FILES
        self.assertIn("examples/resource-outline.html", FILES)

    def test_host_owns_behavior_and_semantics_are_explained(self):
        docs = source("docs/native-patterns.md")
        self.assertIn("Resource outline", docs)
        self.assertIn("native disclosure", docs)
        self.assertIn("not an ARIA tree", docs)
        self.assertIn("application", docs)


if __name__ == "__main__":
    unittest.main()
