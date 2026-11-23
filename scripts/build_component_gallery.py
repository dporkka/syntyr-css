"""Build one portable component/gallery manifest from canonical Syntyr sources.

All output is static JSON: no runtime dependency, API calls or framework.
The existing curated metadata and copyable docs snippets remain authoritative.
"""
from __future__ import annotations

import argparse
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "metadata/component-gallery.v1.json"
OPEN_CARD = re.compile(r'<article class="catalog-card syn-panel"(?P<attrs>[^>]*)>', re.I)
EXAMPLE = re.compile(
    r'<div class="catalog-preview">\n(?P<preview>.*?)\n          </div>\n'
    r'          <details class="catalog-code-details">.*?'
    r'<pre class="catalog-source"><code>(?P<source>.*?)</code></pre>',
    re.S,
)
TITLE = re.compile(r'<h2 class="syn-heading" id="([^"]+)">([^<]+)</h2>')
MODULE = re.compile(r'<span class="syn-badge">([^<]+)</span>')
DESCRIPTION = re.compile(r'<p class="syn-muted">(.*?)</p>', re.S)
IDENTIFIER = re.compile(r'^[a-z][a-z0-9-]+$')

# Document feature dependencies, not a blanket browser support guarantee.
# An example's requirements are detected from its parsed native HTML.
# Curated and intentionally small; tags are authored on the copyable HTML
# cards so browser filters and external agents share a single source of truth.
USE_CASE_DEFINITIONS = {
    "marketing-site": {
        "label": "Marketing website",
        "description": "Landing-page, pricing, trust, and public-site compositions.",
    },
    "saas-dashboard": {
        "label": "SaaS dashboard",
        "description": "Application surfaces, status, metrics, tables, and operations UI.",
    },
    "forms-workflow": {
        "label": "Forms and onboarding",
        "description": "Data entry, search, feedback, and multistep form compositions.",
    },
    "content-docs": {
        "label": "Content and documentation",
        "description": "Editorial content, help, semantic text, and documentation layouts.",
    },
    "navigation": {
        "label": "Navigation and discovery",
        "description": "Site navigation, wayfinding, search, and pagination patterns.",
    },
}

NATIVE_BROWSER_FEATURES = {
    "details-name": {
        "name": "Exclusive details grouping",
        "documentation_url": "https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details",
        "fallback": "Individual disclosures work but multiple answers may remain open.",
    },
    "invoker-commands": {
        "name": "HTML Invoker Commands",
        "documentation_url": "https://developer.mozilla.org/en-US/docs/Web/API/Invoker_Commands_API",
        "fallback": "Provide an accessible link or host-owned dialog opener when commandfor is unsupported.",
    },
    "popover": {
        "name": "HTML Popover API",
        "documentation_url": "https://developer.mozilla.org/en-US/docs/Web/API/Popover_API",
        "fallback": "Provide important content through a normal link or disclosure when popovers are unsupported.",
    },
}


class ExampleHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: set[str] = set()
        self.classes: set[str] = set()
        self.native_features: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "iframe", "object", "embed"}:
            raise ValueError(f"Unsafe tag in catalog example: {tag}")
        for key, value in attrs:
            if key.lower().startswith("on"):
                raise ValueError(f"Event handler forbidden in catalog example: {key}")
            if key.lower() in {"href", "src", "action"} and value and value.strip().lower().startswith("javascript:"):
                raise ValueError("JavaScript URL forbidden in catalog example")
        attributes = {key.lower(): value for key, value in attrs}
        if tag == "details" and "name" in attributes:
            self.native_features.add("details-name")
        if "commandfor" in attributes:
            self.native_features.add("invoker-commands")
        if "popover" in attributes or "popovertarget" in attributes:
            self.native_features.add("popover")
        self.elements.add(tag)
        for key, value in attrs:
            if key == "class" and value:
                self.classes.update(c for c in value.split() if c.startswith("syn-"))


def build_manifest() -> dict:
    curated = json.loads((ROOT / "metadata/components.json").read_text(encoding="utf-8"))
    if curated["schema_version"] != 1:
        raise ValueError("Unsupported component manifest version")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if curated["source_version"] != version:
        raise ValueError("Curated component manifest is stale")
    api = json.loads((ROOT / "metadata/syntyr-api.json").read_text(encoding="utf-8"))
    if api["version"] != 1:
        raise ValueError("Unsupported generated CSS API metadata version")
    catalog = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
    sheet = (ROOT / "dist/syntyr.all.css").read_text(encoding="utf-8")
    matches = list(OPEN_CARD.finditer(catalog))
    if not matches:
        raise ValueError("No component examples found in catalog")
    seen: set[str] = set()
    examples: list[dict] = []
    for index, card in enumerate(matches):
        block = catalog[card.end():matches[index + 1].start() if index + 1 < len(matches) else len(catalog)]
        attrs = card.group("attrs")
        label = re.search(r'aria-labelledby="([^"]+)"', attrs)
        keywords = re.search(r'data-catalog-keywords="([^"]+)"', attrs)
        category = re.search(r'data-catalog-category="([^"]+)"', attrs)
        use_cases_attr = re.search(r'data-catalog-use-cases="([^"]+)"', attrs)
        title = TITLE.search(block)
        module = MODULE.search(block)
        description = DESCRIPTION.search(block)
        snippet = EXAMPLE.search(block)
        if not all((label, keywords, category, use_cases_attr, title, module, description, snippet)):
            raise ValueError(f"Incomplete catalog card #{index + 1}")
        use_cases = use_cases_attr[1].split()
        if not use_cases or len(use_cases) != len(set(use_cases)) or any(
            tag not in USE_CASE_DEFINITIONS for tag in use_cases
        ):
            raise ValueError(f"Invalid curated use cases on catalog card #{index + 1}")
        identifier, heading_id, raw_title = label[1], title[1], title[2]
        if identifier != heading_id or not IDENTIFIER.fullmatch(identifier) or identifier in seen:
            raise ValueError(f"Invalid or duplicate catalog example id: {identifier}")
        seen.add(identifier)
        badge_modules = module[1].split(" + ")
        valid_modules = {"syntyr.core.css", "syntyr.recipes.css",
                         "syntyr.geometry.css", "syntyr.viz.css",
                         "syntyr.semantic.css", "syntyr.utilities.css"}
        if not badge_modules or any(name not in valid_modules for name in badge_modules):
            raise ValueError(f"Unexpected CSS module: {module[1]}")
        # Keep the stable primary-module field for existing gallery consumers.
        # The badge can also declare additional required stylesheets.
        css_module = badge_modules[0]
        if css_module not in {"syntyr.core.css", "syntyr.recipes.css",
                              "syntyr.geometry.css", "syntyr.viz.css"}:
            raise ValueError(f"Unexpected primary CSS module: {css_module}")
        raw_html = unescape(snippet["source"]).strip()
        if raw_html != snippet["preview"].strip():
            raise ValueError(f"Catalog preview and copyable HTML differ: {identifier}")
        parser = ExampleHTML()
        parser.feed(raw_html)
        if not parser.elements:
            raise ValueError(f"Empty catalog example: {identifier}")
        core_css = (ROOT / "dist/syntyr.core.css").read_text(encoding="utf-8")
        optional_css = {
            name: (ROOT / "dist" / name).read_text(encoding="utf-8")
            for name in ("syntyr.semantic.css", "syntyr.utilities.css")
        }
        # Preserve the stable primary module field and complete stylesheet
        # requirements separately. Non-core badges may require multiple CSS files.
        required_modules = ["syntyr.core.css"] + [
            name for name in badge_modules if name != "syntyr.core.css"
        ]
        for cls in sorted(parser.classes):
            selector = r'\.' + re.escape(cls) + r'(?![\w-])'
            loaded = [core_css] + [
                (ROOT / "dist" / name).read_text(encoding="utf-8")
                for name in required_modules if name != "syntyr.core.css"
            ]
            if not any(re.search(selector, stylesheet) for stylesheet in loaded):
                for optional, stylesheet in optional_css.items():
                    if re.search(selector, stylesheet):
                        required_modules.append(optional)
                        break
                else:
                    raise ValueError(f"Unknown class {cls} in {css_module}: {identifier}")
            if not re.search(r'\.' + re.escape(cls) + r'(?![\w-])', sheet):
                raise ValueError(f"Class missing from all.css: {cls}")
        examples.append({
            "id": identifier,
            "title": unescape(raw_title),
            "module": css_module,
            "required_stylesheets": required_modules,
            "description": unescape(re.sub(r"<[^>]+>", "", description[1])).strip(),
            "keywords": keywords[1].lower().split(),
            "category": category[1],
            "use_cases": use_cases,
            "catalog_url": f"docs/catalog.html#{identifier}",
            "playground_url": f"docs/playground.html#component={identifier}",
            "elements": sorted(parser.elements),
            "classes": sorted(parser.classes),
            "native_feature_requirements": sorted(parser.native_features),
            "html": raw_html,
        })
    return {
        "schema_version": 1,
        "source_version": version,
        "completeness": "curated-examples",
        "source_of_truth": {
            "components": "metadata/components.json",
            "examples": "docs/catalog.html",
            "themes": "metadata/syntyr-api.json",
        },
        "scope": "syn-root",
        "runtime_requirement": "none",
        "use_case_definitions": USE_CASE_DEFINITIONS,
        "adoption_guidance": {
            "framework_guide": "docs/framework-integrations.html",
            "required_css_order": ["syntyr.core.css", "then optional files listed by each example's required_stylesheets"],
            "stylesheet_rule": "Load required_stylesheets in their listed order; syntyr.all.css replaces, never accompanies, individual modules.",
            "html_rule": "Place example HTML inside a stable .syn-root; copy IDs only once per document and replace demo links and form actions.",
            "browser_rule": "Consult native_feature_requirements and native_browser_features fallbacks; an empty list does not guarantee compatibility.",
            "release_rule": "Unreleased 0.3.0-alpha.5 source candidate; do not assume published alpha.4 includes these examples.",
        },
        "native_browser_features": NATIVE_BROWSER_FEATURES,
        "note": "Unreleased source-tree candidate, not a guarantee of published alpha.4 availability. Host applications own behavior, data and validation.",
        "components": curated["components"],
        "recipes": curated["recipes"],
        "themes": api["themes"],
        "examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if checked-in JSON is stale")
    args = parser.parse_args()
    try:
        rendered = json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n"
    except (ValueError, KeyError, OSError) as error:
        print(f"INVALID component gallery: {error}", file=sys.stderr)
        return 1
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print("STALE component gallery; run python3 scripts/build_component_gallery.py", file=sys.stderr)
            return 1
        print(f"OK {OUTPUT.relative_to(ROOT)}")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"WROTE {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
