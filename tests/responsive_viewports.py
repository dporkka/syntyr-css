"""Canonical CSS-pixel test targets, not CSS breakpoints.

Keep the docs playground width choices in sync (enforced by a unit test).
"""
import json
from pathlib import Path

_PROBE = json.loads((Path(__file__).resolve().parents[1] / "metadata/responsive-probe.v1.json").read_text(encoding="utf-8"))
CANONICAL_VIEWPORTS = tuple((v["id"], v["width"], v["height"]) for v in _PROBE["viewports"])

# Retain legacy and orientation/text enlargement coverage in addition to the
# canonical targets. Text scaling here is not native browser zoom.
PUBLISHED_VIEWPORTS = tuple((w, h, 1) for _, w, h in CANONICAL_VIEWPORTS) + (
    (320, 800, 1), (375, 812, 1), (430, 932, 1), (1024, 768, 1),
    (667, 375, 1), (844, 390, 1),
    (320, 800, 1.5), (320, 800, 2), (390, 844, 2),
)
