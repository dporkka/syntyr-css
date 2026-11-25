"""The responsive test matrix and playground must agree on canonical sizes."""
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = (
    ("small-mobile", 320, 568),
    ("mobile", 390, 844),
    ("tablet", 768, 1024),
    ("large-tablet", 1024, 1366),
    ("desktop", 1440, 900),
    ("large-desktop", 1920, 1080),
)


class PreviewOptions(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.widths = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "select":
            self.active = attrs.get("id") == "playground-viewport"
        elif self.active and tag == "option":
            self.widths.append(attrs["value"])

    def handle_endtag(self, tag):
        if tag == "select":
            self.active = False


class ResponsiveViewportContract(unittest.TestCase):
    def test_canonical_registry(self):
        from responsive_viewports import CANONICAL_VIEWPORTS
        self.assertEqual(CANONICAL_VIEWPORTS, EXPECTED)

    def test_playground_exposes_all_canonical_widths(self):
        options = PreviewOptions()
        options.feed((ROOT / "docs/playground.html").read_text())
        self.assertEqual(options.widths, ["fluid", *(str(w) for _, w, _ in EXPECTED)])

    def test_published_matrix_preserves_stress_cases(self):
        from responsive_viewports import CANONICAL_VIEWPORTS, PUBLISHED_VIEWPORTS
        for _, w, h in CANONICAL_VIEWPORTS:
            self.assertIn((w, h, 1), PUBLISHED_VIEWPORTS)
        for case in ((320, 800, 1.5), (320, 800, 2), (390, 844, 2),
                     (667, 375, 1), (844, 390, 1), (1024, 768, 1)):
            self.assertIn(case, PUBLISHED_VIEWPORTS)
        self.assertEqual(len(set(PUBLISHED_VIEWPORTS)), len(PUBLISHED_VIEWPORTS))
