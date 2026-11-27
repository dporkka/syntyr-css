"""Restricted object/string data models and absolute JSON Pointer bindings."""
import re
from copy import deepcopy

from . import MAX_DEPTH, _require, _text

MAX_MODEL_KEYS = 1024
_RESERVED = {"__proto__", "prototype", "constructor"}


def _key(key):
    _text(key, nonempty=True)
    _require(len(key) <= 128 and key not in _RESERVED, "Invalid model key")


def validate_model(model):
    _require(type(model) is dict, "Model must be an object")
    remaining = MAX_MODEL_KEYS

    def walk(value, depth):
        nonlocal remaining
        _require(depth <= MAX_DEPTH, "Model depth exceeded")
        if type(value) is str:
            _text(value)
            return
        _require(type(value) is dict, "Model supports objects and strings only")
        for key, child in value.items():
            remaining -= 1
            _require(remaining >= 0, "Model key limit exceeded")
            _key(key)
            walk(child, depth + 1)

    walk(model, 0)


def _tokens(path):
    _text(path)
    _require(path.startswith("/") and path != "/", "Expected absolute non-root pointer")
    parts = path[1:].split("/")
    _require(len(parts) <= MAX_DEPTH, "Pointer depth exceeded")
    result = []
    for part in parts:
        _require(not re.search(r"~(?![01])", part), "Invalid pointer escape")
        key = part.replace("~1", "/").replace("~0", "~")
        _key(key)
        result.append(key)
    return result


def _lookup(model, parts):
    value = model
    for part in parts:
        _require(type(value) is dict and part in value, "Missing model path")
        value = value[part]
    return value


def resolve_components(components, model):
    result = []
    for component in components:
        record = component.copy()
        if record.get("component") == "Text" and type(record.get("text")) is dict:
            binding = record["text"]
            _require(set(binding) == {"@path"}, "Unsupported text binding")
            value = _lookup(model, _tokens(binding["@path"]))
            _text(value)
            record["text"] = value
        result.append(record)
    return result


def update_model(model, path, value):
    if path == "/":
        validate_model(value)
        return value
    parts = _tokens(path)
    proposed = deepcopy(model)
    parent = _lookup(proposed, parts[:-1])
    _require(type(parent) is dict, "Model parent must be an object")
    if value is None:
        _require(parts[-1] in parent, "Missing model path")
        del parent[parts[-1]]
    else:
        parent[parts[-1]] = value
    validate_model(proposed)
    return proposed
