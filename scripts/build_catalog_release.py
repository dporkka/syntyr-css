"""Audit catalog examples against immutable published CSS (no package install).

Selector coverage is conservative evidence of stylesheet support, NOT proof of
visual equivalence, browser support or accessible interactive behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_component_gallery import build_manifest
PINNED = "0.3.0-alpha.4"
SOURCE = "0.3.0-alpha.5"
FROZEN_DIR = ROOT / "site-releases" / PINNED
OUTPUT = ROOT / "metadata/catalog-release-compatibility.v1.json"
CATALOG = ROOT / "docs/catalog.html"
CARD = re.compile(r'(<article class="catalog-card syn-panel")(?P<attrs>[^>]*)(>)')
LABEL = re.compile(r'data-catalog-alpha4="(?:true|false)"')
STYLE_CLASS = re.compile(r'(?<![\w-])\.([A-Za-z_][\w-]*)')
CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)


def frozen_stylesheet_classes() -> dict[str, set[str]]:
    manifest = json.loads((ROOT / "site-releases/manifest.json").read_text(encoding="utf-8"))
    expected = manifest[PINNED]
    actual = {}
    for name, checksum in expected.items():
        path = FROZEN_DIR / name
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != checksum:
            raise ValueError(f"Immutable published CSS checksum mismatch: {name}")
        actual[name] = set(STYLE_CLASS.findall(CSS_COMMENT.sub("", content.decode("utf-8"))))
    return actual


def build_release_matrix() -> dict:
    published = frozen_stylesheet_classes()
    examples = []
    for item in build_manifest()["examples"]:
        missing_stylesheets = sorted(set(item["required_stylesheets"]) - published.keys())
        covered_classes = set().union(*(published[name] for name in item["required_stylesheets"] if name in published))
        missing_classes = sorted(set(item["classes"]) - covered_classes)
        eligible = not (missing_stylesheets or missing_classes)
        examples.append({
            "id": item["id"],
            "published_css_covered": eligible,
            "missing_stylesheets": missing_stylesheets,
            "missing_classes": missing_classes,
        })
    return {
        "schema_version": 1,
        "published_release": PINNED,
        "source_candidate": SOURCE,
        "method": "Conservative frozen alpha.4 stylesheet and CSS class-selector coverage; not visual or behavioral certification.",
        "examples": examples,
    }


def render_release_matrix(matrix: dict) -> str:
    return json.dumps(matrix, indent=2, ensure_ascii=False) + "\n"


def annotate_catalog(source: str, matrix: dict) -> str:
    by_id = {row["id"]: row for row in matrix["examples"]}
    seen = set()

    def annotate(match: re.Match) -> str:
        attrs = match.group("attrs")
        identifier = re.search(r'aria-labelledby="([^"]+)"', attrs)
        if not identifier or identifier.group(1) not in by_id:
            raise ValueError("Catalog card missing known aria-labelledby ID")
        identifier = identifier.group(1)
        if identifier in seen:
            raise ValueError(f"Duplicate catalog card: {identifier}")
        seen.add(identifier)
        attrs = LABEL.sub("", attrs)
        attrs = re.sub(r' {2,}', ' ', attrs)
        coverage = "true" if by_id[identifier]["published_css_covered"] else "false"
        return f'{match.group(1)} data-catalog-alpha4="{coverage}"{attrs}{match.group(3)}'

    annotated = CARD.sub(annotate, source)
    if seen != by_id.keys():
        raise ValueError(f"Catalog IDs differ from compatibility matrix: {sorted(by_id.keys()-seen)}")
    return annotated


def verify_catalog_annotations(matrix: dict) -> bool:
    content = CATALOG.read_text(encoding="utf-8")
    return content == annotate_catalog(content, matrix)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    matrix = build_release_matrix()
    expected = render_release_matrix(matrix)
    source = CATALOG.read_text(encoding="utf-8")
    annotated = annotate_catalog(source, matrix)
    if args.check:
        ok = OUTPUT.is_file() and OUTPUT.read_text(encoding="utf-8") == expected and source == annotated
        if not ok:
            print("Stale catalog release compatibility matrix/annotations; regenerate it")
        else:
            print(f"OK {len(matrix['examples'])} catalog examples against immutable {PINNED} CSS")
        return 0 if ok else 1
    OUTPUT.write_text(expected, encoding="utf-8")
    if annotated != source:
        CATALOG.write_text(annotated, encoding="utf-8")
    print(f"Updated {len(matrix['examples'])} catalog examples and frozen CSS coverage matrix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
