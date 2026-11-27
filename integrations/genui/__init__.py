"""Experimental, read-only HTML renderer. No application behavior or CSS changes."""
import json
from html import escape
from pathlib import Path

MAX_BYTES = 262_144
MAX_DEPTH = 12
MAX_NODES = 256
MAX_TEXT = 4000
MAX_ITEMS = 100
MAX_COLUMNS = 20
MAX_NUMBER = 1_000_000_000
_CATALOG = json.loads(Path(__file__).with_name("catalog.json").read_text(encoding="utf-8"))
_COMPONENTS = _CATALOG["components"]


class GenUIError(ValueError):
    """The untrusted document does not satisfy the supported contract."""


def _require(condition, message):
    if not condition:
        raise GenUIError(message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(_):
    raise GenUIError("Non-finite JSON number")


def _text(value, nonempty=False):
    _require(type(value) is str and len(value) <= MAX_TEXT, "Invalid text")
    _require(not nonempty or bool(value.strip()), "Empty label")
    _require(all(not (0xD800 <= ord(c) <= 0xDFFF or
                      (ord(c) < 32 and c not in "\t\n\r"))
                 for c in value), "Invalid text character")


def _strings(value, labels=False, limit=MAX_ITEMS):
    _require(type(value) is list and 1 <= len(value) <= limit, "Invalid string list")
    for item in value:
        _text(item, labels)


def _prop(value, kind):
    if kind in ("text", "label"):
        _text(value, kind == "label")
    elif kind in ("heading", "integer"):
        low, high = (1, 6) if kind == "heading" else (0, MAX_NUMBER)
        _require(type(value) is int and low <= value <= high, "Invalid integer")
    elif kind in ("strings", "labels"):
        _strings(value, kind == "labels", MAX_COLUMNS if kind == "labels" else MAX_ITEMS)
    elif kind == "rows":
        _require(type(value) is list and len(value) <= MAX_ITEMS, "Invalid table rows")
        for row in value:
            _strings(row, limit=MAX_COLUMNS)
    else:
        raise GenUIError("Unsupported catalog property")


def _validate(node, depth, budget):
    _require(depth <= MAX_DEPTH and budget[0] > 0, "Component limit exceeded")
    budget[0] -= 1
    _require(type(node) is dict and set(node) <= {"type", "props", "children"}, "Invalid node")
    kind = node.get("type")
    _require(type(kind) is str and kind in _COMPONENTS, "Unknown component")
    contract = _COMPONENTS[kind]
    props = node.get("props", {})
    _require(type(props) is dict and props.keys() == contract["props"].keys(), "Invalid properties")
    for name, prop_kind in contract["props"].items():
        _prop(props[name], prop_kind)
    if kind == "Progress":
        _require(0 <= props["value"] <= props["max"] and props["max"] > 0, "Invalid progress range")
    if kind == "Table":
        _require(all(len(row) == len(props["columns"]) for row in props["rows"]), "Invalid row width")
    if contract["children"]:
        children = node.get("children")
        _require(type(children) is list and 1 <= len(children) <= MAX_NODES, "Invalid children")
        for child in children:
            _validate(child, depth + 1, budget)
    else:
        _require("children" not in node, "Leaf component cannot have children")


def _render(node):
    kind = node["type"]
    p = node.get("props", {})
    if kind in ("Panel", "Stack", "Grid", "Details"):
        children = "".join(_render(child) for child in node["children"])
        if kind == "Details":
            return f'<details><summary>{escape(p["summary"])}</summary>{children}</details>'
        tag, css = {"Panel": ("div", "syn-panel"), "Stack": ("div", "syn-stack"),
                    "Grid": ("div", "syn-grid")}[kind]
        return f'<{tag} class="{css}">{children}</{tag}>'
    if kind == "Heading":
        level = p["level"]
        return f'<h{level} class="syn-heading">{escape(p["text"])}</h{level}>'
    if kind == "Text":
        return f'<p>{escape(p["text"])}</p>'
    if kind == "Badge":
        return f'<span class="syn-badge">{escape(p["text"])}</span>'
    if kind == "Metric":
        return (f'<dl class="syn-stat"><dt class="syn-stat-label">{escape(p["label"])}</dt>'
                f'<dd class="syn-stat-value">{escape(p["value"])}</dd></dl>')
    if kind == "List":
        return '<ul class="syn-list">' + "".join(f'<li>{escape(item)}</li>' for item in p["items"]) + '</ul>'
    if kind == "Table":
        columns = "".join(f'<th scope="col">{escape(col)}</th>' for col in p["columns"])
        rows = "".join("<tr>" + "".join(f'<td>{escape(cell)}</td>' for cell in row) + "</tr>" for row in p["rows"])
        return (f'<div class="syn-table-wrap" tabindex="0" role="region" aria-label="{escape(p["caption"])}">'
                f'<table class="syn-table"><caption>{escape(p["caption"])}</caption>'
                f'<thead><tr>{columns}</tr></thead><tbody>{rows}</tbody></table></div>')
    if kind == "Progress":
        return (f'<label>{escape(p["label"])} '
                f'<progress value="{p["value"]}" max="{p["max"]}">{p["value"]}/{p["max"]}</progress>'
                f' <span>{p["value"]}/{p["max"]}</span></label>')
    if kind == "Divider":
        return "<hr>"
    raise GenUIError("Unsupported component")


def render_json(document: str) -> str:
    """Validate a bounded JSON document, then return a scoped HTML fragment."""
    _require(type(document) is str and len(document) <= MAX_BYTES, "Invalid document size")
    try:
        _require(len(document.encode("utf-8")) <= MAX_BYTES, "Invalid document size")
        spec = json.loads(document, object_pairs_hook=_pairs, parse_constant=_invalid_constant)
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise GenUIError("Invalid JSON document") from exc
    _require(type(spec) is dict and spec.keys() == {"version", "root"}, "Invalid envelope")
    _require(type(spec["version"]) is int and spec["version"] == _CATALOG["version"], "Unsupported version")
    _validate(spec["root"], 1, [MAX_NODES])
    return '<div class="syn-root">' + _render(spec["root"]) + '</div>'
