"""Fail closed on CSS source drift without adding a compiler or runtime dependency.

Usage: python3 scripts/maintenance_policy.py

Every source must be owned by a shipped distribution; a distribution must not
include the same module twice. Component theme forks, missing CSS variables
without fallbacks, and specificity overrides introduce long-lived maintenance
cost and are not allowed. No byte ceilings.
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    from .build import SOURCE, all_distributions
except ImportError:
    from build import SOURCE, all_distributions


def css_code_only(content: str) -> str:
    """Mask CSS comments and quoted strings without changing nesting positions.

    This is a lexical guard for handwritten source, not a complete CSS parser.
    Escaped quotes inside strings cannot escape the string-masking boundary.
    """
    out = list(content)
    i = 0
    while i < len(content):
        if content.startswith("/*", i):
            end = content.find("*/", i + 2)
            stop = len(content) if end < 0 else end + 2
        elif content[i] == "\\":
            # Escapes outside strings must not turn an escaped quote into a string.
            i += 2
            continue
        elif content[i] in ("\"", "'"):
            quote = content[i]
            stop = i + 1
            while stop < len(content):
                if content[stop] == "\\":
                    stop += 2
                elif content[stop] == quote:
                    stop += 1
                    break
                else:
                    stop += 1
            stop = min(stop, len(content))
        else:
            i += 1
            continue
        for j in range(i, stop):
            if content[j] not in "\r\n":
                out[j] = " "
        i = stop
    return "".join(out)


THEME_ATTRIBUTE = re.compile(r"\[\s*data-syn-theme\b")
CSS_WHITESPACE = " \t\r\n\f"


def css_escape(content: str, pos: int) -> tuple[str, int] | None:
    """Decode one CSS escape at pos; reject invalid raw URL escapes.

    Hex escapes consume up to six digits and one optional whitespace character.
    This preserves the actual network/fragment destination for policy checks.
    """
    pos += 1  # backslash
    if pos >= len(content) or content[pos] in "\r\n\f":
        return None
    start = pos
    while pos < len(content) and pos - start < 6 and content[pos] in "0123456789abcdefABCDEF":
        pos += 1
    if pos > start:
        scalar = int(content[start:pos], 16)
        if pos < len(content) and content[pos] in CSS_WHITESPACE:
            if content[pos:pos + 2] == "\r\n":
                pos += 2
            else:
                pos += 1
        decoded = chr(scalar) if 0 < scalar <= 0x10ffff and not 0xd800 <= scalar <= 0xdfff else "\ufffd"
        return decoded, pos
    return content[pos], pos + 1


def css_url_argument(content: str, pos: int) -> tuple[str, int] | None:
    """Extract a literal CSS url() argument, honoring quoted/unquoted escapes.

    The caller finds only genuine url() tokens in comment/string-masked CSS.
    This intentionally rejects invalid syntax instead of silently allowing it.
    """
    size = len(content)
    while pos < size and content[pos] in CSS_WHITESPACE:
        pos += 1
    quoted = pos < size and content[pos] in ("'", '"')
    quote = content[pos] if quoted else ""
    if quoted:
        pos += 1
    value = []
    while pos < size:
        char = content[pos]
        if char == "\\":
            decoded = css_escape(content, pos)
            if decoded is None:
                return None
            chunk, pos = decoded
            value.append(chunk)
            continue
        if quoted and char == quote:
            pos += 1
            break
        if not quoted and (char == ")" or char in CSS_WHITESPACE):
            break
        if char in "\r\n\f" or (not quoted and char in "('\""):
            return None
        value.append(char)
        pos += 1
    else:
        return None
    while pos < size and content[pos] in CSS_WHITESPACE:
        pos += 1
    if pos >= size or content[pos] != ")":
        return None
    return "".join(value), pos + 1


def css_identifier(content: str, pos: int) -> tuple[str, int]:
    """Read a CSS identifier with escapes; callers inspect decoded keywords."""
    chars = []
    while pos < len(content):
        char = content[pos]
        if char == "\\":
            escaped = css_escape(content, pos)
            if escaped is None:
                break
            decoded, pos = escaped
            chars.append(decoded)
        elif char.isalnum() or char in "_-":
            chars.append(char)
            pos += 1
        else:
            break
    return "".join(chars), pos


def css_references(masked: str, raw: str) -> tuple[bool, list[str | None]]:
    """Find import at-rules and URL functions, including escaped CSS names.

    Masked strings/comments avoid false positives. Parsed URL arguments are
    skipped so their text cannot masquerade as CSS tokens.
    """
    imports = False
    urls = []
    pos = 0
    while pos < len(masked):
        char = masked[pos]
        if char == "@":
            name, end = css_identifier(masked, pos + 1)
            if name.lower() == "import":
                imports = True
            pos = max(pos + 1, end)
            continue
        if char.isalpha() or char in "_-\\":
            name, end = css_identifier(masked, pos)
            if end <= pos:
                pos += 1
                continue
            next_pos = end
            while next_pos < len(masked) and masked[next_pos] in CSS_WHITESPACE:
                next_pos += 1
            if name.lower() == "url" and next_pos < len(masked) and masked[next_pos] == "(":
                parsed = css_url_argument(raw, next_pos + 1)
                urls.append(None if parsed is None else parsed[0])
                pos = next_pos + 1 if parsed is None else parsed[1]
            else:
                pos = end
            continue
        pos += 1
    return imports, urls


# Native hidden is a tightly-scoped accessibility exception to the normal
# prohibition on !important in base.css. Never allow generic display overrides.
NATIVE_HIDDEN_GUARD = re.compile(
    r':where\(\s*\.syn-root\[hidden\]:not\(\[hidden="until-found" i\]\)\s*,\s*'
    r'\.syn-root \[hidden\]:not\(\[hidden="until-found" i\]\)\s*\)\s*'
    r'\{\s*display\s*:\s*none\s*!important\s*;\s*\}',
    re.IGNORECASE | re.DOTALL,
)
CUSTOM_PROPERTY = re.compile(r"(?<=[{;}])\s*(--syn-[a-zA-Z0-9_-]+)\s*:")
VAR_REFERENCE = re.compile(r"\b(?i:var)\(\s*(--syn-[a-zA-Z0-9_-]+)\s*([,)])")
IMPORTANT = re.compile(r"!\s*important\b", re.IGNORECASE)
BLOCK_OR_IMPORTANT = re.compile(r"[{}]|!\s*important\b", re.IGNORECASE)
APPROVED_REDUCED_MOTION_MEDIA = re.compile(
    r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)", re.IGNORECASE
)
ALLOWED_MOTION_DECLARATION = re.compile(
    r"(?:scroll-behavior\s*:\s*auto|transition-duration\s*:\s*0s|animation-duration\s*:\s*0s)",
    re.IGNORECASE,
)


def base_important_issues(content: str) -> list[str]:
    """Allow only the existing accessibility overrides inside reduced-motion media.

    Only the positive, standalone reduced-motion media query is accepted.
    This conservative block walk is for handwritten base.css, not a general
    CSS parser or a consumer build dependency.
    """
    blocks = []
    cursor = 0
    issues = []
    for token in BLOCK_OR_IMPORTANT.finditer(content):
        if token.group() == "{":
            blocks.append(content[cursor:token.start()].rsplit(";", 1)[-1].strip())
            cursor = token.end()
        elif token.group() == "}":
            if blocks:
                blocks.pop()
            cursor = token.end()
        else:
            preceding = content[cursor:token.start()].rsplit(";", 1)[-1].strip()
            reduced_motion = any(
                APPROVED_REDUCED_MOTION_MEDIA.fullmatch(block)
                for block in blocks
            )
            if not reduced_motion or not ALLOWED_MOTION_DECLARATION.fullmatch(preceding):
                issues.append("base.css: !important outside reduced-motion accessibility allowlist")
    return issues


# Adapter-only syntax and DOM contracts must not become core CSS requirements.
# Keep the list narrow: native HTML/ARIA states remain valid core selectors.
INTEGRATION_LEAK = re.compile(
    r"@(?:theme|apply|tailwind|plugin|config)\b"
    r"|\.syn-(?:shadcn|radix|figma)(?!\w)"
    r"|\.(?:radix-|react-aria-|shadcn-)"
    r"|--(?:tw|radix|react-aria|figma)-"
    r"|\[\s*data-(?:radix|react-aria)-"
)


def find_issues(source_root: Path = SOURCE, bundles: dict | None = None) -> list[str]:
    """Return deterministic, actionable violations of the source ownership policy."""
    registry = all_distributions() if bundles is None else bundles
    issues = []
    referenced = set()
    cleaned_sources = {}
    for bundle, sources in sorted(registry.items()):
        seen = set()
        for source in sources:
            source_path = Path(source)
            if source_path.is_absolute() or ".." in source_path.parts or source_path.suffix != ".css":
                issues.append(f"{bundle}: invalid source: {source}")
                continue
            if source in seen:
                issues.append(f"{bundle}: duplicate source: {source}")
            seen.add(source)
            referenced.add(source)
            if not (source_root / source).is_file():
                issues.append(f"{bundle}: missing source: {source}")

    for path in sorted(source_root.rglob("*.css")):
        name = path.relative_to(source_root).as_posix()
        if name not in referenced:
            issues.append(f"unregistered source: {name}")
        raw_content = path.read_text(encoding="utf-8")
        content = css_code_only(raw_content)
        cleaned_sources[name] = content
        imports, urls = css_references(content, raw_content)
        if imports:
            issues.append(f"{name}: CSS import; bundle the source at build time")
        for asset in urls:
            if asset is None:
                issues.append(f"{name}: invalid CSS url() token")
                break
            # Do not strip decoded whitespace: an escaped/quoted leading space
            # is part of the URL, not harmless syntax around its argument.
            if not asset.lower().startswith("data:") and not asset.startswith("#"):
                issues.append(f"{name}: external CSS asset; embed or own it in the host application")
                break
        # Theme palette variants must live in tokens, not in copied components.
        if name not in {"tokens.css", "base.css", "print.css", "viz.css"} and THEME_ATTRIBUTE.search(content):
            label = "component theme fork" if name.startswith("components/") else "theme fork"
            issues.append(f"{name}: {label}; change theme tokens instead")
        if INTEGRATION_LEAK.search(content):
            issues.append(f"{name}: integration leak; keep vendor-specific syntax, selectors and tokens in integrations/")
        if name == "base.css":
            # Strip only the exact native-hidden accessibility declaration
            # before applying the existing strict reduced-motion allowlist.
            audited = NATIVE_HIDDEN_GUARD.sub("", raw_content)
            issues.extend(base_important_issues(css_code_only(audited)))
        elif IMPORTANT.search(content):
            issues.append(f"{name}: !important outside base.css; use cascade layers")

    # A custom property can be supplied by a theme or consumer when var() has
    # a fallback. Without a fallback, a misspelled/missing default silently
    # invalidates the consuming declaration in the browser.
    declarations = {
        match.group(1) for content in cleaned_sources.values()
        for match in CUSTOM_PROPERTY.finditer(content)
    }
    for name, content in sorted(cleaned_sources.items()):
        for match in VAR_REFERENCE.finditer(content):
            token, delimiter = match.groups()
            if delimiter == ")" and token not in declarations:
                issues.append(f"{name}: unresolved CSS variable without fallback: {token}")

    return sorted(set(issues))


def main() -> int:
    issues = find_issues()
    if issues:
        for issue in issues:
            print("MAINTENANCE POLICY: " + issue)
        return 1
    print("OK: CSS sources are registered once per bundle, with no component theme forks or !important overrides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
