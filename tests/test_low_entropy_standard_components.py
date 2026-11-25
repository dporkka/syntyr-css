"""Native-first standard library contracts should not need new widget classes."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LowEntropyStandardComponents(unittest.TestCase):
    def test_core_form_class_supports_native_specialized_inputs(self):
        css = (ROOT / "src/components/forms.css").read_text(encoding="utf-8")
        for kind in ("range", "file", "color"):
            with self.subTest(kind=kind):
                self.assertIn(f'&.syn-input[type="{kind}"]', css)
        self.assertIn("::file-selector-button", css)
        self.assertIn("accent-color: var(--syn-accent)", css)
        self.assertIn("@media (forced-colors: active)", css)
        # Native controls stay native, with no scripted shadow input or custom roles.
        self.assertNotIn("appearance: none", css)
        self.assertNotIn("role=\"slider\"", css)

    def test_standard_components_are_in_core_and_optional_semantic_mode(self):
        core = (ROOT / "dist/syntyr.core.css").read_text(encoding="utf-8")
        standalone = (ROOT / "dist/components/forms.css").read_text(encoding="utf-8")
        semantic = (ROOT / "src/semantic.css").read_text(encoding="utf-8")
        for kind in ("range", "file", "color"):
            with self.subTest(kind=kind):
                rule = f'&.syn-input[type="{kind}"]'
                self.assertIn(rule, core)
                self.assertIn(rule, standalone)
                self.assertIn(f'input[type="{kind}"]', semantic)
        for native in ("output", "meter", "progress", "details", "dialog", "summary"):
            self.assertIn(native, semantic)

    def test_native_first_inventory_and_examples_are_discoverable(self):
        docs = (ROOT / "docs/components.md").read_text(encoding="utf-8")
        gallery = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        self.assertIn("## Standard low-entropy component inventory", docs)
        for label in ("Text and search", "Range", "File upload", "Color picker",
                      "Date and time", "Choice controls", "Data and progress",
                      "Disclosure and overlays", "Navigation", "Media and content",
                      "Application-owned behavior"):
            with self.subTest(label=label):
                self.assertIn(label, docs)
        for kind in ("range", "file", "color"):
            self.assertRegex(gallery, rf'<input[^>]*type="{kind}"[^>]*class="syn-input"|<input[^>]*class="syn-input"[^>]*type="{kind}"')
        self.assertIn('data-catalog-keywords="native range file color', gallery)
        self.assertNotIn("new JavaScript runtime", docs)

    def test_no_new_core_dependencies_for_native_controls(self):
        forms = (ROOT / "src/components/forms.css").read_text(encoding="utf-8")
        self.assertNotIn("@import", forms)
        self.assertNotIn("@apply", forms)
        self.assertTrue(re.search(r'&\.syn-input\[type="range"\]', forms))


if __name__ == "__main__":
    unittest.main()
