#!/usr/bin/env python3
"""Summarize Syntyr design-partner research without publishing respondent details.

The seed CSV is public and intentionally empty of respondent identities. Use
--csv with a private, gitignored copy for actual research. This tool never
prints row-level content and never infers sales from expressed interest.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "business" / "design-partner-pilot.csv"
REQUIRED_FIELDS = {
    "slot", "target_segment", "status", "intent", "paid_commitment",
}
STATUSES = {"not_contacted", "invited", "accepted", "interviewed", "declined"}
INTENTS = {"", "would_buy", "maybe", "would_not_buy"}
COMMITMENTS = {"", "documented"}


def load_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV; reject missing research fields rather than invent results."""
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not REQUIRED_FIELDS.issubset(reader.fieldnames):
            missing = sorted(REQUIRED_FIELDS - set(reader.fieldnames or ()))
            raise ValueError(f"Tracker missing required columns: {', '.join(missing)}")
        return list(reader)


def summarize(rows: list[dict[str, str]]) -> dict[str, int | str]:
    """Validate the full cohort, then return *only* anonymous aggregate counts."""
    seen: set[str] = set()
    counts = {status: 0 for status in STATUSES}
    intents = {value: 0 for value in INTENTS}
    commitments = 0

    for index, item in enumerate(rows, start=1):
        slot = (item.get("slot") or "").strip()
        status = (item.get("status") or "").strip()
        intent = (item.get("intent") or "").strip()
        commitment = (item.get("paid_commitment") or "").strip()
        segment = (item.get("target_segment") or "").strip()

        if not slot or slot in seen:
            raise ValueError(f"Row {index}: missing or duplicate slot")
        seen.add(slot)
        if not segment:
            raise ValueError(f"Row {index}: target_segment is required")
        if status not in STATUSES:
            raise ValueError(f"Row {index}: unsupported status")
        if intent not in INTENTS:
            raise ValueError(f"Row {index}: unsupported purchase-intent value")
        if commitment not in COMMITMENTS:
            raise ValueError(f"Row {index}: paid_commitment must be blank or documented")
        if status != "interviewed" and intent:
            raise ValueError(f"Row {index}: intent requires a completed interview")
        if commitment and (status != "interviewed" or intent != "would_buy"):
            raise ValueError(
                f"Row {index}: documented commitment requires interviewed + would_buy"
            )

        counts[status] += 1
        if status == "interviewed":
            intents[intent] += 1
        commitments += int(commitment == "documented")

    completed = counts["interviewed"]
    return {
        "slots": len(rows),
        "invited_total": len(rows) - counts["not_contacted"],
        "accepted_or_interviewed": counts["accepted"] + completed,
        "interviews_completed": completed,
        "declined": counts["declined"],
        "would_buy": intents["would_buy"],
        "maybe": intents["maybe"],
        "would_not_buy": intents["would_not_buy"],
        "no_intent_recorded": intents[""],
        "documented_commitments": commitments,
        "purchase_evidence": "not_collected",
        "decision": (
            "review_commitments_and_launch_gates"
            if completed >= 10 else "needs_10_qualified_interviews"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV,
                        help="path to an anonymized or locally private tracker")
    parser.add_argument("--json", action="store_true",
                        help="print aggregate JSON for local reporting")
    args = parser.parse_args(argv)
    try:
        report = summarize(load_rows(args.csv))
    except (OSError, ValueError, csv.Error) as error:
        print(f"Invalid research tracker: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Syntyr Console Kit: design-partner evidence (not sales)")
        print(f"Invited/responded cohort: {report['invited_total']} / {report['slots']}")
        print(f"Qualified interviews completed: {report['interviews_completed']} / 10")
        print(
            f"Intent after interview: {report['would_buy']} would buy, "
            f"{report['maybe']} maybe, {report['would_not_buy']} would not buy"
        )
        print(f"Documented commitments (not purchases): {report['documented_commitments']}")
        print(f"Sales/revenue: not tracked or inferred; decision: {report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
