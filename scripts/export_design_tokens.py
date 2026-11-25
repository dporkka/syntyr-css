"""Export portable DTCG-style token snapshots from canonical Syntyr CSS.

One explicit theme/density per document; browser-dependent values are omitted.
No Figma API, runtime dependency, or generated CSS change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

if __package__:
    from .export_ecosystem_adapters import COLORS, DIMENSIONS, PALETTES, REM_VALUE, figma_color, read_palettes
    from .export_figma_handoff import scoped_declarations
else:
    from export_ecosystem_adapters import COLORS, DIMENSIONS, PALETTES, REM_VALUE, figma_color, read_palettes
    from export_figma_handoff import scoped_declarations

ROOT = Path(__file__).resolve().parents[1]
DENSITIES = ("compact", "comfortable", "spacious")
ALIAS = re.compile(r"var\(--syn-([a-z0-9-]+)\)")
# Fluid tokens can change under @supports; a fallback is not their portable value.
FOUNDATIONS = (
    "type-xs", "type-sm", "type-base", "type-body",
    "space-1", "space-2", "space-3", "space-4", "space-5",
    "content-max", "content-gap", "control-height", "control-padding-block",
    "row-padding-block", "card-padding", "panel-padding-default",
)
SEMANTIC = (
    "text-subtle", "border-default", "border-hover", "border-focus",
    "focus-ring", "surface-interactive", "primary-hover-bg",
)


def dimension(value: str) -> dict | None:
    match = REM_VALUE.fullmatch(value)
    if value == "0":
        return {"$type": "dimension", "$value": {"value": 0, "unit": "px"}}
    if match:
        return {"$type": "dimension", "$value": {"value": float(match.group(1)), "unit": "rem"}}
    return None


def export_tokens(theme: str, density: str = "comfortable") -> dict:
    if theme not in PALETTES or density not in DENSITIES:
        raise ValueError(f"Unsupported theme/density: {theme}/{density}")
    source = (ROOT / "src/tokens.css").read_text(encoding="utf-8")
    palette = read_palettes(source)[theme]
    base = scoped_declarations(source, ":where(.syn-root)")
    base.update(scoped_declarations(
        source, f':where(.syn-root[data-syn-density="{density}"], '
                f'.syn-root [data-syn-density="{density}"])'))
    semantic = scoped_declarations(source, ":where(.syn-root, .syn-root [data-syn-theme])")
    result = {"palette": {}, "foundation": {}, "semantic": {}}
    for name in COLORS:
        result["palette"][name] = figma_color(palette[f"--syn-{name}"])
    for name in DIMENSIONS:
        token = dimension(palette[f"--syn-{name}"])
        if token is None:
            raise ValueError(f"Unsupported palette dimension: {name}")
        result["palette"][name] = token
    # First collect literals; aliases can only point to existing typed literals.
    for name in FOUNDATIONS:
        value = base[f"--syn-{name}"]
        token = dimension(value)
        if token is not None:
            result["foundation"][name] = token
    for group, names, declarations in (
        ("foundation", FOUNDATIONS, base), ("semantic", SEMANTIC, semantic)
    ):
        for name in names:
            match = ALIAS.fullmatch(declarations[f"--syn-{name}"])
            if not match:
                continue
            target_name = match.group(1)
            for target_group in ("palette", "foundation"):
                target = result[target_group].get(target_name)
                if target is not None and isinstance(target["$value"], dict):
                    result[group][name] = {
                        "$type": target["$type"],
                        "$value": "{" + target_group + "." + target_name + "}",
                    }
                    break
            else:
                raise ValueError(f"Unsupported alias target: {name} -> {target_name}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=PALETTES, required=True)
    parser.add_argument("--density", choices=DENSITIES, default="comfortable")
    args = parser.parse_args()
    print(json.dumps(export_tokens(args.theme, args.density), indent=2))


if __name__ == "__main__":
    main()
