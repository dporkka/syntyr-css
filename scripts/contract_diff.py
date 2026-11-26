#!/usr/bin/env python3
"""Compare generated Syntyr public API inventories across pinned source revisions.

No network access or dependencies. This checks names and stylesheet availability,
not visual/behavioral compatibility; browser and accessibility gates remain required.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def _strings(value: object, label: str) -> set[str]:
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        raise ValueError(f"{label} must be a list of nonempty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{label} contains duplicate values")
    return set(value)


def _items(contract: dict[str, Any], field: str) -> dict[str, set[str]]:
    records = contract.get(field)
    if not isinstance(records, list):
        raise ValueError(f"{field} must be a list of named entries")
    output: dict[str, set[str]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("name"), str) or not record["name"]:
            raise ValueError(f"{field} entries must have a nonempty name")
        name = record["name"]
        if name in output:
            raise ValueError(f"{field} contains duplicate name {name}")
        output[name] = _strings(record.get("stylesheets"), f"{field}.{name}.stylesheets")
    return output


def _validate(contract: object) -> dict[str, Any]:
    if not isinstance(contract, dict) or type(contract.get("schema_version")) is not int or contract["schema_version"] != 1:
        raise ValueError("Unsupported or missing schema_version (expected 1)")
    if not isinstance(contract.get("source_version"), str) or not contract["source_version"]:
        raise ValueError("source_version must be a nonempty string")
    for field in ("stylesheets", "themes"):
        _strings(contract.get(field), field)
    declared = set(contract["stylesheets"])
    for field in ("classes", "tokens"):
        for name, providers in _items(contract, field).items():
            unknown = providers - declared
            if unknown:
                raise ValueError(
                    f"{field}.{name}.stylesheets references undeclared stylesheets: "
                    + ", ".join(sorted(unknown))
                )
    attributes = contract.get("attributes")
    if not isinstance(attributes, dict) or any(not isinstance(name, str) or not name for name in attributes):
        raise ValueError("attributes must be a mapping of names to lists")
    for name, values in attributes.items():
        _strings(values, f"attributes.{name}")
    return contract


def _delta(old: set[str], new: set[str]) -> dict[str, list[str]]:
    return {"added": sorted(new - old), "removed": sorted(old - new)}


def _stylesheet_removals(old: dict[str, set[str]], new: dict[str, set[str]]) -> list[dict[str, Any]]:
    return [{"name": name, "stylesheets": sorted(old[name] - new[name])}
            for name in sorted(old.keys() & new.keys()) if old[name] - new[name]]


def compare_contracts(before: object, after: object) -> dict[str, Any]:
    """Return a deterministic summary; never silently accept malformed contracts."""
    old, new = _validate(before), _validate(after)
    old_classes, new_classes = _items(old, "classes"), _items(new, "classes")
    old_tokens, new_tokens = _items(old, "tokens"), _items(new, "tokens")
    attr_changes = {
        name: _delta(set(old["attributes"].get(name, [])), set(new["attributes"].get(name, [])))
        for name in sorted(old["attributes"].keys() | new["attributes"].keys())
        if set(old["attributes"].get(name, [])) != set(new["attributes"].get(name, []))
    }
    changes = {
        "classes": _delta(set(old_classes), set(new_classes)),
        "tokens": _delta(set(old_tokens), set(new_tokens)),
        "themes": _delta(set(old["themes"]), set(new["themes"])),
        "stylesheets": _delta(set(old["stylesheets"]), set(new["stylesheets"])),
        "attributes": attr_changes,
        "class_stylesheet_removals": _stylesheet_removals(old_classes, new_classes),
        "token_stylesheet_removals": _stylesheet_removals(old_tokens, new_tokens),
    }
    breaking = (
        any(changes[field]["removed"] for field in ("classes", "tokens", "themes", "stylesheets"))
        or any(delta["removed"] for delta in attr_changes.values())
        or bool(changes["class_stylesheet_removals"] or changes["token_stylesheet_removals"])
    )
    return {
        "schema_version": 1,
        "source_versions": {"old": old["source_version"], "new": new["source_version"]},
        "breaking": bool(breaking),
        "changes": changes,
        "limitations": "Name/export-availability diff only; does not check CSS cascade, visual behavior or accessibility.",
    }


def _human(report: dict[str, Any]) -> str:
    versions = report["source_versions"]
    lines = [f"Syntyr CSS contract: {versions['old']} -> {versions['new']}",
             f"Potentially breaking public API removals: {'YES' if report['breaking'] else 'no'}"]
    changes = report["changes"]
    for field in ("classes", "tokens", "themes", "stylesheets"):
        change = changes[field]
        if change["added"] or change["removed"]:
            lines.append(f"{field}: +{', '.join(change['added']) or 'none'}; -{', '.join(change['removed']) or 'none'}")
    for name, change in changes["attributes"].items():
        lines.append(f"{name}: +{', '.join(change['added']) or 'none'}; -{', '.join(change['removed']) or 'none'}")
    for kind in ("class", "token"):
        for entry in changes[f"{kind}_stylesheet_removals"]:
            lines.append(f"{kind} {entry['name']} no longer in: {', '.join(entry['stylesheets'])}")
    lines.append(report["limitations"])
    return "\n".join(lines)


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, value in pairs:
        if key in values:
            raise ValueError(f"duplicate JSON object key: {key}")
        values[key] = value
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path, help="Old metadata/syntyr-contract.json (or - for stdin)")
    parser.add_argument("after", type=Path, help="New metadata/syntyr-contract.json (or - for stdin)")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON report")
    parser.add_argument("--fail-on-breaking", action="store_true", help="Exit 1 on potential public API removals")
    args = parser.parse_args(argv)
    def read_manifest(path: Path) -> object:
        source = sys.stdin.read() if path == Path("-") else path.read_text(encoding="utf-8")
        return json.loads(source, object_pairs_hook=_reject_duplicate_json_keys)

    try:
        if args.before == args.after == Path("-"):
            raise ValueError("Only one manifest may be read from stdin")
        before = read_manifest(args.before)
        after = read_manifest(args.after)
        report = compare_contracts(before, after)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"Cannot compare Syntyr CSS contracts: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.json else _human(report))
    return 1 if args.fail_on_breaking and report["breaking"] else 0


if __name__ == "__main__":
    sys.exit(main())
