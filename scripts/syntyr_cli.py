#!/usr/bin/env python3
"""Optional read-only Syntyr CLI; CSS consumers need none of this tooling.

Run from a source checkout. Validation commands preserve the canonical
parsers and exit statuses; discovery reads the version-aware catalog.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_mcp.catalog import MAX_RESULTS, PUBLISHED, RELEASES, SyntyrCatalog  # noqa: E402
from scripts import contract_diff, syntyr_agent, syntyr_check  # noqa: E402


def _catalog_command(options) -> int:
    try:
        catalog = SyntyrCatalog()
        if options.command == "search":
            report = catalog.search_components(options.query, options.release)
        elif options.name.startswith(("syn-", "--syn-")):
            report = catalog.lookup_api(options.name, options.release)
        else:
            report = catalog.get_component(options.name, options.release)
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"syntyr {options.command}: {exc}", file=sys.stderr)
        return 2

    if options.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"SYNTYR {options.command.upper()} — {report['release']} ({report['release_status']})")
    if options.command == "search":
        for item in report["components"]:
            print(f"{item['name']} — {', '.join(item['stylesheets'])}")
        if not report["components"]:
            print("No matching curated components.")
        print(f"At most {MAX_RESULTS} results.")
    elif "component" in report:
        item = report["component"]
        print(f"NAME: {item['name']}")
        print(f"ELEMENTS: {', '.join(item['elements'])}")
        print(f"CLASSES: {', '.join(item['classes'])}")
        print(f"STYLESHEETS: {', '.join(item['stylesheets'])}")
        print(f"NOTES: {item['notes']}")
    else:
        item = report["entry"]
        print(f"NAME: {item['name']} ({item['kind']})")
        print(f"STYLESHEET: {item['stylesheet']}")
        print(f"DESCRIPTION: {item['description']}")
    if report.get("note"):
        print(report["note"])
    return 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    delegates = {
        "check": (syntyr_check.main, [], "Validate literal HTML (source contract by default)"),
        "diff": (contract_diff.main, [], "Compare two public CSS contracts"),
        "info": (syntyr_agent.main, ["info"], "Inspect a pinned consumer installation"),
        "project-check": (syntyr_agent.main, ["check"], "Validate a pinned consumer project"),
    }
    if args and args[0] in delegates:
        handler, prefix, _ = delegates[args[0]]
        return handler([*prefix, *args[1:]])

    parser = argparse.ArgumentParser(prog="syntyr", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    version = sub.add_parser("version", help="Show source and published release versions")
    version.add_argument("--format", choices=("text", "json"), default="text")
    search = sub.add_parser("search", help="Search the curated release-aware component catalog")
    search.add_argument("query", nargs="?", default="")
    manual = sub.add_parser("man", help="Read a component, selector or token reference")
    manual.add_argument("name", help="Component name, class or token (use -- before --syn-* tokens)")
    for command in (search, manual):
        command.add_argument("--release", choices=RELEASES, default=PUBLISHED)
        command.add_argument("--format", choices=("text", "json"), default="text")
    for name, (_, _, help_text) in delegates.items():
        sub.add_parser(name, help=help_text)
    options = parser.parse_args(args)
    if options.command in ("search", "man"):
        return _catalog_command(options)
    if options.command == "version":
        try:
            source = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as exc:
            print(f"syntyr version: {exc}", file=sys.stderr)
            return 2
        if options.format == "json":
            print(json.dumps({"source_version": source, "published_version": PUBLISHED},
                             sort_keys=True))
        else:
            print(f"Source: {source}\nPublished: {PUBLISHED}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
