"""Public opt-in CSS contract for reusable website-block effects."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BlockMotionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.motion = (ROOT / 'src/motion.css').read_text()
        cls.docs = (ROOT / 'docs/animation.md').read_text()

    def test_scroll_presets_are_declarative_and_scoped(self):
        for name in ('fade', 'rise', 'slide-left', 'slide-right', 'zoom'):
            with self.subTest(preset=name):
                self.assertIn(f'[data-syn-scroll="{name}"]', self.motion)
                self.assertIn(f'data-syn-scroll="{name}"', self.docs)
        self.assertIn('.syn-root', self.motion)
        self.assertIn('animation-timeline: view()', self.motion)
        self.assertIn('animation-range: entry 0% entry 100%;', self.motion)

    def test_scroll_animation_requires_native_full_support_and_motion_opt_in(self):
        self.assertIn('@supports (animation-timeline: view()) and (animation-range: entry 0% entry 100%)', self.motion)
        self.assertIn('@media (prefers-reduced-motion: no-preference)', self.motion)
        self.assertIn('fallback', self.docs.lower())
        self.assertIn('prefers-reduced-motion', self.docs)

    def test_hover_example_and_agent_index_are_discoverable_and_clipped(self):
        self.assertIn('style="display: block" href="/portfolio/project" data-syn-hover="zoom"', self.docs)
        index = (ROOT / 'llms.txt').read_text()
        self.assertIn('CSS-only scroll', index)
        self.assertIn('parallax', index)

    def test_parallax_layer_uses_view_timeline_and_has_overscan(self):
        for selector in ('[data-syn-parallax]', '[data-syn-parallax-layer]', '[data-syn-parallax-content]'):
            self.assertIn(selector, self.motion)
            self.assertIn(selector.strip("[]"), self.docs)
        self.assertIn('view-timeline-name: --syn-parallax', self.motion)
        self.assertIn('animation-timeline: --syn-parallax', self.motion)
        self.assertIn('--syn-parallax-travel', self.motion)
        self.assertIn('overflow: clip', self.motion)

    def test_hover_media_zoom_is_opt_in_and_reduced_motion_respected(self):
        self.assertIn('[data-syn-hover="zoom"]', self.motion)
        self.assertIn('[data-syn-hover-media]', self.motion)
        self.assertIn('(hover: hover)', self.motion)
        self.assertIn('(pointer: fine)', self.motion)
        self.assertIn('syn-surface--lift', self.docs)  # reuse, do not duplicate existing class

    def test_common_website_animations_are_opt_in_and_scope_bounded(self):
        names = ("fade-in", "fade-out", "slide-up", "slide-down", "slide-left",
                 "slide-right", "zoom-in", "zoom-out", "pop", "bounce", "pulse",
                 "shake", "rotate-in", "flip-in")
        for name in names:
            with self.subTest(name=name):
                self.assertIn(f'[data-syn-animate="{name}"]', self.motion)
                self.assertIn(f'@keyframes syn-animate-{name}', self.motion)
                self.assertIn(f'data-syn-animate="{name}"', self.docs)
        self.assertIn('.syn-root[data-syn-animate]', self.motion)
        self.assertIn('.syn-root [data-syn-animate]', self.motion)
        self.assertIn('prefers-reduced-motion: no-preference', self.motion)

    def test_animation_loop_controls_have_safe_defaults(self):
        for token in ('--syn-animation-duration', '--syn-animation-delay',
                      '--syn-animation-easing', '--syn-animation-iterations',
                      '--syn-animation-direction', '--syn-animation-play-state',
                      '--syn-animation-fill-mode', '--syn-animation-distance',
                      '--syn-animation-scale'):
            self.assertIn(token, self.motion)
            self.assertIn(token, self.docs)
        self.assertIn('syn-animate--loop', self.motion)
        self.assertIn('animation-iteration-count: var(--syn-animation-iterations, 1)', self.motion)
        self.assertIn('animation-fill-mode: var(--syn-animation-fill-mode, none)', self.motion)
        self.assertIn('--syn-animation-keyframes: none', self.motion)
        self.assertNotIn('!important', self.motion)
        self.assertIn('iterations: 3', self.docs)
        self.assertIn('loop: true', self.docs)

    def test_existing_animation_demo_showcases_css_only_block_effects(self):
        demo = (ROOT / 'examples/animation.html').read_text()
        self.assertIn('href="../dist/syntyr.motion.css"', demo)
        for attr in ('data-syn-scroll="rise"', 'data-syn-scroll="fade"',
                     'data-syn-parallax', 'data-syn-parallax-layer',
                     'data-syn-parallax-content', 'data-syn-hover="zoom"',
                     'data-syn-hover-media'):
            with self.subTest(attr=attr):
                self.assertIn(attr, demo)

    def test_no_core_motion_or_runtime_is_added(self):
        core = (ROOT / 'src/base.css').read_text()
        self.assertNotIn('data-syn-scroll', core)
        self.assertNotIn('data-syn-parallax', core)
        self.assertNotIn('data-syn-hover="zoom"', core)
        self.assertNotIn('@import', self.motion)
        self.assertIn('syntyr.motion.css', self.docs)


if __name__ == '__main__':
    unittest.main()
