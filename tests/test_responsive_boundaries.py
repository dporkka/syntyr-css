"""Ensure current dimensional media/container queries have a probe."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ResponsiveBoundaryContract(unittest.TestCase):
    def test_adjacent_pixels(self):
        from responsive_boundaries import adjacent_pixels
        self.assertEqual(adjacent_pixels(31), (495, 496, 497))
        self.assertEqual(adjacent_pixels(12), (191, 192, 193))

    def test_all_dimensional_queries_have_explicit_coverage(self):
        from responsive_boundaries import MEDIA, CONTAINERS
        # Intentionally constrain this inventory to the current simple rem
        # queries; a new query syntax requires a deliberate test strategy.
        expected = set()
        for path in (ROOT / "src").rglob("*.css"):
            source = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
            for match in re.finditer(r"@(media|container)\s+([^{}]+)\{", source):
                kind, condition = match.groups()
                if re.search(r"\b(?:width|height|inline-size|block-size)\b", condition):
                    expected.add((kind, str(path.relative_to(ROOT)), condition.strip()))
        actual = {("media", file, query) for file, query, *_ in MEDIA}
        actual |= {("container", file, query) for file, query, *_ in CONTAINERS}
        self.assertEqual(expected, actual)
