"""Run existing browser coverage for candidate interaction contracts.

Optional maintainer tooling. No dependencies are installed by this command.
A passing suite is evidence for the named scenarios, not WCAG certification.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

# Explicit allowlist: neither the manifest nor user input can supply commands.
GROUPS = (
    ("native", ("dialog", "disclosure"), ".", "tests/native_interactions_browser.py",
     (sys.executable, "tests/native_interactions_browser.py")),
    ("dropdown", ("dropdown",), ".", "tests/dropdown_browser.py",
     (sys.executable, "tests/dropdown_browser.py")),
    ("headless", ("combobox", "sortable-table"), "examples/headless-react",
     "examples/headless-react/tests/interactions.spec.ts",
     ("npm", "test", "--", "--workers=2", "--grep",
      "combobox filters and selects|sortable data grid")),
)


def plan(ids=None):
    known = {item for _, covered, *_ in GROUPS for item in covered}
    selected = known if ids is None else set(ids)
    if not selected:
        raise ValueError("Select at least one interaction contract")
    if selected - known:
        raise ValueError("Unknown interaction contract: " + ", ".join(sorted(selected - known)))
    return [
        {"suite": suite, "contracts": sorted(selected.intersection(covered)),
         "cwd": cwd, "test_file": test_file, "command": list(command)}
        for suite, covered, cwd, test_file, command in GROUPS
        if selected.intersection(covered)
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contracts", nargs="*", help="Omit to run all five contracts")
    parser.add_argument("--list", action="store_true", help="Show planned suites without executing")
    args = parser.parse_args()
    try:
        groups = plan(args.contracts or None)
    except ValueError as exc:
        parser.error(str(exc))
    failed = False
    for group in groups:
        print(f'{group["suite"]}: {", ".join(group["contracts"])} ({group["test_file"]})', flush=True)
        if not args.list:
            try:
                result = subprocess.run(group["command"], cwd=ROOT / group["cwd"], check=False)
                failed |= result.returncode != 0
            except OSError as exc:
                print(f"Cannot launch {group['suite']}: {exc}", file=sys.stderr)
                failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
