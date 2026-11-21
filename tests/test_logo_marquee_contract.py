"""Public HTML/CSS contract of the opt-in responsive logo marquee."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LogoMarqueeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "src/motion.css").read_text()
        cls.docs = (ROOT / "docs/animation.md").read_text()
        cls.demo = (ROOT / "examples/animation.html").read_text()

    def test_opt_in_scoped_layout_has_two_independent_rows_and_repeatable_groups(self):
        for selector in (".syn-logo-marquee", ".syn-logo-marquee__row",
                         ".syn-logo-marquee__track", ".syn-logo-marquee__group"):
            self.assertIn(selector, self.css)
            self.assertIn(selector, self.docs)
            self.assertIn(selector.removeprefix("."), self.demo)
        self.assertIn(".syn-root", self.css)
        self.assertIn("min-inline-size: 100cqi", self.css)
        self.assertIn("container-type: inline-size", self.css)

    def test_seamless_loop_animates_exactly_one_of_two_identical_groups(self):
        self.assertIn("@keyframes syn-logo-marquee-scroll", self.css)
        self.assertIn("translateX(-50%)", self.css)
        self.assertIn("animation-timing-function: linear", self.css)
        self.assertIn("animation-iteration-count: infinite", self.css)
        self.assertIn(":first-child + .syn-logo-marquee__group:last-child", self.css)
        self.assertIn('data-syn-logo-direction="right"', self.css)
        self.assertIn("animation-direction: reverse", self.css)

    def test_exposed_custom_properties_and_accessibility_contract(self):
        for name in ("--syn-logo-duration", "--syn-logo-speed", "--syn-logo-gap",
                     "--syn-logo-height", "--syn-logo-row-gap", "--syn-logo-play-state"):
            self.assertIn(name, self.css)
            self.assertIn(name, self.docs)
        self.assertIn("prefers-reduced-motion: no-preference", self.css)
        self.assertIn(":focus-within", self.css)
        self.assertIn('aria-hidden="true"', self.demo)
        self.assertIn("inert", self.demo)
        self.assertIn('data-syn-logo-direction="left"', self.demo)
        self.assertIn('data-syn-logo-direction="right"', self.demo)
        self.assertIn("No JavaScript", self.docs)
        self.assertIn("alpha.5", self.docs)

    def test_build_preserves_motion_as_optional_module(self):
        from scripts.build import distributions
        distributions = distributions()
        self.assertIn("motion.css", distributions["syntyr.motion.css"])
        self.assertNotIn("motion.css", distributions["syntyr.core.css"])


if __name__ == "__main__":
    unittest.main()
