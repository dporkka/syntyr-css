"""Offline design inspection of canonical Syntyr CSS and curated examples.

Token edges are possible static references across scopes and fallback branches,
not computed browser dependencies. Variant evidence is illustrative, not a
compatibility matrix of all possible class combinations.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re

if __package__:
    from .build import all_distributions
    from .design_reference_audit import CSS_NON_CODE
else:
    from build import all_distributions
    from design_reference_audit import CSS_NON_CODE

ROOT = Path(__file__).resolve().parents[1]
DECL = re.compile(r"(?:^|(?<=[;{]))\s*(--syn-[\w-]+)\s*:\s*([^;{}]*)")
REF = re.compile(r"(?<![\w-])var\(\s*(--syn-[\w-]+)(?=\s*[,\)])")


def token_graph(sources):
    graph = {}

    def node(name):
        return graph.setdefault(name, {"declared_in": set(), "referenced_in": set(),
                                       "depends_on": set()})

    for path, css in sorted(sources.items()):
        code = CSS_NON_CODE.sub(" ", css)
        for name in REF.findall(code):
            node(name)["referenced_in"].add(path)
        for name, value in DECL.findall(code):
            entry = node(name)
            entry["declared_in"].add(path)
            entry["depends_on"].update(REF.findall(value))
    return graph


def source_graph():
    paths = sorted({path for modules in all_distributions().values() for path in modules})
    return token_graph({"src/" + path: (ROOT / "src" / path).read_text(encoding="utf-8")
                        for path in paths})


def token_report(graph, name):
    if name not in graph:
        raise ValueError(f"Unknown source token: {name}")
    seen = {name}
    pending = list(graph[name]["depends_on"])
    while pending:
        target = pending.pop()
        if target not in seen:
            seen.add(target)
            pending.extend(graph[target]["depends_on"])
    return {"token": name,
            **{key: sorted(value) for key, value in graph[name].items()},
            "referenced_by_tokens": sorted(key for key, value in graph.items()
                                           if name in value["depends_on"]),
            "transitive_dependencies": sorted(seen - {name})}


class ElementClasses(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "class" and value:
                self.elements.append(set(value.split()))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def variant_matrix(components, examples):
    evidence = {}
    for example in examples:
        parser = ElementClasses()
        parser.feed(example["html"])
        evidence[example["id"]] = parser.elements

    families = []
    for component in components:
        classes = component["classes"]
        for base in classes:
            modifiers = [name for name in classes if name.startswith(base + "--")]
            if not modifiers:
                continue
            families.append({
                "component": component["name"],
                "base_class": base,
                "module": component["module"],
                "elements": component["elements"],
                "guidance": component["notes"],
                "variants": [
                    {"class": modifier, "example_ids": sorted(
                        key for key, elements in evidence.items()
                        if any({base, modifier} <= el for el in elements))}
                    for modifier in modifiers
                ],
            })
    return families


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    token = commands.add_parser("token", help="inspect static token references")
    token.add_argument("name", help="CSS variable (precede with --)")
    commands.add_parser("variants", help="list curated modifiers and example evidence")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if args.command == "token":
        try:
            result = token_report(source_graph(), args.name)
        except ValueError as exc:
            parser.error(str(exc))
        result["scope"] = "Possible source references; not browser-computed dependencies."
    else:
        manifest = json.loads((ROOT / "metadata/component-gallery.v1.json").read_text(encoding="utf-8"))
        if manifest["source_version"] != version:
            parser.error("Stale gallery source version")
        result = {"families": variant_matrix(manifest["components"], manifest["examples"]),
                  "scope": "Curated modifiers and same-element examples; not exhaustive or a compatibility guarantee."}
    result["source_version"] = version
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
