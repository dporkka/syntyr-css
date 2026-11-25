"""Read-only reconciliation of Syntyr portable token snapshots.

Supports the exported DTCG 2025.10 subset, not arbitrary DTCG documents.
Exit 0: unchanged; 1: valid but drifted; 2: invalid or unreadable.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys

if __package__:
    from .export_design_tokens import DENSITIES, PALETTES, export_tokens
else:
    from export_design_tokens import DENSITIES, PALETTES, export_tokens

REFERENCE = re.compile(r"\{([a-z0-9-]+\.[a-z0-9-]+)\}")
HEX = re.compile(r"#[0-9a-fA-F]{6}")


def number(value):
    return type(value) in (int, float) and (
        type(value) is int or math.isfinite(value))


def literal(kind, value, path):
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a typed literal or whole-token alias")
    if kind == "dimension":
        if (set(value) != {"value", "unit"} or value["unit"] not in ("px", "rem")
                or not number(value["value"])):
            raise ValueError(f"{path}: invalid dimension")
        return
    if kind != "color":
        raise ValueError(f"{path}: unsupported token type")
    if not {"colorSpace", "components"} <= value.keys() <= {
            "colorSpace", "components", "alpha", "hex"}:
        raise ValueError(f"{path}: unsupported color fields")
    components = value["components"]
    alpha = value.get("alpha", 1)
    if (value["colorSpace"] != "srgb" or not isinstance(components, list)
            or len(components) != 3
            or not all(number(v) and 0 <= v <= 1 for v in components)
            or not number(alpha) or not 0 <= alpha <= 1):
        raise ValueError(f"{path}: invalid sRGB color")
    if "hex" in value:
        h = value["hex"]
        # DTCG hex is an optional six-digit fallback, independent of alpha.
        if (not isinstance(h, str) or not HEX.fullmatch(h)
                or h.upper() != "#" + "".join(f"{round(v * 255):02X}" for v in components)):
            raise ValueError(f"{path}: inconsistent sRGB hex fallback")


def reconcile(actual, expected):
    """Validate against one explicit source snapshot and report structural drift."""
    if not isinstance(actual, dict) or actual.keys() != expected.keys():
        raise ValueError("Expected exactly the exported token groups")
    flat = {}
    baseline = {}
    refs = {}
    for group, tokens in expected.items():
        incoming = actual[group]
        if not isinstance(incoming, dict) or incoming.keys() != tokens.keys():
            raise ValueError(f"{group}: missing or unknown token names")
        for name, original in tokens.items():
            path = f"{group}.{name}"
            token = incoming[name]
            if (not isinstance(token, dict) or set(token) != {"$type", "$value"}
                    or token["$type"] != original["$type"]):
                raise ValueError(f"{path}: missing fields or changed token type")
            flat[path] = token
            baseline[path] = original
            value = token["$value"]
            if isinstance(value, str):
                match = REFERENCE.fullmatch(value)
                if not match:
                    raise ValueError(f"{path}: invalid alias syntax")
                refs[path] = match.group(1)
            else:
                literal(token["$type"], value, path)
    for path, target in refs.items():
        if target not in flat or flat[target]["$type"] != flat[path]["$type"]:
            raise ValueError(f"{path}: unresolved or mismatched alias {target}")
        seen = {path}
        while target in refs:
            if target in seen:
                raise ValueError(f"{path}: cyclic alias")
            seen.add(target)
            target = refs[target]
            if target not in flat or flat[target]["$type"] != flat[path]["$type"]:
                raise ValueError(f"{path}: unresolved or mismatched alias {target}")
    return [{"path": path, "source": baseline[path]["$value"],
             "candidate": flat[path]["$value"]}
            for path in sorted(flat) if flat[path] != baseline[path]]


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--theme", required=True, choices=PALETTES)
    parser.add_argument("--density", default="comfortable", choices=DENSITIES)
    args = parser.parse_args()
    try:
        actual = json.loads(args.snapshot.read_text(encoding="utf-8"),
                            object_pairs_hook=unique_object)
        changes = reconcile(actual, export_tokens(args.theme, args.density))
    except (OSError, ValueError, RecursionError) as exc:
        print(f"Invalid snapshot: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"theme": args.theme, "density": args.density,
                      "changes": changes}, indent=2))
    return int(bool(changes))


if __name__ == "__main__":
    sys.exit(main())
