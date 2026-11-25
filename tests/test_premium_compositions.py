"""Contracts for premium CSS-only composition recipes and surface hierarchy."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class PremiumCompositions(unittest.TestCase):
    def test_surface_depth_roles_are_theme_aware_and_opt_in(self):
        tokens = read("src/tokens.css")
        recipes = read("src/recipes.css")
        core = read("dist/syntyr.core.css")
        self.assertIn("--syn-surface-floating:", tokens)
        self.assertIn("--syn-border-floating:", tokens)
        for name in ("recessed", "raised", "floating"):
            self.assertIn(f".syn-surface--{name}", recipes)
            self.assertNotIn(f".syn-surface--{name}", core)
        self.assertIn("var(--syn-surface-floating)", recipes)
        self.assertIn("var(--syn-shadow-overlay)", recipes)
        self.assertIn("@media (forced-colors: active)", recipes)

    def test_workflow_compositions_are_styling_only_and_semantic(self):
        recipes = read("src/recipes.css")
        for name in (
            "syn-page-header",
            "syn-detail-layout",
            "syn-detail-main",
            "syn-detail-aside",
            "syn-command-panel",
            "syn-command-row",
            "syn-command-key",
            "syn-activity-timeline",
            "syn-showcase",
            "syn-showcase-visual",
        ):
            self.assertIn(f".{name}", recipes)
        self.assertIn('aria-current="true"', recipes)
        self.assertIn(":focus-visible", recipes)
        self.assertIn("prefers-reduced-motion: reduce", recipes)

    def test_example_uses_real_html_and_accessible_states(self):
        page = read("examples/premium-compositions.html")
        self.assertIn("syntyr.recipes.css", page)
        self.assertIn('data-syn-theme="studio"', page)
        self.assertIn('data-syn-theme="grid"', page)
        self.assertIn('data-syn-theme="noir"', page)
        self.assertIn('<search aria-label="Search sample actions">', page)
        self.assertIn("<form", page)
        self.assertIn("<kbd", page)
        self.assertIn('<ol class="syn-activity-timeline"', page)
        self.assertNotIn('aria-current="true"', page)
        self.assertIn('aria-label=', page)
        self.assertNotIn("<script", page)

    def test_docs_describe_app_owned_behavior_and_depth_roles(self):
        docs = read("docs/premium-compositions.md")
        self.assertIn("syntyr.recipes.css", docs)
        self.assertIn("application", docs.lower())
        self.assertIn("keyboard", docs.lower())
        self.assertIn("progressive enhancement", docs.lower())
        self.assertIn("syn-surface--floating", docs)
        self.assertIn("premium-compositions.html", docs)


if __name__ == "__main__":
    unittest.main()
