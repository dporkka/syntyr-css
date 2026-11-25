"""Optional command launcher enhances the existing styling without core JS."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read(path):
    file = ROOT / path
    return file.read_text(encoding="utf-8") if file.exists() else ""


class CommandLauncherRecipeTests(unittest.TestCase):
    def test_dialog_and_no_js_destinations_exist(self):
        html = read("examples/command-launcher.html")
        self.assertIn('class="syn-command-panel"', html)
        self.assertIn('<dialog', html)
        self.assertIn('aria-labelledby="command-title"', html)
        self.assertIn('data-command-open hidden', html)
        self.assertIn('href="#quick-destinations"', html)
        self.assertIn('<nav id="quick-destinations"', html)
        self.assertIn('type="module" src="command-launcher.mjs"', html)
        self.assertIn('<label class="syn-label" for="command-query"', html)
        self.assertIn('data-command-empty hidden', html)
        self.assertNotIn('onclick=', html)
        self.assertNotIn('role="combobox"', html)

    def test_optional_adapter_uses_native_dialog_and_safe_text(self):
        js = read("examples/command-launcher.mjs")
        for needle in ('showModal()', 'close()', 'addEventListener("keydown"',
                       'addEventListener("input"', 'event.metaKey', 'event.ctrlKey',
                       'textContent', 'item.hidden =', 'export function matchCommand'):
            with self.subTest(needle=needle):
                self.assertIn(needle, js)
        for forbidden in ('innerHTML', 'eval(', 'fetch(', 'localStorage', 'document.write'):
            self.assertNotIn(forbidden, js)

    def test_existing_css_styled_as_dialog_without_new_visual_family(self):
        css = read("src/recipes.css")
        self.assertIn('&.syn-command-panel:where(dialog)', css)
        self.assertIn('&.syn-command-panel:where(dialog)::backdrop', css)
        self.assertIn('.syn-command-row', css)
        self.assertNotIn('.syn-command-launcher', css)

    def test_both_command_destinations_resolve_inside_offline_zip(self):
        from html.parser import HTMLParser
        from pathlib import PurePosixPath
        from scripts.package_release import FILES
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.destinations = []
            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    target = dict(attrs).get("href", "")
                    if target.startswith("./") or target.startswith("../"):
                        self.destinations.append(target)
        links = Links()
        links.feed(read("examples/command-launcher.html"))
        self.assertEqual(len(links.destinations), 6)
        self.assertEqual(links.destinations[:3], links.destinations[3:])
        self.assertIn("python3 -m http.server 8000 --bind 127.0.0.1", read("docs/distribution.md"))
        for href in links.destinations:
            # Parent of examples/command-launcher.html within release ZIP.
            target = PurePosixPath("examples").joinpath(href)
            parts = []
            for part in target.parts:
                if part == "..":
                    parts.pop()
                elif part != ".":
                    parts.append(part)
            packaged = "/".join(parts)
            with self.subTest(href=href):
                self.assertIn(packaged, FILES)
                self.assertTrue((ROOT / packaged).is_file())

    def test_example_is_allowlisted_and_documented(self):
        site = read("scripts/build_cloudflare_site.py")
        zip_script = read("scripts/package_release.py")
        for name in ('command-launcher.html', 'command-launcher.mjs'):
            self.assertIn(f'"{name}"', site)
            self.assertIn(f'"examples/{name}"', zip_script)
        self.assertIn('command-launcher.html', read('README.md'))
        self.assertIn('command-launcher.html', read('docs/premium-compositions.md'))


if __name__ == '__main__':
    unittest.main()
