"""Read-only A2UI 1.0 basic-catalog subset; not a general protocol client."""

import json

from . import (
    MAX_BYTES, MAX_DEPTH, MAX_NODES, GenUIError, _invalid_constant,
    _pairs, _require, _text, render_json,
)

BASIC_CATALOG_ID = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"


def _identifier(value):
    _text(value, nonempty=True)
    _require(len(value) <= 128, "Identifier too long")
    return value


def _convert(component, visit):
    kind = component.get("component")
    props = {key: value for key, value in component.items()
             if key not in ("id", "component")}
    if kind == "Column":
        _require(set(props) == {"children"}, "Unsupported Column properties")
        children = props["children"]
        _require(type(children) is list and 1 <= len(children) <= MAX_NODES,
                 "Invalid fixed child list")
        return {"type": "Stack", "children": [visit(child) for child in children]}
    if kind == "Card":
        _require(set(props) == {"child"}, "Unsupported Card properties")
        return {"type": "Panel", "children": [visit(props["child"])]}
    if kind == "Text":
        _require(set(props) <= {"text", "variant"} and "text" in props
                 and props.get("variant", "body") == "body", "Unsupported Text properties")
        _text(props["text"])
        return {"type": "Text", "props": {"text": props["text"]}}
    if kind == "Divider":
        _require(set(props) <= {"axis"} and props.get("axis", "horizontal") == "horizontal",
                 "Unsupported Divider properties")
        return {"type": "Divider"}
    raise GenUIError("Unsupported A2UI component")


def render_a2ui(document: str) -> str:
    """Render a complete, single-surface createSurface message atomically."""
    _require(type(document) is str and len(document) <= MAX_BYTES, "Invalid document size")
    try:
        _require(len(document.encode("utf-8")) <= MAX_BYTES, "Invalid document size")
        message = json.loads(document, object_pairs_hook=_pairs, parse_constant=_invalid_constant)
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise GenUIError("Invalid A2UI JSON") from exc

    _require(type(message) is dict and set(message) == {"version", "createSurface"}
             and message["version"] == "1.0", "Expected A2UI 1.0 createSurface")
    surface = message["createSurface"]
    _require(type(surface) is dict and set(surface) == {"surfaceId", "catalogId", "components"},
             "Unsupported surface properties")
    _identifier(surface["surfaceId"])
    _require(surface["catalogId"] == BASIC_CATALOG_ID, "Unsupported catalog")
    components = surface["components"]
    _require(type(components) is list and 1 <= len(components) <= MAX_NODES,
             "Invalid component list")
    by_id = {}
    for component in components:
        _require(type(component) is dict and "id" in component, "Invalid component")
        key = _identifier(component["id"])
        _require(key not in by_id, "Duplicate component ID")
        by_id[key] = component

    seen = set()

    def expand(key, depth=1):
        _identifier(key)
        _require(depth <= MAX_DEPTH, "Component depth exceeded")
        _require(key in by_id, "Missing component reference")
        _require(key not in seen, "Cycle or reused component")
        seen.add(key)
        return _convert(by_id[key], lambda child: expand(child, depth + 1))

    root = expand("root")
    _require(len(seen) == len(by_id), "Unreachable component")
    # All values pass through the existing presentation validator and escaping.
    return render_json(json.dumps({"version": 1, "root": root}, ensure_ascii=False))
