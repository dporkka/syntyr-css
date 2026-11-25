"""Optional, explicitly configured local HTML inspector bridge."""
from __future__ import annotations

import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from .catalog import CANDIDATE, MAX_HTML_CHARS, MAX_RESULTS, ROOT, CatalogError, SyntyrCatalog
from scripts.syntyr_check import validate_html

MAX_SELECTOR_CHARS = 256
BINARY_ENV = "SYNTYR_HTML_INSPECTOR"


def _validate_input(html: str, release: str) -> bytes:
    if release != CANDIDATE:
        raise CatalogError("HTML inspection requires the explicit source candidate release")
    if not isinstance(html, str) or len(html) > MAX_HTML_CHARS:
        raise CatalogError(f"HTML must be a string of at most {MAX_HTML_CHARS} characters")
    try:
        return html.encode("utf-8")
    except UnicodeError:
        raise CatalogError("HTML must be valid UTF-8") from None


def _validate_selector(selector: str) -> None:
    if not isinstance(selector, str) or len(selector) > MAX_SELECTOR_CHARS or "\x00" in selector:
        raise CatalogError(f"Invalid selector: use at most {MAX_SELECTOR_CHARS} characters without NUL")


def _invoke(data: bytes, arguments: list[str], timeout: float = 5) -> dict:
    executable = Path(os.environ.get(BINARY_ENV, ""))
    if not executable.is_absolute() or not executable.is_file():
        raise CatalogError(f"Configure {BINARY_ENV} with the absolute path to a trusted, prebuilt inspector")
    # No shell, PATH discovery, implicit Go builds, network, or caller-supplied paths.
    try:
        result = subprocess.run(
            [str(executable), "--catalog", str(ROOT / "metadata/components.json"),
             *arguments, "-"],
            input=data, capture_output=True, timeout=timeout, check=False,
            cwd=ROOT,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        raise CatalogError("HTML inspector failed to execute or timed out") from None
    if result.returncode != 0:
        raise CatalogError("HTML inspector rejected input (check selector and catalog)") from None
    try:
        report = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        raise CatalogError("Invalid HTML inspector response") from None
    if not isinstance(report, dict):
        raise CatalogError("Invalid HTML inspector response")
    return report


def inspect_markup(html: str, release: str, selector: str = "") -> dict:
    """Inspect supplied literal HTML, never caller-provided filesystem paths."""
    data = _validate_input(html, release)
    _validate_selector(selector)
    report = _invoke(data, ["--selector", selector, "--limit", str(MAX_RESULTS)])
    if (report.get("schema_version") != 1
            or report.get("source_version") != release or report.get("selector") != selector
            or not isinstance(report.get("elements"), list)
            or len(report["elements"]) > MAX_RESULTS
            or not isinstance(report.get("truncated"), bool)
            or report.get("document_sha256") != hashlib.sha256(data).hexdigest()
            or any(not isinstance(e, dict) or not isinstance(e.get("element_id"), str)
                   or not re.fullmatch(r"el-[1-9][0-9]*", e["element_id"]) for e in report["elements"])):
        raise CatalogError("Incompatible HTML inspector response; rebuild from this checkout")
    return {**report, "release": release, "release_status": "unreleased_candidate"}


MAX_OPERATIONS = 8
MODIFIER = re.compile(r"syn-[a-z0-9_-]+--[a-z0-9_-]+")


def plan_variants(html: str, release: str, document_sha256: str, operations: list[dict]) -> dict:
    """All-or-nothing preview of independent class replacements on one snapshot."""
    return _plan_variants(html, release, document_sha256, operations, source_patches=False)


def plan_source_patches(html: str, release: str, document_sha256: str, operations: list[dict]) -> dict:
    """Preview exact source edits and validate their combined candidate."""
    return _plan_variants(html, release, document_sha256, operations, source_patches=True)


def _plan_variants(html: str, release: str, document_sha256: str, operations: list[dict], *, source_patches: bool) -> dict:
    data = _validate_input(html, release)
    if document_sha256 != hashlib.sha256(data).hexdigest():
        raise CatalogError("Document digest mismatch; inspect again")
    if not isinstance(operations, list) or not 1 <= len(operations) <= MAX_OPERATIONS:
        raise CatalogError(f"Expected 1 to {MAX_OPERATIONS} operations")
    seen = set()
    for op in operations:
        if not isinstance(op, dict) or set(op) != {"element_id", "selector", "from", "to"}:
            raise CatalogError("Each operation requires element_id, selector, from and to")
        element = op["element_id"]
        if not isinstance(element, str) or not re.fullmatch(r"el-[1-9][0-9]{0,7}", element):
            raise CatalogError("Invalid element ID")
        if element in seen:
            raise CatalogError("Duplicate element target; plan one change per element")
        seen.add(element)
        _validate_selector(op["selector"])
        if not op["selector"]:
            raise CatalogError("An explicit selector is required")
        if any(not isinstance(op[k], str) or len(op[k]) > 128 or not MODIFIER.fullmatch(op[k]) for k in ("from", "to")):
            raise CatalogError("Expected literal Syntyr modifier classes")
    deadline = time.monotonic() + 5
    changes = []
    patches = []
    for index, op in enumerate(operations):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CatalogError("HTML plan timed out")
        try:
            change = _invoke(data, ["--selector", op["selector"],
                                    "--document-sha256", document_sha256,
                                    "--element-id", op["element_id"],
                                    "--preview-from", op["from"], "--preview-to", op["to"],
                                    *(["--source-patch"] if source_patches else [])], remaining)
        except CatalogError as error:
            raise CatalogError(f"Operation {index + 1}: {error}") from None
        expected = {"schema_version": 1, "source_version": release,
                    "document_sha256": document_sha256, "element_id": op["element_id"],
                    "selector": op["selector"], "attribute": "class", "preview_only": True}
        if (any(change.get(k) != v for k, v in expected.items())
                or not isinstance(change.get("before"), str)
                or not isinstance(change.get("after"), str)
                or change["before"] == change["after"]):
            raise CatalogError("Incompatible preview response; rebuild from this checkout")
        changes.append({k: change[k] for k in ("element_id", "selector", "attribute", "before", "after")})
        if source_patches:
            patch = change.get("source_patch")
            if not isinstance(patch, dict) or set(patch) != {"start_byte", "end_byte", "expected", "replacement"}:
                raise CatalogError("Incompatible source patch response")
            start, end = patch["start_byte"], patch["end_byte"]
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(data)
                    or patch["expected"] != op["from"] or patch["replacement"] != op["to"]
                    or data[start:end] != op["from"].encode("ascii")):
                raise CatalogError("Source patch precondition mismatch")
            patches.append({**patch, "element_id": op["element_id"]})
    result = {"schema_version": 1, "release": release, "release_status": "unreleased_candidate",
              "document_sha256": document_sha256, "preview_only": True, "changes": changes,
              "limitations": "Independent decoded class-attribute proposals; no source patches, writes, or rendered validation."}
    if not source_patches:
        return result
    patches.sort(key=lambda p: p["start_byte"])
    if any(a["end_byte"] > b["start_byte"] for a, b in zip(patches, patches[1:])):
        raise CatalogError("Overlapping source patches")
    candidate = data
    for patch in reversed(patches):
        candidate = candidate[:patch["start_byte"]] + patch["replacement"].encode("ascii") + candidate[patch["end_byte"]:]
    updated = candidate.decode("utf-8")
    contract = SyntyrCatalog()._validation_contract(release)
    baseline = validate_html(html, contract, semantic=True)
    diagnostics = validate_html(updated, contract, semantic=True)
    errors = sum(d["severity"] == "error" for d in diagnostics)
    result.update(patches=patches, result_sha256=hashlib.sha256(candidate).hexdigest(),
                  unified_diff=_unified_diff(html, updated),
                  validation={"valid": errors == 0, "error_count": errors,
                              "baseline_error_count": sum(d["severity"] == "error" for d in baseline),
                              "diagnostic_count": len(diagnostics),
                              "diagnostics": diagnostics[:MAX_RESULTS],
                              "truncated": len(diagnostics) > MAX_RESULTS},
                  limitations="Exact UTF-8 byte patches on supported literal HTML; static contract and semantic diagnostics only, no writes or rendered validation.")
    return result


def _unified_diff(before: str, after: str) -> str:
    def lines(text):
        parts = text.split("\n")
        return [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])
    out = []
    for line in difflib.unified_diff(lines(before), lines(after), fromfile="original.html", tofile="candidate.html"):
        out.append(line)
        if not line.endswith("\n"):
            out.append("\n" + r"\ No newline at end of file" + "\n")
    return "".join(out)
