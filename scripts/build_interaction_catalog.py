"""Validate and render the versioned, dependency-free interaction recipe catalog.

The JSON is the single authoring source. Source markers and named regression
tests must exist before a recipe can appear as documented and test-backed.
No runtime JS, network access or third-party Python packages are required.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "metadata/interaction-recipes.json"
OUTPUT = ROOT / "docs/interaction-recipes.md"
FIELDS = {
    "id", "title", "kind", "use_when", "behavior_owner",
    "source", "docs", "css", "source_markers", "test_file",
    "test_markers", "keyboard", "fallback",
}
KINDS = {"native", "headless"}
EXAMPLE = "examples/headless-react/tests/interactions.spec.ts"
NATIVE_TEST = "tests/interaction_recipe_browser.py"


def _path(name: str, prefix: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError(f"Invalid recipe path: {name!r}")
    pure = PurePosixPath(name)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts or not name.startswith(prefix):
        raise ValueError(f"Unsafe recipe path: {name!r}")
    target = ROOT / name
    if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(ROOT):
        raise ValueError(f"Missing or unsafe recipe resource: {name}")
    return target


def load_catalog() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def validate_catalog(catalog: dict) -> None:
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "source_version", "release_status", "recipes"}:
        raise ValueError("Invalid recipe manifest shape")
    if type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        raise ValueError("Unsupported recipe schema")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if catalog["source_version"] != version or catalog["release_status"] != "unreleased-source-candidate":
        raise ValueError("Catalog version/status does not match the unreleased source candidate")
    recipes = catalog["recipes"]
    if not isinstance(recipes, list) or not recipes:
        raise ValueError("Expected nonempty recipes array")
    seen: set[str] = set()
    for entry in recipes:
        if not isinstance(entry, dict) or set(entry) != FIELDS:
            raise ValueError("Invalid recipe fields")
        ident = entry["id"]
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", ident):
            raise ValueError(f"Invalid recipe ID: {ident!r}")
        if ident in seen:
            raise ValueError(f"Duplicate recipe ID: {ident}")
        seen.add(ident)
        kind = entry["kind"]
        if kind not in KINDS:
            raise ValueError(f"Unsupported recipe kind: {kind}")
        for field in ("title", "use_when", "behavior_owner", "keyboard", "fallback"):
            value = entry[field]
            if not isinstance(value, str) or not value.strip() or "|" in value or "\n" in value:
                raise ValueError(f"{ident}: invalid {field}")
        source = _path(entry["source"], "examples/")
        _path(entry["docs"], "docs/")
        for field in ("source_markers", "test_markers", "css"):
            values = entry[field]
            if not isinstance(values, list) or not values or any(
                not isinstance(item, str) or not item for item in values
            ):
                raise ValueError(f"{ident}: invalid {field}")
        if kind == "native":
            if entry["test_file"] != NATIVE_TEST or source.suffix != ".html":
                raise ValueError(f"{ident}: native recipe needs HTML + native browser regression")
        elif entry["test_file"] != EXAMPLE or source.suffix != ".tsx":
            raise ValueError(f"{ident}: headless recipe needs React source + real browser regression")
        tests = _path(entry["test_file"], "tests/" if kind == "native" else "examples/")
        for path, markers in ((source, entry["source_markers"]), (tests, entry["test_markers"])):
            contents = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in contents:
                    raise ValueError(f"{ident}: missing marker {marker!r} in {path.relative_to(ROOT)}")
        if __package__:
            from .build import all_distributions
        else:
            from build import all_distributions
        public_dist = {f"dist/{name}" for name in all_distributions()}
        for css in entry["css"]:
            _path(css, "dist/" if css.startswith("dist/") else "integrations/")
            if css not in public_dist and css != "integrations/headless/interactions.css":
                raise ValueError(f"{ident}: unrecognized CSS asset {css}")
        if kind == "headless" and "dist/syntyr.core.css" not in entry["css"]:
            raise ValueError(f"{ident}: headless recipes need the core stylesheet")


def _source_link(path: str) -> str:
    if path.endswith(".html"):
        return f"../{path}"
    # React examples are source fixtures, not deployed interactive JS on the CSS-only site.
    return f"https://github.com/dporkka/syntyr-css/blob/main/{path}"


def render_catalog(catalog: dict) -> str:
    validate_catalog(catalog)
    version = catalog["source_version"]
    lines = [
        "# Interaction recipes: native first, headless when necessary",
        "",
        f"**Version:** unreleased alpha.5 source candidate ({version}). The currently",
        "published immutable alpha.4 release does not contain every candidate",
        "adapter or document here. Verify availability in your installed release.",
        "",
        "Syntyr styles interfaces; it does not implement widget state or keyboard",
        "controllers. Start with HTML's own behavior and add **optional application",
        "dependencies** for interactions that really require them.",
        "",
        "This is a source-validated, machine-readable set of integration references;",
        "the presence of regression tests does not certify accessibility, nor",
        "does it claim that every browser or assistive technology has been tested.",
        "The canonical data is [interaction-recipes.json](../metadata/interaction-recipes.json).",
        "",
        "## Choose the lightest behavior owner",
        "",
        "| Recipe | When to use | Behavior owner | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for recipe in catalog["recipes"]:
        name = recipe["title"]
        test = f"[test source]({_source_link(recipe['test_file'])})"
        lines.append(
            f"| [{name}](#{recipe['id']}) | {recipe['use_when']} | "
            f"{recipe['behavior_owner']} | {test} |"
        )
    lines.extend([
        "",
        "## Integration contracts",
        "",
    ])
    for recipe in catalog["recipes"]:
        name = recipe["title"]
        lines.extend([
            f"<a id=\"{recipe['id']}\"></a>",
            "",
            f"### {name}",
            "",
            f"- **Type:** {recipe['kind']} — **behavior:** {recipe['behavior_owner']}.",
            f"- **Source:** [{recipe['source']}]({_source_link(recipe['source'])}); "
            f"[guide]({Path(recipe['docs']).name}).",
            f"- **CSS:** `{' + '.join(recipe['css'])}`.",
            f"- **Keyboard:** {recipe['keyboard']}.",
            f"- **Fallback:** {recipe['fallback']}",
            f"- **Regression source:** [{recipe['test_file']}]({_source_link(recipe['test_file'])}).",
            "",
        ])
    lines.extend([
        "## Run the regressions",
        "",
        "For browser-native recipes (**No JavaScript** in the page):",
        "",
        "```sh",
        "python3 tests/interaction_recipe_browser.py --browsers chromium firefox",
        "```",
        "",
        "Install Playwright and the selected browser binaries in your **development**",
        "environment. The script deliberately fails if an engine cannot launch.",
        "Feature-dependent dialog behavior is tested with a visible fallback when",
        "invoker commands are unavailable.",
        "",
        "For the optional React Aria/Radix examples:",
        "",
        "```sh",
        "cd examples/headless-react",
        "npm ci",
        "npm run build",
        "npm test",
        "```",
        "",
        "The React fixture includes genuine keyboard navigation, filtering,",
        "selection, focus restoration, grid sorting, and notification dismissal.",
        "The React dependencies do **not** ship in Syntyr's CSS core.",
        "",
        "The zero-dependency manifest contract and documentation checks run with:",
        "",
        "```sh",
        "python3 -m unittest tests.test_interaction_recipe_catalog -v",
        "python3 scripts/build_interaction_catalog.py --check",
        "```",
        "",
        "## Responsibilities that CSS cannot satisfy",
        "",
        "- No CSS class implements ARIA semantics, roving focus, key handling,",
        "  asynchronous selection, announcement timing, sorting, or persistence.",
        "- For plain tables, preserve native HTML semantics; do not apply",
        "  `role=\"grid\"` without implementing the full keyboard model.",
        "- A native popover with links is **not** an ARIA menu. It uses normal Tab",
        "  navigation; use Radix only when menu semantics are genuinely required.",
        "- Form submission, server-side validation, authorization and actual data",
        "  sorting belong to the host application. The static sorted-table example",
        "  is a truthful snapshot, not an interactive sorting implementation.",
        "- Portal-mounted headless controls must remain inside a themed",
        "  `.syn-root` or explicitly receive the corresponding theme scope.",
        "- Before production adoption, test NVDA/VoiceOver, keyboard-only use,",
        "  high zoom/reflow, forced colors, reduced motion, IME and mobile touch",
        "  with your chosen browser versions. Automated results are not certification.",
        "",
        "Use existing [native browser documentation](native-browser-apis.md),",
        "[data-table guidance](data-tables.md) and",
        "[headless interaction guidance](headless-interactions.md) for further details.",
        "",
    ])
    # markdown_it escapes literal HTML tags, so use standard heading slug links
    # instead of raw anchors; the generated HTML uses heading slugs.
    lines = [line for line in lines if not line.startswith('<a id=')]
    for recipe in catalog["recipes"]:
        anchor = re.sub(r"[^a-z0-9 -]", "", recipe["title"].lower()).replace(" ", "-")
        lines = [line.replace(f"(#{recipe['id']})", f"(#{anchor})") for line in lines]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = render_catalog(load_catalog())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != result:
            print("STALE interaction recipe guide; run scripts/build_interaction_catalog.py", file=sys.stderr)
            return 1
        print("OK interaction recipe guide and source/test contracts")
        return 0
    OUTPUT.write_text(result, encoding="utf-8")
    print(f"Generated {len(load_catalog()['recipes'])} validated interaction recipes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
