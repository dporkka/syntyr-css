"""Human approval contract for freezing an immutable Syntyr CSS release.

Machine-readable signoff is *not* a WCAG certificate or cryptographic identity
proof. It prevents accidentally treating a passing automated suite as human
accessibility, branding or deployment approval.
"""
import json
from pathlib import Path

REQUIRED_CHECKS = (
    "contrast",
    "screen_reader",
    "real_browser_zoom",
    "native_forced_colors",
    "browser_support",
    "brand_clearance",
)


class ReleaseBlocked(ValueError):
    """Approval evidence is missing, incomplete or from a different source."""


def validate_approval(document: object, version: str, commit: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["approval must be a JSON object"]
    if document.get("version") != version:
        errors.append("version does not match the candidate VERSION")
    if document.get("commit") != commit:
        errors.append("commit does not match the exact candidate HEAD SHA")
    checks = document.get("checks")
    if not isinstance(checks, dict):
        return errors + ["checks must be an object"]
    for name in REQUIRED_CHECKS:
        item = checks.get(name)
        if not isinstance(item, dict):
            errors.append(f"{name}: missing manual review")
            continue
        if item.get("status") != "pass":
            errors.append(f"{name}: review status must be pass")
        for field in ("reviewer", "evidence"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name}: {field} is required")
    extra = sorted(set(checks) - set(REQUIRED_CHECKS))
    if extra:
        errors.append(f"unknown review checks: {', '.join(extra)}")
    return errors


def require_approval(root: Path, version: str, commit: str,
                     approval_path: Path | None = None) -> None:
    path = approval_path or root / "release/release-approval.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReleaseBlocked(f"Release blocked: cannot read approval {path}: {exc}") from exc
    errors = validate_approval(document, version, commit)
    if errors:
        raise ReleaseBlocked("Release blocked:\n- " + "\n- ".join(errors))
