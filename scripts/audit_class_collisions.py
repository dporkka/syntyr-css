"""Audit exact public-class collisions with another CSS stylesheet.

Requires only the Python standard library. This reports class names found in
explicit selectors; it is not proof of compatibility (resets, element selectors,
specificity, and styles from dynamic CSS generators can still conflict).

Example: python3 scripts/audit_class_collisions.py --css host.css --json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CSS_WHITESPACE = " \t\r\n\f"
# CSS whitespace only: `\s` would also consume U+00A0, which belongs to a
# property name and would fabricate a declaration that is not present.
TOKEN_DECLARATION = re.compile(
    rf"[{CSS_WHITESPACE}]*(--syn-[\w-]+)[{CSS_WHITESPACE}]*:", re.UNICODE)
HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def _mask_comments_and_strings(source: str) -> str:
    """Keep punctuation structure without treating CSS strings as selectors."""
    out = []
    i = 0
    while i < len(source):
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            i = len(source) if end == -1 else end + 2
            out.append(" ")
        elif source[i] == "\\":
            # An escape outside a string keeps the next character literal: a
            # quote here belongs to an identifier, so it must not open a string.
            out.append(source[i])
            if i + 1 < len(source):
                out.append(source[i + 1])
                i += 2
            else:
                i += 1
        elif source[i] in ("'", '"'):
            quote = source[i]
            i += 1
            while i < len(source):
                if source[i] == "\\":
                    i += 2
                elif source[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            out.append(" ")
        else:
            out.append(source[i])
            i += 1
    return "".join(out)


def _css_name_char(char: str) -> bool:
    return (char.isascii() and (char.isalnum() or char in "_-")) or ord(char) >= 0x80


def _css_name_start(char: str) -> bool:
    return (char.isascii() and (char.isalpha() or char == "_")) or ord(char) >= 0x80


def _read_css_identifier(source: str, start: int) -> tuple[str, int] | None:
    """Read one complete CSS identifier, decoding escapes per CSS Syntax.

    A Unicode/escaped suffix belongs to the SAME class, not a shorter
    ASCII prefix. Hex escapes consume up to six digits and one terminator
    whitespace; punctuation escapes consume exactly one character.
    """
    if start >= len(source):
        return None
    first = source[start]
    if not (_css_name_start(first) or first in "-\\"):
        return None
    if first == "-" and (start + 1 == len(source) or
                         not (_css_name_start(source[start + 1]) or
                              source[start + 1] in "-\\")):
        return None

    output = []
    pos = start
    while pos < len(source):
        char = source[pos]
        if char == "\\":
            if pos + 1 >= len(source) or source[pos + 1] in "\r\n\f":
                return None
            pos += 1
            if source[pos] in HEX_DIGITS:
                end = pos
                while (end < len(source) and end - pos < 6 and
                       source[end] in HEX_DIGITS):
                    end += 1
                codepoint = int(source[pos:end], 16)
                if codepoint == 0 or 0xD800 <= codepoint <= 0xDFFF or codepoint > 0x10FFFF:
                    codepoint = 0xFFFD
                output.append(chr(codepoint))
                pos = end
                if pos < len(source) and source[pos] in CSS_WHITESPACE:
                    pos += 1
            else:
                output.append(source[pos])
                pos += 1
        elif _css_name_char(char):
            output.append(char)
            pos += 1
        else:
            break
    return ("".join(output), pos) if output else None


def extract_css_classes(css: str) -> set[str]:
    """Discover explicit class selectors, including escaped punctuation.

    Handles nested @media/@layer blocks and native CSS nesting. It does not
    expand compiler-generated utilities or concatenated CSS nesting suffixes.
    """
    classes: set[str] = set()
    prelude: list[str] = []
    for char in _mask_comments_and_strings(css):
        if char == "{":
            selector = "".join(prelude).strip()
            if selector and not selector.startswith("@"):
                position = 0
                while position < len(selector):
                    char = selector[position]
                    if char == "\\":
                        # Skip an escaped character so an escaped dot is never
                        # mistaken for a class-selector boundary.
                        position += 2
                        continue
                    if char == ".":
                        parsed = _read_css_identifier(selector, position + 1)
                        if parsed:
                            classes.add(parsed[0])
                            position = parsed[1]
                            continue
                    position += 1
            prelude.clear()
        elif char in ("}", ";"):
            prelude.clear()
        else:
            prelude.append(char)
    return classes


def audit_stylesheet(
    css: str,
    public_classes: set[str],
    *,
    public_tokens: set[str] | frozenset[str] = frozenset(),
) -> dict:
    """Compare declared names, not runtime styling or cascade compatibility."""
    external = extract_css_classes(css)
    # Only declaration positions inside CSS blocks count. A feature query
    # such as @supports (--syn-accent: red) does not set a CSS variable.
    masked = _mask_comments_and_strings(css)
    external_tokens = set()
    for segment in re.split(r"[{};]", masked):
        match = TOKEN_DECLARATION.match(segment)
        if match:
            external_tokens.add(match.group(1))
    return {
        "other_class_count": len(external),
        "exact_overlap": sorted(external & public_classes),
        "other_syn_classes": sorted(c for c in external if c.startswith("syn-")),
        "exact_token_overlap": sorted(external_tokens & public_tokens),
        "other_syn_tokens": sorted(external_tokens),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--css", action="append", required=True, type=Path,
                        help="Other framework/app CSS file; repeat for multiple files")
    parser.add_argument("--json", action="store_true", help="Write machine-readable report")
    parser.add_argument("--fail-on-overlap", action="store_true",
                        help="Exit 1 if any external selector matches a Syntyr class")
    args = parser.parse_args(argv)
    api = json.loads((ROOT / "metadata/syntyr-api.json").read_text(encoding="utf-8"))
    public_classes = {c["name"] for c in api["classes"]}
    public_tokens = {t["name"] for t in api["tokens"]}
    if not public_classes or any(not name.startswith("syn-") for name in public_classes):
        parser.error("Syntyr class inventory is empty or not entirely syn-prefixed")
    if not public_tokens or any(not name.startswith("--syn-") for name in public_tokens):
        parser.error("Syntyr token inventory is empty or not entirely --syn-prefixed")
    comparisons = []
    for path in args.css:
        data = audit_stylesheet(path.read_text(encoding="utf-8"), public_classes,
                                public_tokens=public_tokens)
        comparisons.append({"source": str(path), **data})
    result = {"syntyr_class_count": len(public_classes),
              "syntyr_token_count": len(public_tokens), "comparisons": comparisons,
              "limitations": "Exact selectors and custom property declarations only; "
                             "no compiler expansion, CSS resets, or specificity analysis."}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in comparisons:
            print(f"{item['source']}: {item['other_class_count']} classes, "
                  f"{len(item['exact_overlap'])} exact overlaps: "
                  f"{', '.join(item['exact_overlap']) or 'none'}; "
                  f"{len(item['exact_token_overlap'])} token overlaps: "
                  f"{', '.join(item['exact_token_overlap']) or 'none'}")
        print("Scope: literal selectors; inspect global styles and cascade separately.")
    return int(args.fail_on_overlap and any(
        x["exact_overlap"] or x["exact_token_overlap"] for x in comparisons
    ))


if __name__ == "__main__":
    sys.exit(main())
