"""Single-file, scoped semantic onboarding stays consistent with every release channel."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

from scripts.build import distributions
from scripts.package_release import FILES
from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


class SemanticStarterTests(unittest.TestCase):
    def test_one_file_matches_core_plus_semantic_without_overwriting_components(self):
        manifests = distributions()
        self.assertEqual(manifests['syntyr.semantic-bundle.css'],
                         manifests['syntyr.core.css'] + ('semantic.css',))
        bundle = (ROOT / 'dist/syntyr.semantic-bundle.css').read_text()
        self.assertEqual(bundle, (ROOT / 'dist/syntyr.core.css').read_text()
                         + (ROOT / 'dist/syntyr.semantic.css').read_text())
        self.assertIn('@layer syn.semantic', bundle)
        self.assertIn('.syn-root', bundle)

    def test_bundle_is_available_to_npm_zip_and_cloudflare(self):
        pkg = json.loads((ROOT / 'package.json').read_text())
        self.assertEqual(pkg['exports']['./semantic-bundle.css'],
                         './dist/syntyr.semantic-bundle.css')
        self.assertIn('dist/syntyr.semantic-bundle.css', FILES)
        published = source_files()
        self.assertIn('dist/syntyr.semantic-bundle.css', published)
        self.assertIn('examples/semantic-starter.html', published)
        self.assertIn('docs/from-pico.md', published)

    def test_example_uses_one_css_file_and_real_semantic_markup(self):
        source = (ROOT / 'examples/semantic-starter.html').read_text()
        parser = PageParser()
        parser.feed(source)
        styles = [a['href'] for tag, a in parser.nodes
                  if tag == 'link' and a.get('rel') == 'stylesheet']
        self.assertEqual(styles, ['../dist/syntyr.semantic-bundle.css'])
        self.assertFalse(any(tag == 'script' for tag, _ in parser.nodes))
        bodies = [a for tag, a in parser.nodes if tag == 'body']
        self.assertEqual(len(bodies), 1)
        self.assertEqual(set(bodies[0]['class'].split()), {'syn-root', 'syn-page', 'syn-semantic'})
        self.assertEqual(bodies[0]['data-syn-theme'], 'studio')
        self.assertTrue({'main', 'form', 'input', 'button', 'article', 'details', 'summary'}
                        <= {tag for tag, _ in parser.nodes})
        self.assertIn('action="?"', source)
        self.assertNotIn('onclick=', source)

    def test_semantic_starter_link_is_reachable_in_desktop_and_mobile_nav(self):
        html = (ROOT / "index.html").read_text()
        import re
        for label in ('Main navigation', 'Mobile navigation'):
            match = re.search(r'<nav\b[^>]*aria-label="' + label + r'"[^>]*>(.*?)</nav>', html, re.S)
            self.assertIsNotNone(match, f"Missing {label}")
            self.assertIn('href="examples/semantic-starter.html"', match.group(1),
                          f"Starter missing from {label}")

    def test_agent_documentation_exposes_pico_migration_only_for_alpha5(self):
        index = (ROOT / "llms.txt").read_text()
        sources = (ROOT / "scripts/build_agent_docs.py").read_text()
        combined = (ROOT / "llms-full.txt").read_text()
        self.assertIn("docs/from-pico.md", index)
        self.assertIn('"docs/from-pico.md"', sources)
        self.assertIn("## Source: docs/from-pico.md", combined)
        guide = (ROOT / "docs/from-pico.md").read_text()
        self.assertIn("alpha.5-only", guide)
        self.assertIn("explicit", guide)
        self.assertIn("alpha.4", guide)
        guide_index = (ROOT / "docs/guides.html").read_text()
        self.assertIn('href="from-pico.html"', guide_index)
        self.assertIn('href="../examples/semantic-starter.html"', guide_index)

    def test_document_starter_uses_existing_preset_and_print_module(self):
        source = (ROOT / "examples/document-starter.html").read_text()
        parser = PageParser()
        parser.feed(source)
        self.assertEqual([attrs["href"] for tag, attrs in parser.nodes
                          if tag == "link" and attrs.get("rel") == "stylesheet"],
                         ["../dist/presets/minimal.css", "../dist/syntyr.print.css"])
        self.assertFalse(any(tag == "script" for tag, _ in parser.nodes))
        self.assertIn("examples/document-starter.html", source_files())
        self.assertTrue({"h1", "h2", "pre", "code", "figure", "figcaption", "table", "ol", "ul"}
                        <= {tag for tag, _ in parser.nodes})
        self.assertIn('class="chroma"', source)
        self.assertIn('class="syn-shell syn-prose"', source)
        self.assertIn('class="syn-root syn-panel"', source)
        self.assertIn('role="region" aria-label="Inventory" tabindex="0"', source)
        self.assertIn("tests/document_prose_browser.py", (ROOT / ".woodpecker/browser.yaml").read_text())
        self.assertIn("../examples/document-starter.html", (ROOT / "docs/from-pico.md").read_text())

    def test_documented_starter_is_not_misrepresented_as_published(self):
        for relative in ('README.md', 'docs/distribution.md', 'docs/ai-quickstart.md'):
            content = (ROOT / relative).read_text()
            self.assertIn('syntyr.semantic-bundle.css', content, relative)
            self.assertIn('alpha.5', content, relative)


if __name__ == '__main__':
    unittest.main()
