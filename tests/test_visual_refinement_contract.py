"""Design refinement contracts: calm enterprise UI without runtime dependencies."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VisualRefinementContract(unittest.TestCase):
    def test_role_based_typography_and_surface_hierarchy(self):
        tokens = (ROOT / "src/tokens.css").read_text()
        for token in ("--syn-font-ui:", "--syn-font-display:", "--syn-type-xs:",
                      "--syn-type-sm:", "--syn-type-base:", "--syn-surface-recessed:",
                      "--syn-surface-raised:", "--syn-border-subtle:", "--syn-row-padding-block:"):
            with self.subTest(token=token):
                self.assertIn(token, tokens)
        self.assertIn('data-syn-theme="minimal"', tokens)
        self.assertIn('data-syn-theme="studio"', tokens)
        self.assertIn("--syn-font-ui: var(--syn-mono);", tokens)

    def test_density_is_opt_in_and_scoped_to_syntyr(self):
        tokens = (ROOT / "src/tokens.css").read_text()
        self.assertIn('.syn-root[data-syn-density="compact"]', tokens)
        self.assertIn('.syn-root [data-syn-density="compact"]', tokens)
        self.assertIn("--syn-control-height: 2.25rem;", tokens)
        data = (ROOT / "src/components/data.css").read_text()
        self.assertIn("var(--syn-row-padding-block)", data)

    def test_calm_dashboard_navigation_and_compact_data_tables(self):
        recipes = (ROOT / "src/recipes.css").read_text()
        data = (ROOT / "src/components/data.css").read_text()
        typography = (ROOT / "src/components/typography.css").read_text()
        buttons = (ROOT / "src/components/buttons.css").read_text()
        self.assertIn("var(--syn-surface-recessed)", recipes)
        self.assertIn("var(--syn-border-subtle)", recipes)
        self.assertIn('.syn-table tbody tr:not([data-syn-state="selected"])', data)
        self.assertIn('.syn-table:is([role="grid"], [role="treegrid"]) tr[aria-selected="true"]', data)
        self.assertIn('font-variant-numeric: tabular-nums', data)
        self.assertIn("var(--syn-font-ui)", buttons)
        self.assertIn("var(--syn-font-ui)", typography)

    def test_premium_effects_are_optional_and_static(self):
        effects = (ROOT / "src/effects.css").read_text()
        core = (ROOT / "dist/syntyr.core.css").read_text()
        self.assertIn(".syn-gradient-wash", effects)
        self.assertNotIn(".syn-gradient-wash", core)
        self.assertNotIn("@keyframes", effects)
        self.assertIn("forced-colors: active", effects)

    def test_existing_live_examples_demonstrate_compact_and_editorial_modes(self):
        ops = (ROOT / "examples/operations-console.html").read_text()
        business = (ROOT / "examples/business.html").read_text()
        self.assertIn('data-syn-density="compact"', ops)
        self.assertIn('syn-site-heading--editorial', business)
        self.assertIn('syn-gradient-wash', business)
        self.assertIn('href="../dist/syntyr.effects.css"', business)
        self.assertNotIn("<script", ops.lower())
        self.assertNotIn("<script", business.lower())

    def test_research_document_is_in_public_allowlist(self):
        from scripts.build_cloudflare_site import source_files
        self.assertIn("docs/design-research-linear-resend.md", source_files())

    def test_no_arbitrary_gzip_thresholds_remain_in_enforced_tests(self):
        for path in (ROOT / "tests").glob("test_*.py"):
            with self.subTest(path=path.name):
                source = path.read_text()
                self.assertNotRegex(source, r'assertLessEqual\(len\(gzip\.compress')
                self.assertNotRegex(source, r'5\s*\*\s*1024|8\s*\*\s*1024')
        for path in ("README.md", "ARCHITECTURE.md", "docs/components.md",
                     "docs/geometry-terminal.md"):
            source = (ROOT / path).read_text()
            self.assertNotRegex(source, r'(?i)(core|full|all|bundle).*?(size budget|gzip limit|[58] ki?b gzip)')
        self.assertIn("gzip", (ROOT / "scripts/build.py").read_text())


if __name__ == "__main__":
    unittest.main()
