"""Native CSS refinements preserve Syntyr's scoped, composable contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class NativeCSSComposition(unittest.TestCase):
    def test_record_fields_share_two_parent_tracks_and_stack_when_narrow(self):
        source = read("src/recipes.css")
        self.assertIn("container-name: syn-record-fields;", source)
        self.assertIn("container-type: inline-size;", source)
        self.assertIn("@supports (grid-template-columns: subgrid)", source)
        self.assertIn("grid-template-columns: subgrid;", source)
        self.assertIn("grid-column: 1 / -1;", source)
        self.assertIn("@container syn-record-fields (max-width: 24rem)", source)
        self.assertIn("grid-template-columns: minmax(0, 1fr);", source)
        self.assertIn("repeat(auto-fit, minmax(min(100%, 10rem), 1fr))", source)
        self.assertNotIn("subgrid", read("dist/syntyr.core.css"))

    def test_corner_effect_tracks_text_direction_without_a_new_variant(self):
        source = read("src/components/layout.css")
        self.assertIn("inset-inline-end: -1px;", source)
        self.assertIn("inset-block-end: -1px;", source)
        self.assertIn("&.syn-panel--cut:dir(rtl)::after", source)
        self.assertIn("clip-path: polygon(0 0, 0 100%, 100% 100%);", source)

    def test_popover_fallback_uses_logical_placement(self):
        source = read("src/components/overlays.css")
        self.assertIn("inset-block-end: 1rem;", source)
        self.assertIn("inset-inline-end: 1rem;", source)
        self.assertIn("position-try-fallbacks: flip-block, flip-inline;", source)
        self.assertNotIn("inset: auto 1rem 1rem auto;", source)

    def test_activity_timeline_markers_use_logical_properties(self):
        source = read("src/recipes.css")
        self.assertIn("padding-inline-start: 1.75rem;", source)
        self.assertIn("inset-inline-start: .25rem;", source)
        self.assertIn("inset-inline-start: .56rem;", source)

    def test_documentation_describes_subgrid_and_browser_fallback(self):
        doc = read("docs/recipes.md")
        for phrase in ("Subgrid", "container", "24rem", "fallback"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, doc)
        doc = read("docs/native-patterns.md")
        self.assertIn("RTL", doc)
        self.assertIn("logical", doc)

    def test_generated_optional_styles_have_subgrid(self):
        self.assertIn("grid-template-columns: subgrid;", read("dist/syntyr.recipes.css"))


if __name__ == "__main__":
    unittest.main()
