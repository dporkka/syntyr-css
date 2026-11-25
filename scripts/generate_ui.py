#!/usr/bin/env python3
"""Optional offline, fail-closed orchestration of the existing Syntyr tools."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_mcp.catalog import CANDIDATE, MAX_LOCAL_DOCUMENT_CHARS, CatalogError, SyntyrCatalog

MAX_INPUT = 256 * 1024
MAX_OUTPUT = 4 * 1024 * 1024
NOTE = ("Static presentation only. Host requirements remain unresolved implementation work. "
        "Validation is release-pinned markup checking, not a runtime or accessibility audit.")


# These are reviewed canonical section equivalents, not copied recipe source
# or a claim of full contract implementation. Keep this mapping narrow.
NATIVE_EQUIVALENTS = {
    ("combobox", "native-select", "fallback"): (
        "filter-toolbar", "Fixed-list native selection only; host owns search/filter submission."),
    ("sortable-table", "native-table", "fallback"): (
        "data-table", "Static example rows only; no live sorting or server data."),
    ("disclosure", "native-modal-dialog", "example"): (
        "faq", "Native details/summary disclosure only; no modal dialog."),
}


def _compose(request, *, plan=False):
    node = shutil.which("node")
    if not node:
        raise CatalogError("Optional Node.js authoring tool is required")
    payload = json.dumps(request, ensure_ascii=True).encode()
    if len(payload) > MAX_INPUT:
        raise CatalogError("Generation JSON exceeds 256 KiB")
    command = [node, str(ROOT / "scripts/compose.mjs")]
    if plan:
        command.append("--plan")
    try:
        result = subprocess.run(command, input=payload, capture_output=True, cwd=ROOT, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CatalogError("Local composer failed or timed out") from exc
    if result.returncode not in ((0, 2) if plan else (0,)):
        raise CatalogError("Local composer rejected the request")
    if len(result.stdout) > MAX_OUTPUT:
        raise CatalogError("Composer response exceeds output limit")
    try:
        output = json.loads(result.stdout)
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError("Invalid response from local composer") from exc
    if not isinstance(output, dict):
        raise RuntimeError("Invalid response from local composer")
    if plan and (output.get("ready") is not (result.returncode == 0)):
        raise RuntimeError("Inconsistent planner response")
    return output


def generate(request: dict):
    """Return an artifact only when each applicable stage succeeds."""
    allowed = {"release", "title", "theme", "requirements", "description", "language",
               "interactions", "runtime_policy"}
    if not isinstance(request, dict) or request.keys() - allowed:
        raise CatalogError("Unknown generation request fields")
    if request.get("release") != CANDIDATE:
        raise CatalogError("Generation requires the explicit source candidate")
    if len(json.dumps(request, ensure_ascii=True).encode()) > MAX_INPUT:
        raise CatalogError("Generation JSON exceeds 256 KiB")

    plan = _compose({key: value for key, value in request.items()
                     if key not in ("interactions", "runtime_policy")}, plan=True)
    base = {"release": CANDIDATE, "plan": plan, "note": NOTE}

    def blocked(stage, **details):
        return {**base, "status": "blocked", "stage": stage, **details}

    if not plan["ready"]:
        return blocked("planning")
    composition = plan["composition"]
    section_ids = [section["section_id"] for section in composition["sections"]]
    interactions = request.get("interactions", [])
    policy = request.get("runtime_policy", "scriptless")
    catalog = SyntyrCatalog()
    # Determine exact individual module requirements, then validate the declared
    # plan with those modules. Do not claim these individual files are loaded:
    # the renderer emits the aggregate bundle, checked separately below.
    requirements = catalog.validate_composition(section_ids, interactions, [], policy, CANDIDATE)
    preflight = catalog.validate_composition(section_ids, interactions,
                                            requirements["required_stylesheets"], policy, CANDIDATE)
    if not preflight["valid"]:
        return blocked("preflight", preflight=preflight)
    rendered_interactions = []
    unrendered = []
    for index, entry in enumerate(interactions):
        key = (entry["contract"], entry["recipe"], entry["relationship"])
        equivalent = NATIVE_EQUIVALENTS.get(key)
        if equivalent is None:
            unrendered.append(index)
            continue
        section_id, limitations = equivalent
        rendered_interactions.append({"index": index, **{k: entry[k] for k in
                                      ("contract", "recipe", "relationship")},
                                      "section_id": section_id,
                                      "rendering": "canonical-section-equivalent",
                                      "limitations": limitations})
    if unrendered:
        return blocked("interaction-rendering", preflight=preflight,
                       unrendered_interactions=unrendered,
                       reason="One or more declared interaction recipes have no canonical section renderer")
    # Keep original intent plan intact. Append equivalent sections only when
    # not already selected, so output stays importable in the visual builder.
    sections = list(composition["sections"])
    selected = set(section_ids)
    for entry in rendered_interactions:
        section_id = entry["section_id"]
        if section_id not in selected:
            sections.append({"section_id": section_id})
            section_ids.append(section_id)
            selected.add(section_id)
    if rendered_interactions:
        requirements = catalog.validate_composition(section_ids, interactions, [], policy, CANDIDATE)
        preflight = catalog.validate_composition(section_ids, interactions,
                                                requirements["required_stylesheets"], policy, CANDIDATE)
        if not preflight["valid"]:
            return blocked("preflight", preflight=preflight)
    output = _compose({**composition, "sections": sections})
    if len(output["html"]) > MAX_LOCAL_DOCUMENT_CHARS:
        return blocked("markup-validation", preflight=preflight,
                       reason="Generated HTML exceeds the pinned validator's document limit")
    validation = catalog.validate_local_document(output["html"], CANDIDATE, output["stylesheets"])
    if validation["diagnostics"] or validation["unknown_classes"] or validation["missing_stylesheets"]:
        return blocked("markup-validation", preflight=preflight, validation=validation)
    return {**base, "status": "generated", "stage": "complete", "preflight": preflight,
            "validation": validation, "rendered_interactions": rendered_interactions, "output": output}


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise CatalogError("Generation JSON exceeds 256 KiB")
        result = generate(json.loads(raw))
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result["status"] == "generated" else 2
    except (ValueError, UnicodeError, RuntimeError) as exc:
        print("Generation error: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
