#!/usr/bin/env python3
"""Optional read-only Syntyr CLI; CSS consumers need none of this tooling.

Run from a source checkout. Each command delegates to the canonical tool,
including its own argument parser, output format, and exit status.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_mcp.catalog import PUBLISHED  # noqa: E402
from scripts import contract_diff, syntyr_agent, syntyr_check  # noqa: E402


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
    for name, (_, _, help_text) in delegates.items():
        sub.add_parser(name, help=help_text)
    options = parser.parse_args(args)
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
