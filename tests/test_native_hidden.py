"""Native HTML visibility state must survive Syntyr component display styles."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeHiddenContract(unittest.TestCase):
    def test_hidden_is_respected_for_root_and_descendant_components(self):
        css = (ROOT / "src/base.css").read_text(encoding="utf-8")
        # A component or semantic selector may set display:flex/grid after
        # the browser's own [hidden] rule, so the base contract must win.
        match = re.search(
            r":where\(\.syn-root\[hidden\][^{}]*\.syn-root \[hidden\][^{}]*\)"
            r"\s*\{([^{}]*)\}", css, re.S
        )
        self.assertIsNotNone(match, "missing scoped root + descendant hidden guard")
        self.assertRegex(match.group(1), r"display\s*:\s*none\s*!important\s*;")

    def test_hidden_until_found_keeps_browser_reveal_behavior(self):
        css = (ROOT / "src/base.css").read_text(encoding="utf-8")
        self.assertIn(':not([hidden="until-found" i])', css)
        self.assertNotIn("content-visibility: hidden", css)

    def test_until_found_guidance_documents_incompatible_display_values(self):
        docs = (ROOT / "docs/native-patterns.md").read_text(encoding="utf-8")
        for value in ("display: none", "display: inline", "display: contents"):
            with self.subTest(value=value):
                self.assertIn(value, docs)

    def test_guard_is_in_core_and_semantic_distributions(self):
        for bundle in ("syntyr.core.css", "syntyr.semantic-bundle.css", "syntyr.all.css"):
            with self.subTest(bundle=bundle):
                css = (ROOT / "dist" / bundle).read_text(encoding="utf-8")
                self.assertIn('.syn-root[hidden]', css)
                self.assertIn('.syn-root [hidden]', css)
                self.assertIn(':not([hidden="until-found" i])', css)


if __name__ == "__main__":
    unittest.main()
