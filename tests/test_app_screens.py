"""Native, copyable SaaS application screen contracts."""
from html.parser import HTMLParser
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit, unquote
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCREENS = {
    'app-onboarding.html': ('Workspace setup', 'onboarding-steps', 'progress'),
    'app-team.html': ('Team & invitations', 'team-members', 'table'),
    'app-notifications.html': ('Notification center', 'notifications-feed', 'time'),
    'app-integrations.html': ('Integrations', 'integrations-directory', 'article'),
    'app-security.html': ('Security & access', 'security-sessions', 'table'),
}

class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, name, attrs):
        self.elements.append((name, dict(attrs)))

class AppScreensContract(unittest.TestCase):
    def test_five_connected_accessible_native_screens(self):
        for filename, (heading, anchor, element) in SCREENS.items():
            with self.subTest(filename=filename):
                doc = ROOT / 'examples' / filename
                raw = doc.read_text(encoding='utf-8')
                parser = Markup()
                parser.feed(raw)
                elements = parser.elements
                ids = [attrs['id'] for _, attrs in elements if attrs.get('id')]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertIn(anchor, ids)
                self.assertIn(heading, unescape(raw))
                self.assertTrue(any(tag == element for tag, _ in elements))
                self.assertEqual(sum(tag == 'main' for tag, _ in elements), 1)
                self.assertEqual(sum(tag == 'h1' for tag, _ in elements), 1)
                self.assertEqual(sum(tag == 'script' for tag, _ in elements), 0)
                self.assertIn('syn-app-shell', raw)
                self.assertIn('syn-app-nav', raw)
                self.assertIn('syn-app-card', raw)
                self.assertIn('data-syn-density="compact"', raw)
                self.assertIn('app-screens.css', raw)
                self.assertIn('illustrative', raw.lower())
                self.assertIn('aria-current="page"', raw)
                self.assertFalse(any(tag == 'form' for tag, _ in elements))
                self.assertFalse(any(tag == 'button' and 'disabled' not in attrs
                                     for tag, attrs in elements), 'Do not present fake active mutations')
                self.assertTrue(any(tag == 'a' and attrs.get('href') == 'app-team.html'
                                    for tag, attrs in elements))
                self.assertTrue(any(tag == 'a' and attrs.get('href') == 'app-security.html'
                                    for tag, attrs in elements))
                for tag, attrs in elements:
                    if tag in ('a', 'link', 'img'):
                        value = attrs.get('href') or attrs.get('src', '')
                        self.assertFalse(value.startswith(('http:', 'https:', '//', 'javascript:')))
                        if value.startswith('#'):
                            self.assertIn(value[1:], ids)
                        elif value:
                            path = urlsplit(value).path
                            self.assertTrue((doc.parent / unquote(path)).exists(), f'{filename}: broken {value}')
                    if tag == 'label' and attrs.get('for'):
                        self.assertIn(attrs['for'], ids)
                for other in SCREENS:
                    if other != filename:
                        self.assertIn('href="' + other + '"', raw)

    def test_structural_security_and_state_labels(self):
        team = (ROOT / 'examples/app-team.html').read_text()
        self.assertIn('Pending invitation', team)
        self.assertIn('Administrator', team)
        self.assertIn('role="group" aria-label="Example team counts"', team)
        self.assertIn('Viewer', team)
        notifications = (ROOT / 'examples/app-notifications.html').read_text()
        self.assertIn('Unread', notifications)
        self.assertIn('Read', notifications)
        self.assertIn('Notification preferences', notifications)
        integrations = (ROOT / 'examples/app-integrations.html').read_text()
        self.assertIn('Connected (example)', integrations)
        self.assertIn('Not connected', integrations)
        security = (ROOT / 'examples/app-security.html').read_text()
        self.assertIn('Multi-factor authentication', security)
        self.assertIn('Active sessions', security)
        self.assertIn('API keys', security)
        self.assertNotIn('sk_live_', security)
        onboarding = (ROOT / 'examples/app-onboarding.html').read_text()
        self.assertIn('aria-current="step"', onboarding)
        self.assertIn('Get started', onboarding)

    def test_shared_styles_are_opt_in_accessible_and_responsive(self):
        css = (ROOT / 'examples/app-screens.css').read_text()
        self.assertIn('.app-screens', css)
        self.assertIn('@media (max-width:', css)
        self.assertIn('@media (forced-colors: active)', css)
        self.assertIn('@media (prefers-reduced-motion: reduce)', css)
        self.assertIn('--syn-', css)
        self.assertNotIn('@import', css)
        self.assertNotIn('url(', css)

    def test_explicit_public_allowlist_and_gallery(self):
        site = (ROOT / 'scripts/build_cloudflare_site.py').read_text()
        gallery = (ROOT / 'docs/index.html').read_text()
        guide = (ROOT / 'docs/app-screens.md').read_text()
        self.assertIn('"app-screens.css"', site)
        for name in SCREENS:
            self.assertIn('"' + name + '"', site)
            self.assertIn('"examples/' + name + '"', site)
            self.assertIn(name, gallery)
            self.assertIn(name, guide)
        self.assertIn('"app-screens.md"', site)
        self.assertTrue((ROOT / 'tests/app-screens_browser.cjs').is_file())
        for name in ('reflow_test.py', 'browser_matrix.py', 'axe_audit.py'):
            source = (ROOT / 'tests' / name).read_text()
            for screen in SCREENS:
                self.assertIn('\"examples/' + screen + '\"', source)

if __name__ == '__main__':
    unittest.main()
