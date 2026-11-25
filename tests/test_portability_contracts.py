"""Durable component, composition and reference-page regression contracts.

Retains the useful pre-v1 behavioral checks without a separate file for each
historical alpha milestone. Commercial preview/release safety lives in its own
focused tests, not in the CSS compatibility contract.
"""
from pathlib import Path
from html.parser import HTMLParser
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PortableCoreContracts(unittest.TestCase):
    def test_embedded_root_does_not_occupy_full_viewport(self):
        base = (ROOT / 'src/base.css').read_text()
        self.assertIn('.syn-page', base)
        self.assertNotIn('min-height: 100vh;', base)
        self.assertIn('min-height: 100svh;', base)

    def test_component_variants_have_documented_css(self):
        buttons = (ROOT / 'src/components/buttons.css').read_text()
        forms = (ROOT / 'src/components/forms.css').read_text()
        for component in ('.syn-button--danger', '.syn-button--outline', '.syn-button--small'):
            self.assertIn(component, buttons)
        for state in (':user-invalid', '[aria-invalid="true"]', '.syn-help', '.syn-error'):
            self.assertIn(state, forms)

    def test_semantic_layer_retains_opt_in_and_scoping(self):
        css = (ROOT / 'src/semantic.css').read_text()
        self.assertIn('.syn-semantic', css)
        self.assertIn('input:not([class])', css)
        self.assertIn('input[data-syn-semantic]', css)
        self.assertIn('[aria-invalid="true"]', css)
        self.assertIn('input[type="range"]', css)

    def test_real_use_examples(self):
        for name in ('console.html', 'landing.html'):
            html = (ROOT / 'examples' / name).read_text()
            self.assertIn('syn-root syn-page', html)
            self.assertNotIn('<script', html)
            self.assertIn('syntyr.', html)


class ResponsiveCompositionContracts(unittest.TestCase):
    def test_modular_container_patterns_are_shipped(self):
        source = (ROOT / 'src/components/patterns.css').read_text()
        self.assertIn('.syn-region', source)
        self.assertIn('container-name: syn-region', source)
        self.assertIn('@container syn-region (min-width:', source)
        for item in ('.syn-split', '.syn-stats', '.syn-stat', '.syn-empty', '.syn-pricing', '.syn-price-card'):
            with self.subTest(item=item):
                self.assertIn(item, source)
        self.assertIn('components/patterns.css', (ROOT / 'scripts/build.py').read_text())
        self.assertIn('.syn-pricing', (ROOT / 'dist/syntyr.core.css').read_text())

    def test_accessible_state_styles_and_explicit_tokens(self):
        buttons = (ROOT / 'src/components/buttons.css').read_text()
        tokens = (ROOT / 'src/tokens.css').read_text()
        for item in ('[aria-pressed="true"]', '[data-syn-state="active"]', '[aria-busy="true"]'):
            self.assertIn(item, buttons)
        for token in ('--syn-ease:', '--syn-duration-fast:', '--syn-success:', '--syn-warning:'):
            self.assertIn(token, tokens)

    def test_free_original_recipes_and_marketing_example(self):
        for rel in ('docs/recipes.md', 'docs/tailwind-research.md', 'examples/pricing.html'):
            with self.subTest(rel=rel):
                self.assertTrue((ROOT / rel).is_file())
        gallery = (ROOT / 'docs/index.html').read_text()
        self.assertIn('id="recipes"', gallery)
        self.assertIn('class="syn-region"', gallery)
        self.assertIn('syn-price-card', gallery)
        self.assertIn('examples/pricing.html', gallery)
        self.assertNotIn('<script', gallery)
        pricing = (ROOT / 'examples/pricing.html').read_text()
        self.assertIn('syn-pricing', pricing)
        self.assertNotIn('<script', pricing)
        self.assertIn('MIT', pricing)

    def test_no_build_dependency_and_explicit_css_artifacts(self):
        self.assertNotIn('tailwindcss', (ROOT / 'dist/syntyr.core.css').read_text().lower())
        from scripts.asset_report import measure_distributions
        sizes = measure_distributions(ROOT / 'dist')
        self.assertIn('syntyr.core.css', sizes)
        self.assertIn('syntyr.all.css', sizes)


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.descriptions = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "meta" and values.get("name") == "description":
            self.descriptions.append(values.get("content", ""))


class ReferenceSiteContracts(unittest.TestCase):
    def test_original_resource_index_is_a_free_reusable_example(self):
        page = (ROOT / "examples/resources.html").read_text(encoding="utf-8")
        for fragment in ('syn-root syn-page', 'data-syn-theme="noir"', 'method="get"',
                         "aria-labelledby", 'scope="col"', "<caption", "syn-table-wrap",
                         "syn-input", "syn-select", "MIT", "ILLUSTRATIVE"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, page)
        self.assertNotIn("<script", page.lower())
        self.assertNotIn("stripe", page.lower())

    def test_theme_customization_guide_is_copy_pasteable(self):
        guide = (ROOT / "docs/theme-customization.md").read_text(encoding="utf-8")
        for token in ("--syn-accent", "--syn-on-accent", "--syn-bg", "--syn-surface",
                      "data-syn-theme", "syn-root", "syn-semantic", "prefers-reduced-motion"):
            self.assertIn(token, guide)
        self.assertIn(chr(96)*3 + "css", guide)
        self.assertIn(chr(96)*3 + "html", guide)
        self.assertIn("contrast", guide.lower())

    def test_site_gallery_links_to_new_demo_and_guide(self):
        page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn('href="../examples/resources.html"', page)
        self.assertIn('href="theme-customization.html"', page)
        metadata = MetadataParser()
        metadata.feed(page)
        self.assertEqual(len(metadata.descriptions), 1, "one non-conflicting SEO meta description")
        self.assertIn('role="group" aria-label="Grid palette"', page)
        self.assertIn('role="group" aria-label="Noir palette"', page)
