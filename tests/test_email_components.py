"""Contracts for optional, dependency-free email workflow presentations."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

from scripts.build import distributions, all_distributions
from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]


class DemoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.labels = set()
        self.controls = []
        self.buttons = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'label' and 'for' in attrs:
            self.labels.add(attrs['for'])
        if tag in ('input', 'textarea', 'select'):
            self.controls.append((tag, attrs))
        if tag == 'button':
            self.buttons.append(attrs)
        if tag == 'script':
            self.scripts.append(attrs)


class EmailComponentsContract(unittest.TestCase):
    def test_email_styles_are_optional_but_available_in_all_bundle(self):
        output = distributions()
        self.assertEqual(output['syntyr.email.css'], ('email.css',))
        self.assertIn('email.css', output['syntyr.all.css'])
        self.assertNotIn('email.css', output['syntyr.core.css'])
        self.assertIn('syntyr.email.css', all_distributions())
        self.assertTrue((ROOT / 'dist/syntyr.email.css').exists())
        self.assertNotIn('.syn-email-inbox', (ROOT / 'dist/syntyr.core.css').read_text())

    def test_email_module_uses_scoped_native_css_and_accessible_states(self):
        css = (ROOT / 'src/email.css').read_text()
        self.assertIn('@layer syn.email', css)
        self.assertIn(':where(.syn-root, .syn-root *)', css)
        for name in ('.syn-email-signup', '.syn-email-inbox', '.syn-email-item',
                     '.syn-email-compose', '.syn-email-recipient-list',
                     '.syn-email-message', '.syn-email-preferences'):
            with self.subTest(name=name):
                self.assertIn(name, css)
        self.assertIn('[data-syn-unread="true"]', css)
        self.assertIn('[aria-current="page"]', css)
        self.assertIn('@container', css)
        self.assertIn('@media (forced-colors: active)', css)
        self.assertNotIn('@import', css)
        self.assertNotIn('url(', css)

    def test_demo_has_real_html_controls_not_fake_interactions(self):
        demo = (ROOT / 'examples/email.html').read_text()
        parser = DemoParser()
        parser.feed(demo)
        self.assertEqual(parser.scripts, [])
        self.assertIn('syntyr.email.css', demo)
        self.assertTrue(any(a.get('type') == 'email' and 'required' in a for _, a in parser.controls))
        self.assertTrue(any(a.get('type') == 'file' for _, a in parser.controls))
        self.assertTrue(any(tag == 'textarea' for tag, _ in parser.controls))
        self.assertTrue(any(a.get('name') == 'topics' for _, a in parser.controls))
        self.assertTrue(any(a.get('autocomplete') == 'one-time-code' for _, a in parser.controls))
        for tag, attrs in parser.controls:
            if attrs.get('id'):
                self.assertIn(attrs['id'], parser.labels, f'missing label for {tag} {attrs["id"]}')
        for button in parser.buttons:
            self.assertIn(button.get('type'), ('submit', 'button'))
            if button.get('type') == 'submit':
                self.assertIn('disabled', button, 'demo must not pretend to send email')
        self.assertIn('Requires an application backend', demo)

    def test_docs_and_demo_are_published(self):
        published = source_files()
        for name in ('dist/syntyr.email.css', 'docs/email-components.md',
                     'docs/email-components.html', 'examples/email.html'):
            self.assertIn(name, published)
        guide = (ROOT / 'docs/email-components.md').read_text()
        self.assertIn('email clients', guide.lower())
        self.assertIn('consent', guide.lower())
        self.assertIn('autocomplete="email"', guide)


if __name__ == '__main__':
    unittest.main()
