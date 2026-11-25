"""Contract for a deterministic bidirectional resize and content stress matrix."""
import unittest
from responsive_stress import sweep_widths, CONTENT_CASES


class ResponsiveStressContract(unittest.TestCase):
    def test_sweep_includes_endpoints_and_every_query_boundary(self):
        from responsive_boundaries import MEDIA, adjacent_pixels
        widths = sweep_widths()
        self.assertEqual(widths[0], 320)
        self.assertEqual(widths[-1], 2560)
        self.assertEqual(tuple(sorted(set(widths))), widths)
        self.assertTrue(all(b-a <= 32 for a,b in zip(widths,widths[1:])))
        for _, query, rem, _ in MEDIA:
            if "width" in query:
                self.assertTrue(set(adjacent_pixels(rem)).issubset(widths))

    def test_stress_cases_include_real_rtl_and_ltr_at_enlarged_text(self):
        self.assertEqual({(c[0], c[1]) for c in CONTENT_CASES},
                         {("de","ltr"),("pt-BR","ltr"),("ar","rtl"),("he","rtl")})
        for lang, direction, label, action, identifier in CONTENT_CASES:
            self.assertGreater(len(identifier), 40)
            self.assertGreater(len(action), 20)
