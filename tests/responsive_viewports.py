"""Canonical CSS-pixel test targets, not CSS breakpoints.

Keep the docs playground width choices in sync (enforced by a unit test).
"""
CANONICAL_VIEWPORTS = (
    ("small-mobile", 320, 568),
    ("mobile", 390, 844),
    ("tablet", 768, 1024),
    ("large-tablet", 1024, 1366),
    ("desktop", 1440, 900),
    ("large-desktop", 1920, 1080),
)

# Retain legacy and orientation/text enlargement coverage in addition to the
# canonical targets. Text scaling here is not native browser zoom.
PUBLISHED_VIEWPORTS = tuple((w, h, 1) for _, w, h in CANONICAL_VIEWPORTS) + (
    (320, 800, 1), (375, 812, 1), (430, 932, 1), (1024, 768, 1),
    (667, 375, 1), (844, 390, 1),
    (320, 800, 1.5), (320, 800, 2), (390, 844, 2),
)
