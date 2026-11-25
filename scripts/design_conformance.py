"""Validate core semantic-color pairs across Syntyr's seven built-in palettes.

This source-token audit does not measure computed gradients, authored theme
overrides, rendered state interactions, assistive technology or WCAG conformance.
No third-party packages or consumer runtime dependencies are required.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

if __package__:
    from .export_ecosystem_adapters import PALETTES, read_palettes
else:
    from export_ecosystem_adapters import PALETTES, read_palettes

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")

# role, foreground, background, minimum WCAG 2.x contrast
# Essential visible focus/strong boundaries are tested at non-text 3:1.
PAIRS = (
    ("text-on-background", "text", "bg", 4.5),
    ("text-on-surface", "text", "surface", 4.5),
    ("muted-on-background", "muted", "bg", 4.5),
    ("muted-on-surface", "muted", "surface", 4.5),
    ("accent-link-on-background", "accent", "bg", 4.5),
    ("accent-link-on-surface", "accent", "surface", 4.5),
    ("primary-action", "on-accent", "accent", 4.5),
    ("danger-on-surface", "danger", "surface", 4.5),
    ("success-on-surface", "success", "surface", 4.5),
    ("warning-on-surface", "warning", "surface", 4.5),
    ("focus-on-surface", "accent", "surface", 3.0),
    ("strong-boundary", "frame-strong", "surface", 3.0),
)


def luminance(hex_color: str) -> float:
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
              for v in channels]
    return sum(v * factor for v, factor in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast_ratio(foreground: str, background: str) -> float:
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def audit(css: str) -> dict:
    """Return machine-readable checked roles and failures, without suppressing gaps."""
    try:
        palettes = read_palettes(css, strict=False)
    except ValueError as exc:
        return {"ok": False, "palettes": {}, "failures": [{
            "theme": "all", "role": "palette-parser", "reason": "invalid-source",
            "detail": str(exc),
        }]}
    result = {}
    failures = []
    for theme in PALETTES:
        colors = palettes[theme]
        checks = []
        for role, fg, bg, minimum in PAIRS:
            foreground = colors.get(f"--syn-{fg}")
            background = colors.get(f"--syn-{bg}")
            check = {"role": role, "foreground": f"--syn-{fg}",
                     "background": f"--syn-{bg}", "minimum": minimum}
            if not foreground or not background:
                check.update(ok=False, reason="missing-token")
            elif not HEX.fullmatch(foreground) or not HEX.fullmatch(background):
                check.update(ok=False, reason="nonliteral-color")
            else:
                ratio = contrast_ratio(foreground, background)
                check.update(ok=ratio >= minimum, ratio=round(ratio, 3))
                if not check["ok"]:
                    check["reason"] = "insufficient-contrast"
            checks.append(check)
            if not check["ok"]:
                failures.append({"theme": theme, **check})
        result[theme] = {"checks": checks}
    return {"ok": not failures, "palettes": result, "failures": failures}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "src/tokens.css",
                        help="CSS source to audit (default: src/tokens.css)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    report = audit(args.source.read_text(encoding="utf-8"))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        total = sum(len(p["checks"]) for p in report["palettes"].values())
        print(f"Semantic color conformance: {total - len(report['failures'])}/{total} "
              f"roles pass across {len(report['palettes'])} palettes")
        for failure in report["failures"]:
            print(f"FAIL {failure['theme']}: {failure['role']} "
                  f"({failure['reason']}, minimum {failure.get('minimum', 'n/a')})")
        print("Token audit only; rendered gradients, custom themes, and user interaction "
              "require separate accessibility testing.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
