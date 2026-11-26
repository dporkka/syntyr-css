"""Create a developer-only manual contrast review CSV from an axe/triage pair.

A reinspection may replace flagged observations, never a human verdict. The
queue records the source commits from both triage reports; reviewers must
verify that the audited rendering and styles match the candidate under review.
"""
import argparse
import csv
import json
from pathlib import Path

from contrast_pixel_triage import REINSPECT_STATUSES as FLAGGED
STATUSES = FLAGGED | {"sampled_above_threshold", "computed_placeholder_above_threshold", "non_text"}


def target_key(item):
    return item["page"], tuple(item["selector"]), item["failure_summary"]


def observation_index(report, known, widths):
    indexed = {}
    for item in report["observations"]:
        key = target_key(item), item["viewport_width"]
        if key[0] not in known or key[1] not in widths:
            raise ValueError(f"Observation outside audit or viewport scope: {key}")
        if key in indexed:
            raise ValueError(f"Duplicate observation: {key}")
        if item["status"] not in STATUSES:
            raise ValueError(f"Unknown observation status: {item['status']}")
        indexed[key] = item
    return indexed


def build_queue(axe, triage, reinspection=None):
    """Require complete, unique per-viewport evidence for every axe target."""
    known = {}
    for page in axe["pages"]:
        for item in page["incomplete"]:
            if item["rule"] != "color-contrast":
                continue
            key = target_key(dict(item, page=page["page"]))
            if key in known:
                raise ValueError(f"Duplicate axe target: {key}")
            known[key] = item
    widths = tuple(triage["viewport_widths"])
    if not widths or len(set(widths)) != len(widths) or any(
        not isinstance(width, int) or width <= 0 for width in widths
    ):
        raise ValueError("Expected unique positive viewport widths")
    original = observation_index(triage, known, widths)
    expected = {(key, width) for key in known for width in widths}
    if original.keys() != expected:
        raise ValueError(f"Incomplete triage: {len(expected - original.keys())} missing observations")

    updated = {}
    if reinspection is not None:
        if set(reinspection["viewport_widths"]) != set(widths):
            raise ValueError("Reinspection viewport scope differs from triage")
        updated = observation_index(reinspection, known, widths)
        for key, item in updated.items():
            prior = original[key]["status"]
            if prior not in FLAGGED or item.get("prior_status") != prior:
                raise ValueError(f"Reinspection does not match a flagged original: {key}")

    rows = []
    for key, item in known.items():
        current = [updated.get((key, width), original[key, width]) for width in widths]
        ratios = [(o["minimum_sampled_ratio"] - o["threshold"], o["minimum_sampled_ratio"],
                   o["threshold"], o["viewport_width"]) for o in current
                  if o.get("minimum_sampled_ratio") is not None and o.get("threshold") is not None]
        worst = min(ratios, default=None)
        status = {o["status"] for o in current}
        priority = "1_unresolved_sample" if status & FLAGGED else (
            "2_graphics_review" if "non_text" in status else "3_text_review")
        rows.append({
            "priority": priority,
            "page": key[0],
            "selector": json.dumps(key[1], ensure_ascii=False),
            "axe_reason": key[2],
            "audit_commit": triage.get("source_commit", ""),
            "reinspection_commit": reinspection.get("source_commit", "") if reinspection and any(
                (key, width) in updated for width in widths) else "",
            "observations": json.dumps({o["viewport_width"]: o["status"] for o in current}),
            "reinspected_widths": ",".join(str(w) for w in widths if (key, w) in updated),
            "minimum_margin": round(worst[0], 3) if worst else "",
            "sampled_ratio": worst[1] if worst else "",
            "sample_threshold": worst[2] if worst else "",
            "sample_width": worst[3] if worst else "",
            # A machine sample, even above threshold, cannot fill these fields.
            "review_status": "pending",
            "reviewer": "",
            "browser_theme_zoom_and_states": "",
            "manual_measurement_and_evidence": "",
            "review_notes": "",
        })
    return sorted(rows, key=lambda row: (row["priority"],
        float(row["minimum_margin"]) if row["minimum_margin"] != "" else float("inf"),
        row["page"], row["selector"]))


FIELDS = (
    "priority", "page", "selector", "axe_reason", "audit_commit", "reinspection_commit",
    "observations", "reinspected_widths", "minimum_margin", "sampled_ratio", "sample_threshold",
    "sample_width", "review_status", "reviewer", "browser_theme_zoom_and_states",
    "manual_measurement_and_evidence", "review_notes"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--axe-report", type=Path, required=True)
    parser.add_argument("--triage-report", type=Path, required=True)
    parser.add_argument("--reinspection-report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        rows = build_queue(load(args.axe_report), load(args.triage_report),
                           load(args.reinspection_report) if args.reinspection_report else None)
    except (KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    # Refuse overwriting a reviewer-edited record.
    with args.output.open("x", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} pending manual review targets written to {args.output}")


if __name__ == "__main__":
    main()
