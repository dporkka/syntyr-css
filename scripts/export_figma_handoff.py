"""Generate a code-side Figma reconciliation handoff from canonical Syntyr CSS.

Does not query, inspect, or mutate the Figma document. Responsive and derived
styles are intentionally marked as requiring real browser/visual verification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

if __package__:
    from .export_ecosystem_adapters import COLORS
else:
    from export_ecosystem_adapters import COLORS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "metadata/figma/syntyr-handoff.v1.json"
DECL = re.compile(r"^\s*(--syn-[a-z0-9-]+):\s*([^;]+);", re.MULTILINE)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
REM = re.compile(r"^(-?(?:\d+(?:\.\d*)?|\.\d+))rem$")
PX = re.compile(r"^(-?(?:\d+(?:\.\d*)?|\.\d+))px$")


def scoped_declarations(source: str, selector: str) -> dict[str, str]:
    marker = selector + " {"
    # CSS comments are non-executable: never let a draft declaration replace
    # a real value in the generated design handoff.
    source = CSS_COMMENT.sub("", source)
    start = source.find(marker)
    if start < 0:
        raise ValueError(f"Missing CSS source scope: {selector}")
    start += len(marker)
    end = source.find("}", start)
    if end < 0:
        raise ValueError(f"Unclosed CSS scope: {selector}")
    return dict(DECL.findall(source[start:end]))


def foundation(name: str, value: str) -> dict:
    rem = REM.fullmatch(value)
    px = PX.fullmatch(value)
    figma_px = (round(float(rem.group(1)) * 16, 5) if rem
                else round(float(px.group(1)), 5) if px else None)
    return {
        "css_variable": name,
        "css_value": value,
        "figma_px": figma_px,
        "requires_browser_validation": figma_px is None,
    }


def build_handoff() -> dict:
    source = (ROOT / "src/tokens.css").read_text(encoding="utf-8")
    root = scoped_declarations(source, ":where(.syn-root)")
    if not {"--syn-space-1", "--syn-control-height", "--syn-type-heading"} <= root.keys():
        raise ValueError("Syntyr base typography/layout contract changed")
    density = {}
    for mode in ("compact", "comfortable", "spacious"):
        selector = (f':where(.syn-root[data-syn-density="{mode}"], '
                    f'.syn-root [data-syn-density="{mode}"])')
        declarations = scoped_declarations(source, selector)
        density[mode] = {key: foundation(key, val) for key, val in sorted(declarations.items())}
        if "--syn-control-height" not in density[mode]:
            raise ValueError(f"{mode}: missing control height")
    css_files = {
        "button": ("src/components/buttons.css", ("syn-button", "syn-button--primary",
                                                     "syn-button--outline")),
        "input": ("src/components/forms.css", ("syn-input", "syn-label", "syn-error")),
        "panel": ("src/components/layout.css", ("syn-panel",)),
        "status": ("src/components/data.css", ("syn-status",)),
    }
    components = {}
    for name, (file, names) in css_files.items():
        css = (ROOT / file).read_text(encoding="utf-8")
        for item in names:
            if f".{item}" not in css:
                raise ValueError(f"Source component selector no longer exists: {item}")
        components[name] = {
            "css_classes": list(names),
            "source_file": file,
            "canonical_stylesheet": "syntyr.core.css",
            "figma_state_is_visual_only": True,
        }
    return {
        "schema_version": 1,
        "source_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "root_font_px_assumption": 16,
        "palette_tokens": [f"--syn-{token}" for token in COLORS],
        "foundations": [foundation(name, value) for name, value in sorted(root.items())],
        "density": density,
        "components": components,
        "figma_pilot": {
            "file_url": "https://www.figma.com/design/Lj8uKUtgJfXMyzVb96x5Q1",
            "parity_status": "not-verified-live",
            "verified_color_tokens_per_theme": None,
            "documented_pilot_color_tokens_per_theme": 9,
            "required_source_color_tokens_per_theme": len(COLORS),
            "notes": "Prior kit documentation reports partial variables and a compact invalid-input instance. Reinspect live Figma before claiming parity.",
        },
        "limitations": (
            "This is not a Figma file inspection. Source literals are translated "
            "using a 16px root assumption; clamp(), var(), color-mix(), focus "
            "rings, accessibility, and rendered geometry need browser plus Figma review."
        ),
    }


def outputs() -> dict[Path, str]:
    return {OUTPUT: json.dumps(build_handoff(), indent=2, ensure_ascii=False) + "\n"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, expected in outputs().items():
        if args.check:
            ok = path.is_file() and path.read_text(encoding="utf-8") == expected
            print(f"{'OK' if ok else 'STALE'} {path.relative_to(ROOT)}")
            return int(not ok)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        print(f"WROTE {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
