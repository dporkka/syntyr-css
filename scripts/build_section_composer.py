"""Generate static, strictly source-owned section definitions for the Syntyr builder.

No browser-side arbitrary HTML import: every template comes from reviewed,
copyable block snippets. User project JSON only stores validated field values.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "metadata/section-composer.v1.json"


def build() -> bytes:
    manifest = json.loads((ROOT / "blocks/manifest.json").read_text(encoding="utf-8"))
    if manifest.get("version") != 1:
        raise ValueError("Unsupported block catalog version")
    sections = []
    seen = set()
    for block in manifest["blocks"]:
        ident = block["id"]
        if ident in seen:
            raise ValueError(f"Duplicate section: {ident}")
        seen.add(ident)
        source = (ROOT / "blocks/snippets" / f"{ident}.html").read_text(encoding="utf-8").strip()
        if any(danger in source.lower() for danger in ("<script", "<iframe", "javascript:", " onload=", " onerror=")):
            raise ValueError(f"Unsafe canonical HTML in {ident}")
        if len(source) > 30000:
            raise ValueError(f"Template exceeds the editor's safe size: {ident}")
        sections.append({
            "id": ident, "title": block["title"], "description": block["description"],
            "category": block["category"], "html": source,
            "required_stylesheets": ["syntyr." + module + ".css" for module in block["modules"]],
        })
    result = {
        "schema_version": 1,
        "source_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "runtime_requirement": "none",
        "source_of_truth": ["blocks/manifest.json", "blocks/snippets/*.html"],
        "sections": sections,
    }
    return (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> int:
    args = argparse.ArgumentParser()
    args.add_argument("--check", action="store_true")
    parsed = args.parse_args()
    expected = build()
    if parsed.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != expected:
            print("STALE", OUTPUT.relative_to(ROOT))
            return 1
        print("OK section composer:", len(json.loads(expected)["sections"]), "copy-owned sections")
        return 0
    OUTPUT.write_bytes(expected)
    print("WROTE", OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
