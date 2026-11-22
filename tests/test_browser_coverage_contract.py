"""Ensure the optional browser and axe matrix include every publicly linked theme."""
from pathlib import Path
from html.parser import HTMLParser
import unittest


class GenericAriaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.unscoped_labels = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "div" and any(key in attrs for key in ("aria-label", "aria-labelledby")) and "role" not in attrs:
            self.unscoped_labels.append((attrs.get("class", ""), attrs.get("aria-label", "")))


ROOT = Path(__file__).resolve().parents[1]


class BrowserCoverageContract(unittest.TestCase):
    def test_blocks_gallery_is_in_browser_reflow_and_axe_inventories(self):
        for name in ("browser_matrix.py", "reflow_test.py", "axe_audit.py"):
            with self.subTest(script=name):
                source = (ROOT / "tests" / name).read_text(encoding="utf-8")
                self.assertIn('"docs/blocks.html"', source)

    def test_new_theme_gallery_is_in_cross_engine_and_axe_audits(self):
        for script in ("browser_matrix.py", "axe_audit.py"):
            with self.subTest(script=script):
                source = (ROOT / "tests" / script).read_text(encoding="utf-8")
                for page in ('"examples/themes.html"', '"examples/saas.html"',
                             '"examples/business.html"', '"examples/terminal.html"'):
                    self.assertIn(page, source)

    def test_new_onboarding_guides_are_in_browser_reflow_and_axe_audits(self):
        for script in ("browser_matrix.py", "reflow_test.py", "axe_audit.py"):
            with self.subTest(script=script):
                self.assertIn('"docs/guides.html"',
                              (ROOT / "tests" / script).read_text())

    def test_design_state_example_is_checked_in_every_browser_and_a11y_matrix(self):
        for script in ("browser_matrix.py", "axe_audit.py", "reflow_test.py"):
            with self.subTest(script=script):
                self.assertIn('"examples/design-states.html"',
                              (ROOT / "tests" / script).read_text(encoding="utf-8"))

    def test_cross_browser_matrix_covers_selected_hover_and_compact_inputs(self):
        source = (ROOT / "tests/browser_matrix.py").read_text()
        self.assertIn("assert_visual_refinement(browser)", source)
        self.assertIn('data-syn-density="compact"', source)
        self.assertIn('aria-selected="true"', source)
        self.assertIn("getBoundingClientRect().height", source)
        self.assertIn("row.hover()", source)

    def test_reflow_ignores_controls_inside_closed_native_disclosures(self):
        script = (ROOT / "tests/reflow_test.py").read_text()
        self.assertIn("details:not([open])", script)
        self.assertIn("closest('summary')", script)

    def test_nested_theme_probes_use_the_current_dataset_contract(self):
        source = (ROOT / "tests/browser_matrix.py").read_text()
        self.assertIn("dataset.synTheme", source)
        self.assertNotIn("dataset.cyTheme", source)

    def test_theme_matrix_checks_all_twelve_palettes_and_color_schemes(self):
        source = (ROOT / "tests/browser_matrix.py").read_text(encoding="utf-8")
        for theme in ("grid", "noir", "studio", "industrial", "terminal", "corporate", "minimal", "graphite", "midnight", "dim", "obsidian", "amethyst"):
            self.assertIn(f'"{theme}"', source)
        self.assertIn('colorScheme', source)

    def test_labeled_generic_containers_expose_a_semantic_role(self):
        pages = [ROOT / "index.html", *sorted((ROOT / "docs").glob("*.html")),
                 *sorted((ROOT / "examples").glob("*.html"))]
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                parser = GenericAriaParser()
                parser.feed(page.read_text(encoding="utf-8"))
                self.assertEqual(parser.unscoped_labels, [], "add an appropriate role")


if __name__ == "__main__":
    unittest.main()
