"""Convert optional Keystatic/Payload homepage documents into Syntyr CMS v1 JSON.

Build-time-only, standard library. The portable renderer is authoritative:
unknown fields, unsafe URLs, duplicated IDs and unsupported blocks fail closed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

if __package__:
    from .render_cms_starter import SECTION_FIELDS, validate_document
else:
    from render_cms_starter import SECTION_FIELDS, validate_document


ROOT_FIELDS = frozenset(("title", "description", "theme", "sections"))
PAYLOAD_METADATA = frozenset(("id", "createdAt", "updatedAt", "_status"))
PAYLOAD_BLOCK_METADATA = frozenset(("id", "blockName"))
NESTED_FIELDS = {
    "features": ("items", {"title", "description"}),
    "faq": ("items", {"question", "answer"}),
    "pricing": ("plans", {"name", "price", "features", "button"}),
}


def _only_keys(value: object, allowed: frozenset | set, path: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    extra = value.keys() - allowed
    if extra:
        raise ValueError(f"{path}: unexpected fields {sorted(extra)}")
    return value


def _payload_nested(section: dict, kind: str) -> None:
    """Payload arrays carry database row IDs, which must not enter portable JSON."""
    if kind not in NESTED_FIELDS:
        return
    field, allowed = NESTED_FIELDS[kind]
    raw = section.get(field)
    if not isinstance(raw, list):
        raise ValueError(f"{kind}.{field}: expected an array")
    cleaned = []
    for index, item in enumerate(raw):
        value = _only_keys(item, allowed | {"id"}, f"{kind}.{field}[{index}]")
        cleaned.append({key: val for key, val in value.items() if key != "id"})
    section[field] = cleaned
    if kind == "pricing":
        for i, plan in enumerate(cleaned):
            benefits = plan.get("features")
            if not isinstance(benefits, list):
                raise ValueError(f"pricing.plans[{i}].features: expected an array")
            normalized = []
            for j, benefit in enumerate(benefits):
                row = _only_keys(
                    benefit, {"feature", "id"}, f"pricing.plans[{i}].features[{j}]",
                )
                if "feature" not in row:
                    raise ValueError(f"pricing.plans[{i}].features[{j}]: missing feature")
                normalized.append(row["feature"])
            plan["features"] = normalized


def _keystatic_section(value: object, index: int) -> dict:
    item = _only_keys(value, {"discriminant", "value"}, f"sections[{index}]")
    kind = item.get("discriminant")
    if not isinstance(kind, str) or kind not in SECTION_FIELDS:
        raise ValueError(f"sections[{index}]: unknown Keystatic block type")
    data = _only_keys(item.get("value"), SECTION_FIELDS[kind] - {"type"}, f"sections[{index}].value")
    return {"type": kind, **data}


def _payload_section(value: object, index: int) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"sections[{index}]: expected object")
    kind = value.get("blockType")
    if not isinstance(kind, str) or kind not in SECTION_FIELDS:
        raise ValueError(f"sections[{index}]: unknown Payload block type")
    fields = SECTION_FIELDS[kind] - {"type", "id"}
    _only_keys(
        value, fields | {"blockType", "sectionId"} | PAYLOAD_BLOCK_METADATA,
        f"sections[{index}]",
    )
    section = {key: val for key, val in value.items() if key in fields}
    if "sectionId" not in value:
        raise ValueError(f"sections[{index}]: missing stable sectionId")
    section.update({"type": kind, "id": value["sectionId"]})
    _payload_nested(section, kind)
    return section


def convert(adapter: str, document: object) -> dict:
    if adapter not in ("keystatic", "payload"):
        raise ValueError("adapter must be keystatic or payload")
    allowed = ROOT_FIELDS | (PAYLOAD_METADATA if adapter == "payload" else frozenset())
    data = _only_keys(document, allowed, "page")
    if not isinstance(data.get("sections"), list):
        raise ValueError("page.sections: expected array")
    normalize = _keystatic_section if adapter == "keystatic" else _payload_section
    page = {key: data[key] for key in ("title", "description", "theme") if key in data}
    page["sections"] = [normalize(block, index) for index, block in enumerate(data["sections"])]
    return validate_document(page)


def export(adapter: str, source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output paths must differ")
    content = json.loads(source.read_text(encoding="utf-8"))
    validated = convert(adapter, content)  # No filesystem mutation before validation.
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent,
            prefix=".syntyr-cms-", suffix=".json.tmp", delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)
            json.dump(validated, tmp, ensure_ascii=False, indent=2)
            tmp.write("\n")
        os.replace(tmp_path, destination)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("adapter", choices=("keystatic", "payload"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        export(args.adapter, args.input, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(2, f"CMS export rejected: {error}\n")
    print(f"Validated {args.adapter} document => {args.output}")
