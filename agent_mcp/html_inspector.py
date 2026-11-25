"""Optional, explicitly configured local HTML inspector bridge."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from .catalog import CANDIDATE, MAX_HTML_CHARS, MAX_RESULTS, ROOT, CatalogError

MAX_SELECTOR_CHARS = 256
BINARY_ENV = "SYNTYR_HTML_INSPECTOR"


def inspect_markup(html: str, release: str, selector: str = "") -> dict:
    """Inspect supplied literal HTML, never caller-provided filesystem paths."""
    if release != CANDIDATE:
        raise CatalogError("HTML inspection requires the explicit source candidate release")
    if not isinstance(html, str) or len(html) > MAX_HTML_CHARS:
        raise CatalogError(f"HTML must be a string of at most {MAX_HTML_CHARS} characters")
    if not isinstance(selector, str) or len(selector) > MAX_SELECTOR_CHARS or "\x00" in selector:
        raise CatalogError(f"Invalid selector: use at most {MAX_SELECTOR_CHARS} characters without NUL")
    executable = Path(os.environ.get(BINARY_ENV, ""))
    if not executable.is_absolute() or not executable.is_file():
        raise CatalogError(f"Configure {BINARY_ENV} with the absolute path to a trusted, prebuilt inspector")
    # No shell, PATH discovery, implicit Go builds, network, or caller-supplied paths.
    try:
        result = subprocess.run(
            [str(executable), "--catalog", str(ROOT / "metadata/components.json"),
             "--selector", selector, "--limit", str(MAX_RESULTS), "-"],
            input=html.encode("utf-8"), capture_output=True, timeout=5, check=False,
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
    if (not isinstance(report, dict) or report.get("schema_version") != 1
            or report.get("source_version") != release or report.get("selector") != selector
            or not isinstance(report.get("elements"), list)
            or len(report["elements"]) > MAX_RESULTS
            or not isinstance(report.get("truncated"), bool)):
        raise CatalogError("Incompatible HTML inspector response; rebuild from this checkout")
    return {**report, "release": release, "release_status": "unreleased_candidate"}
