"""Free-tools: explicit publishing, SEO and zero network/browser dependency contract."""
import unittest
from html.parser import HTMLParser
from scripts.build_cloudflare_site import source_files, SITE_URL

PAGES = ('index.html', 'color-contrast-checker.html', 'css-theme-generator.html',
         'css-clamp-generator.html', 'responsive-design-tester.html', 'ascii-playground.html')

class FreeToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = source_files()

    def test_independent_indexable_pages_and_assets_are_allowlisted(self):
        sitemap = self.files['sitemap.xml'].decode()
        for filename in PAGES:
            path = 'tools/' + filename
            html = self.files[path].decode()
            self.assertIn('<h1', html, path)
            self.assertIn('<meta name="description"', html, path)
            self.assertIn('<title>', html, path)
            self.assertIn(f'<link rel="canonical" href="{SITE_URL}/tools/' + ('' if filename == 'index.html' else filename.removesuffix('.html')) + '">', html)
            self.assertIn('href="index.html"', html, path)
        for asset in ('site.css', 'site.mjs', 'logic.mjs', 'ascii-playground.css', 'ascii-playground.mjs', 'ascii-logic.mjs'):
            self.assertIn('tools/' + asset, self.files)
        self.assertIn(f'{SITE_URL}/tools/</loc>', sitemap)
        self.assertIn(f'{SITE_URL}/tools/color-contrast-checker</loc>', sitemap)

    def test_tools_linked_from_home_and_docs(self):
        self.assertIn('href="tools/"', self.files['index.html'].decode())
        self.assertIn('href="../tools/"', self.files['docs/index.html'].decode())

    def test_responsive_preview_iframe_uses_true_content_width(self):
        css = self.files['tools/site.css'].decode()
        import re
        iframe_rule = re.search(r'\.tool-stage iframe\s*\{([^}]*)\}', css)
        self.assertIsNotNone(iframe_rule)
        self.assertIn('box-sizing:content-box', iframe_rule.group(1))

    def test_form_customizer_is_discoverable_from_free_tools(self):
        for name in PAGES:
            html = self.files['tools/' + name].decode()
            self.assertIn('href="../docs/form-builder.html"', html, name)

    def test_nested_theme_preview_is_not_full_height_page(self):
        html = self.files['tools/css-theme-generator.html'].decode()
        self.assertIn('id="theme-preview" class="syn-root tool-sample"', html)
        self.assertNotIn('id="theme-preview" class="syn-root syn-page', html)

    def test_tools_are_isolated_and_have_strict_sandbox(self):
        html = self.files['tools/responsive-design-tester.html'].decode()
        self.assertIn('sandbox=""', html)
        self.assertNotIn('allow-scripts', html)
        self.assertIn('type="module"', html)
        self.assertIn('client-side', self.files['tools/index.html'].decode().lower())

if __name__ == '__main__':
    unittest.main()
