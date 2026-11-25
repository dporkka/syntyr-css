"""Public release must contain only the current SYNTYR brand and syn- API."""
from pathlib import Path
import subprocess
import re
import unittest
from scripts.build import all_distributions

ROOT = Path(__file__).resolve().parents[1]

class CleanBrandTests(unittest.TestCase):
    def test_tracked_source_contains_no_retired_brand_or_css_api(self):
        tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
        old_name = 'cyber' + 'line'
        old_prefix = 'cy' + '-'
        old_layer = 'cy' + '.'
        for relative in filter(None, tracked):
            self.assertNotIn(old_name, relative.lower(), relative)
            path = ROOT / relative
            if not path.is_file():
                continue
            try:
                contents = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            with self.subTest(path=relative):
                self.assertNotIn(old_name, contents.lower())
                self.assertIsNone(re.search(r'(?<![A-Za-z0-9])' + re.escape(old_prefix), contents))
                self.assertIsNone(re.search(r'(?<![A-Za-z0-9])' + re.escape(old_layer), contents))

    def test_only_syntyr_css_is_distributed(self):
        self.assertEqual(
            {p.relative_to(ROOT / 'dist').as_posix() for p in (ROOT / 'dist').rglob('*.css')},
            set(all_distributions()),
        )
        css = (ROOT / 'dist/syntyr.core.css').read_text()
        self.assertIn('.syn-root', css)
        self.assertIn('--syn-accent', css)
        self.assertIn('data-syn-theme', css)

if __name__ == '__main__':
    unittest.main()
