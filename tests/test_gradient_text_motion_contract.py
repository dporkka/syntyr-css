"""Opt-in gradient and text motion is composable with existing Syntyr blocks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GradientTextMotionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "src/motion.css").read_text()
        cls.docs = (ROOT / "docs/animation.md").read_text()

    def test_gradient_reuses_static_wash_and_requires_foreground(self):
        self.assertIn('data-syn-gradient="drift"', self.css)
        self.assertIn('syn-gradient-wash', self.css)
        self.assertIn('[data-syn-gradient-content]', self.css)
        self.assertIn('syn-gradient-drift', self.css)
        self.assertIn('pointer-events: none', self.css)
        self.assertIn('isolation: isolate', self.css)
        self.assertIn('syn-gradient-wash', self.docs)

    def test_text_effects_are_non_destructive_and_scope_to_root(self):
        for variant in ("underline", "glint"):
            self.assertIn('data-syn-text="' + variant + '"', self.css)
            self.assertIn('data-syn-text="' + variant + '"', self.docs)
        self.assertIn('.syn-root', self.css)
        self.assertIn('text-decoration', self.css)
        self.assertIn('background-clip: text', self.css)
        self.assertIn('@supports', self.css)

    def test_accessibility_makes_motion_opt_in_and_static_for_reduction(self):
        self.assertIn('prefers-reduced-motion: no-preference', self.css)
        self.assertIn('forced-colors: active', self.css)
        self.assertIn('(forced-colors: none)', self.css)
        self.assertIn('prefers-contrast: no-preference', self.css)
        self.assertIn('fallback', self.docs.lower())
        self.assertIn('essential text', self.docs.lower())
        self.assertNotIn('data-syn-gradient', (ROOT / 'src/base.css').read_text())
        self.assertNotIn('data-syn-text', (ROOT / 'src/base.css').read_text())

    def test_animation_demo_includes_copyable_examples(self):
        demo = (ROOT / 'examples/animation.html').read_text()
        for fragment in ('data-syn-gradient="drift"', 'data-syn-gradient-content',
                         'data-syn-text="underline"', 'data-syn-text="glint"'):
            self.assertIn(fragment, demo)
        self.assertIn('href="../dist/syntyr.motion.css"', demo)
        self.assertIn('href="../dist/syntyr.effects.css"', demo)


if __name__ == "__main__":
    unittest.main()
