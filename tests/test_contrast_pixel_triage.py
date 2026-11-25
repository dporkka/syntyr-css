"""Conservative pixel-sampling math/summary contracts (developer-only tooling)."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).with_name('contrast_pixel_triage.py')
SPEC = importlib.util.spec_from_file_location('contrast_pixel_triage', FILE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PixelContrastMath(unittest.TestCase):
    def test_black_white_ratio_is_21(self):
        self.assertAlmostEqual(MODULE.contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0)

    def test_contrast_ratio_is_symmetric_and_identical_colors_are_one(self):
        self.assertEqual(MODULE.contrast_ratio((10, 20, 30), (10, 20, 30)), 1.0)
        self.assertAlmostEqual(MODULE.contrast_ratio((34, 85, 136), (230, 232, 244)),
                               MODULE.contrast_ratio((230, 232, 244), (34, 85, 136)))

    def test_threshold_distinguishes_large_and_regular_text(self):
        self.assertEqual(MODULE.text_contrast_threshold(16, 400), 4.5)
        self.assertEqual(MODULE.text_contrast_threshold(23, 600), 4.5)
        self.assertEqual(MODULE.text_contrast_threshold(19, 700), 3.0)
        self.assertEqual(MODULE.text_contrast_threshold(24, 400), 3.0)

    def test_color_parser_rejects_alpha_without_compositing(self):
        self.assertEqual(MODULE.parse_rgb('rgb(17, 34, 51)'), (17, 34, 51))
        self.assertEqual(MODULE.parse_rgb('rgba(17, 34, 51, 1)'), (17, 34, 51))
        self.assertIsNone(MODULE.parse_rgb('rgba(17, 34, 51, 0.6)'))
        self.assertIsNone(MODULE.parse_rgb('transparent'))

    def test_pixel_scoring_reports_below_and_above_threshold_without_certifying(self):
        class SolidImage:
            width = 12
            height = 12
            def __init__(self, color):
                self.color = color
            def getpixel(self, _position):
                return self.color

        item = {
            'page': 'fixture.html', 'selector': ['#test'], 'failure_summary': 'gradient',
            'viewport_width': 320, 'error': None,
            'fragments': [{'text': 'Small text', 'color': 'rgb(0, 0, 0)',
                           'fontSize': 16, 'weight': 400,
                           'rects': [{'left': 1, 'right': 10, 'top': 1, 'bottom': 10}]}],
        }
        self.assertEqual(MODULE.score_item(item, SolidImage((110, 110, 110)))['status'],
                         'sampled_below_threshold')
        good = MODULE.score_item(item, SolidImage((255, 255, 255)))
        self.assertEqual(good['status'], 'sampled_above_threshold')
        self.assertAlmostEqual(good['minimum_sampled_ratio'], 21)

    @staticmethod
    def placeholder_item(**overrides):
        placeholder = {
            "text": "Search records", "foreground": "rgb(77, 96, 121)",
            "background": "rgb(255, 255, 255)", "background_image": "none",
            "opacity": "1", "element_opacity": "1",
            "font_size_px": 16, "font_weight": 400,
        }
        placeholder.update(overrides)
        return {
            "page": "fixture.html", "selector": ["#search"],
            "failure_summary": "placeholder contrast", "viewport_width": 320,
            "error": "no_visible_text_rect", "fragments": [],
            "placeholder": placeholder,
        }

    def test_solid_visible_placeholder_gets_computed_labelled_contrast(self):
        result = MODULE.score_item(self.placeholder_item(), object())
        self.assertEqual(result["status"], "computed_placeholder_above_threshold")
        self.assertGreaterEqual(result["computed_ratio"], 4.5)
        self.assertIn("computed", result["method"])
        self.assertNotIn("minimum_sampled_ratio", result)

    def test_low_contrast_placeholder_is_flagged(self):
        result = MODULE.score_item(
            self.placeholder_item(foreground="rgb(245, 245, 245)"), object())
        self.assertEqual(result["status"], "computed_placeholder_below_threshold")

    def test_ambiguous_placeholder_paint_is_unsampled(self):
        for overrides in (
            {"background_image": "linear-gradient(red, blue)"},
            {"opacity": "0.5"},
            {"element_opacity": "0.2"},
            {"background": "rgba(255, 255, 255, 0.5)"},
            {"foreground": "rgba(20, 40, 60, 0.3)"},
            {"background": "transparent"},
            {"text": ""},
        ):
            with self.subTest(overrides=overrides):
                result = MODULE.score_item(self.placeholder_item(**overrides), object())
                self.assertEqual(result["status"], "unsampled")

    def test_capture_only_collects_actual_displayed_placeholders(self):
        js = MODULE.MEASURE_JS
        self.assertIn("el.matches(':placeholder-shown')", js)
        self.assertIn("getComputedStyle(el, '::placeholder')", js)
        self.assertIn("backgroundImage", js)

    def test_summary_keeps_unresolved_distinct_from_sampled(self):
        items = [
            {'status': 'sampled_below_threshold'},
            {'status': 'sampled_above_threshold'},
            {'status': 'unsampled'},
            {'status': 'non_text'},
        ]
        self.assertEqual(MODULE.status_counts(items), {
            'sampled_below_threshold': 1,
            'sampled_above_threshold': 1,
            'unsampled': 1,
            'non_text': 1,
        })


if __name__ == '__main__':
    unittest.main()
