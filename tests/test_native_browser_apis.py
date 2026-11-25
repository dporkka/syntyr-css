"""Native browser enhancements remain opt-in, graceful, and CSS-first."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeDemoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.targets = []
        self.commands = []
        self.dialog_forms = []
        self.scripts = []
        self.has_main = False
        self.has_progress = False
        self.has_autosize = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'main':
            self.has_main = True
        if tag == 'script':
            self.scripts.append(attrs)
        if 'popovertarget' in attrs:
            self.targets.append(attrs['popovertarget'])
        if 'commandfor' in attrs:
            self.commands.append((attrs['commandfor'], attrs.get('command')))
        if tag == 'form' and attrs.get('method') == 'dialog':
            self.dialog_forms.append(attrs)
        if attrs.get('class', '').find('syn-reading-progress') >= 0:
            self.has_progress = attrs.get('aria-hidden') == 'true'
        if tag == 'textarea' and 'syn-textarea--autosize' in attrs.get('class', ''):
            self.has_autosize = True


class NativeBrowserApisContract(unittest.TestCase):
    def test_anchor_positioning_is_opt_in_with_native_fallback(self):
        css = (ROOT / 'src/components/overlays.css').read_text()
        self.assertIn('.syn-popover--anchored', css)
        self.assertIn('@supports (position-area: bottom)', css)
        self.assertIn('position-anchor: auto', css)
        self.assertIn('position-try-fallbacks: flip-block', css)
        self.assertIn('&.syn-popover { margin:', css)  # existing usable fallback

    def test_anchor_positioning_remains_active_during_exit(self):
        css = (ROOT / 'src/components/overlays.css').read_text()
        self.assertIn('&.syn-popover.syn-popover--anchored {', css)
        self.assertNotIn('&.syn-popover.syn-popover--anchored:popover-open {', css)

    def test_release_guide_demo_url_is_resolvable_outside_source_checkout(self):
        # The release archive contains docs and styles, not the HTML gallery.
        from scripts.package_release import FILES
        import re
        guide = (ROOT / 'docs/native-browser-apis.md').read_text()
        demo = re.search(r'\[scriptless integration demo\]\(([^)]+)\)', guide)
        self.assertIsNotNone(demo)
        if demo.group(1).startswith('../'):
            self.assertIn('examples/native-apis.html', FILES)
        else:
            self.assertEqual(demo.group(1), 'https://syntyr-css.pages.dev/examples/native-apis.html')

    def test_copyable_dialog_example_has_scoped_styling(self):
        guide = (ROOT / 'docs/native-browser-apis.md').read_text()
        example = guide.split('## Example: a dialog without an event handler', 1)[1]
        example = example.split('```html', 1)[1].split('```', 1)[0]
        self.assertIn('<section class="syn-root"', example)
        self.assertIn('class="syn-dialog"', example)
        self.assertIn('command="show-modal"', example)
        self.assertIn('</section>', example)

    def test_content_sized_textarea_has_constraints_and_fallback(self):
        css = (ROOT / 'src/components/forms.css').read_text()
        self.assertIn('.syn-textarea--autosize', css)
        self.assertIn('field-sizing: content', css)
        self.assertIn('max-height:', css)
        self.assertIn('&.syn-textarea { min-height:', css)

    def test_scroll_effect_and_overlay_motion_are_opt_in_and_reduced_motion_safe(self):
        css = (ROOT / 'src/motion.css').read_text()
        for fragment in ('.syn-reading-progress', 'animation-timeline: scroll(root block)',
                         '@supports (animation-timeline: scroll(root block))',
                         '@media (prefers-reduced-motion: no-preference)',
                         '.syn-popover--transition', '@starting-style',
                         'transition-behavior: allow-discrete'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, css)
        self.assertNotIn('document.startViewTransition()', css)
        self.assertNotIn('@keyframes', (ROOT / 'src/effects.css').read_text())
        self.assertIn('syntyr.motion.css', (ROOT / 'scripts/build.py').read_text())
        self.assertIn('.syn-reading-progress', (ROOT / 'dist/syntyr.motion.css').read_text())
        self.assertNotIn('.syn-reading-progress', (ROOT / 'dist/syntyr.core.css').read_text())

    def test_native_browser_demo_is_scriptless_and_controls_are_real(self):
        parser = NativeDemoParser()
        parser.feed((ROOT / 'examples/native-apis.html').read_text())
        self.assertTrue(parser.has_main)
        self.assertEqual(parser.scripts, [])
        self.assertTrue(parser.has_progress)
        self.assertTrue(parser.has_autosize)
        self.assertTrue(parser.dialog_forms)
        self.assertTrue(parser.targets)
        self.assertTrue(parser.commands)
        self.assertTrue(set(parser.targets) <= parser.ids)
        self.assertTrue({target for target, _ in parser.commands} <= parser.ids)

    def test_native_browser_guide_describes_progressive_enhancement_and_app_owned_apis(self):
        guide = (ROOT / 'docs/native-browser-apis.md').read_text()
        for fragment in ('Popover API', 'Invoker Commands', 'CSS anchor positioning',
                         'field-sizing', 'scroll-driven', 'View Transition API',
                         'Clipboard API', 'Web Share API', 'ResizeObserver',
                         'IntersectionObserver', 'requestClose', 'reduced-motion',
                         'examples/native-apis.html'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, guide)
        self.assertIn('href="native-browser-apis.html"', (ROOT / 'docs/index.html').read_text())
        self.assertIn('examples/native-apis.html', (ROOT / 'README.md').read_text())
        self.assertIn('"examples/native-apis.html"', (ROOT / 'tests/reflow_test.py').read_text())


if __name__ == '__main__':
    unittest.main()
