"""Export Syntyr editor metadata from CSS sources with no external dependencies.

Generated files are committed and supported by any editor able to consume
HTML/CSS custom-data JSON or VS Code workspace snippets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

if __package__:
    from .build import all_distributions, distributions
else:
    from build import all_distributions, distributions

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
OUTPUT = ROOT / "metadata"
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
CLASS = re.compile(r"(?<!-)\.(syn-[a-zA-Z0-9_-]+)\b")
TOKEN = re.compile(r"(?<![\w-])(--syn-[a-zA-Z0-9_-]+)\s*:")
THEME = re.compile(r'data-syn-theme="([^"]+)"')

CLASS_DOCS = {
    "syn-root": "Required style scope for Syntyr components and themes.",
    "syn-media-rail--controls": "Opt-in native CSS carousel previous/next buttons; Scroll Snap remains usable without CSS Overflow 5 support.",
    "syn-media-rail--markers": "Opt-in native CSS position markers; label each direct child with data-syn-scroll-label.",

    "syn-panel": "General-purpose surface; customize via --syn-panel-* properties.",
    "syn-frame--accent": "Optional 2px accent outline for a selected frame shape.",
    "syn-frame--step": "Optional square-stepped top-right and bottom-left frame.",
    "syn-frame--facet": "Optional diagonal top-left and bottom-right facets.",
    "syn-glow": "Opt-in themed shadow; decoration controlled by data-syn-intensity.",
    "syn-button": "Native button or link styling; use semantic HTML.",
    "syn-button--primary": "Primary action appearance.",
    "syn-region": "Container query boundary for responsive compositions.",
    "syn-filter-bar": "Optional wrapping CRM GET filter form; host applies query parameters.",
    "syn-filter-field": "Label and control group in an optional CRM filter bar.",
    "syn-filter-actions": "Wrapping submit and reset action group for CRM filters.",
    "syn-pipeline": "Keyboard-focusable scrollable CRM stage layout; host manages state.",
    "syn-pipeline-lane": "Named stage column with semantic list of records.",
    "syn-pipeline-card": "Opt-in CRM record presentation, not a drag-drop widget.",
    "syn-record-fields": "Responsive definition-list layout for key/value record details.",
    "syn-operation-feedback": "Optional host-managed operation feedback with truthful state text.",
    "syn-change-pair": "Responsive before/after value pair for existing semantic record fields.",
    "syn-change-before": "Previous or removed revision value with visible text label.",
    "syn-change-after": "Updated or added revision value with visible text label.",
    "syn-geo-shell": "Named CSS container for map-based workspace layouts; use with core plus optional geo CSS.",
    "syn-geo-workspace": "Responsive GIS sidebar plus map viewport; stacks based on container width.",
    "syn-geo-map": "Map renderer mount surface; actual projection and map behavior belong to host.",
    "syn-geo-overlay": "Pointer-transparent overlay for application-owned map controls and legends.",
    "syn-geo-marker": "44px visual marker target; renderer-managed marker positions stay renderer-managed.",
    "syn-geo-marker-layer": "Static diagram overlay for percentage-positioned markers, not for renderer-managed markers.",
    "syn-geo-legend": "Readable, labeled map legend; host must provide layer semantics.",
    "syn-geo-scale": "Scale presentation; actual scale and bar width require a real map renderer.",
    "syn-geo-attribution": "Optional attribution surface; preserve map provider credits.",
    "syn-file-queue": "Optional ordered file lifecycle list; not an upload engine.",
    "syn-file-item": "File queue entry with host-owned queued, uploading, complete or failed state.",
    "syn-file-item-header": "Flexible file name and visible status header for queue entries.",
    "syn-view-switcher": "Server-selected view links or host-controlled view buttons; the host owns selection and navigation.",
    "syn-sheet": "Native popover or dialog side-sheet presentation; browser and host own opening, focus, and close behavior.",
    "syn-evidence-card": "Semantic figure-based evidence review presentation with captions and metadata, not a media viewer.",
    "syn-grid": "Responsive grid composition.",
    "syn-stats": "Container-responsive metric composition.",
    "syn-semantic": "Opt-in styling of native HTML elements.",
    "syn-u-flex": "Opt-in flexbox layout utility.",
    "syn-u-w-full": "Opt-in full-width utility.",
}
# Human-reviewed descriptions for the high-frequency interface surface.
# Keep actual interaction responsibilities explicit: these classes only style HTML.
CLASS_DOCS.update({
    "syn-actions": "Flexibly spaced action buttons or links; actions still need native behavior.",
    "syn-alert": "Inline informational or status notice; write the message in readable text.",
    "syn-alert--danger": "Danger-state variant of a text-based alert.",
    "syn-alert--success": "Success-state variant of a text-based alert.",
    "syn-alert--warning": "Warning-state variant of a text-based alert.",
    "syn-app-nav": "Navigation region styling for an application workspace.",
    "syn-app-shell": "Application shell layout for navigation and main content.",
    "syn-avatar": "Compact avatar presentation; provide meaningful image alternatives.",
    "syn-avatar--sm": "Small-size variant of avatar presentation.",
    "syn-avatar--lg": "Large-size variant of avatar presentation.",
    "syn-badge": "Compact status or category label; do not rely on color alone.",
    "syn-badge--accent": "Accent-emphasis variant of a badge or status label.",
    "syn-breadcrumbs": "Breadcrumb navigation styling; use a real navigation list.",
    "syn-button--danger": "Danger-emphasis variant for destructive actions; confirmation is host-owned.",
    "syn-button--ghost": "Low-emphasis ghost button appearance for native buttons or links.",
    "syn-button--icon": "Icon-only button variant; provide an accessible name.",
    "syn-button--outline": "Outlined button variant for secondary actions.",
    "syn-button--small": "Compact-size button variant; preserve accessible interaction targets.",
    "syn-button-group": "Grouped buttons or action links; each retains native semantics.",
    "syn-caption": "Secondary caption text for supporting context.",
    "syn-check": "Inline label layout for native checkbox or radio inputs; state remains native.",
    "syn-chip": "Compact metadata chip or filter label; state is host-owned.",
    "syn-code": "Inline or block code presentation; preserve native code semantics.",
    "syn-data-grid": "Enterprise data-grid presentation; selection, sorting and virtualization are host-owned.",
    "syn-data-grid__cell": "Data-grid cell part; use the data-grid structure and accessible row semantics.",
    "syn-data-grid__columnheader": "Column-header part of a data grid; real sorting is host-owned.",
    "syn-data-grid__row": "Data-grid row part; keyboard behavior and selection are host-owned.",
    "syn-details": "Native details/summary disclosure styling; use real HTML details.",
    "syn-dialog": "Native dialog presentation; opening and focus behavior are browser/host-owned.",
    "syn-display": "Large display typography for prominent page headings.",
    "syn-empty": "Empty-state content presentation; provide meaningful guidance or recovery actions.",
    "syn-error": "Visible form error text; associate with the relevant form control.",
    "syn-error-summary": "Form validation summary presentation; host provides actual errors and focus.",
    "syn-field": "Form field group for a native control, label, and optional help or error text.",
    "syn-field-row": "Responsive row composition for related form fields.",
    "syn-fieldset": "Native fieldset styling; retain a meaningful legend.",
    "syn-floating-label": "Floating label appearance; keep the input's accessible label.",
    "syn-form": "Consistent spacing and structure for semantic HTML forms.",
    "syn-form-actions": "Form submit/cancel action layout; server validation remains host-owned.",
    "syn-heading": "Default component or card heading typography.",
    "syn-help": "Supporting form help text; connect it with aria-describedby where appropriate.",
    "syn-inline": "Inline, wrapping layout for small groups of peers.",
    "syn-input": "Native form input styling; use a real input with an associated label.",
    "syn-input-group": "Input and addon grouping; form behavior remains native or host-owned.",
    "syn-kpi-grid": "Responsive grid of key performance indicator cards or metrics.",
    "syn-label": "Visible form label styling; use native label/for association.",
    "syn-layout": "Responsive multi-column layout with token-configurable minimum widths.",
    "syn-lede": "Lead paragraph typography beneath a heading.",
    "syn-list-group": "Grouped list presentation; preserve semantic list markup.",
    "syn-metric": "Emphasized numeric or measurement presentation with meaningful text.",
    "syn-muted": "Lower-emphasis supporting text; maintain readable contrast.",
    "syn-nav": "Navigation link group styling; use semantic nav and links.",
    "syn-nav-tabs": "Tab-like navigation styling; use links for pages, not fake ARIA tabs.",
    "syn-page-header": "Page heading and action area layout for applications.",
    "syn-pagination": "Pagination link and control presentation; host performs page changes.",
    "syn-panel--raised": "Raised-surface visual variant of a panel.",
    "syn-popover": "Native popover presentation; opening, focus and dismissal are host-owned.",
    "syn-pricing": "Responsive pricing card composition; commercial data is host-owned.",
    "syn-prose": "Readable long-form article typography with scoped content rhythm.",
    "syn-select": "Native HTML select styling; provide a label and valid options.",
    "syn-sheet-header": "Heading and close-action area inside a native sheet.",
    "syn-shell": "Constrained page-width container for a whole page or section.",
    "syn-sidebar": "Sidebar navigation or supporting-content layout.",
    "syn-skeleton": "Visual loading placeholder; do not mistake styling for live loading state.",
    "syn-stack": "Vertical layout with consistent, token-configurable spacing.",
    "syn-stat": "Single metric with value and explanatory label.",
    "syn-status": "Concise status label; include text independent of color.",
    "syn-step": "Single item in a semantic process or progress sequence.",
    "syn-steps": "Process sequence layout; status progression is host-owned.",
    "syn-table": "Native HTML table styling; preserve th, scope, and proper headers.",
    "syn-table--compact": "Compact-density native table variant.",
    "syn-table--sticky": "Sticky-header table presentation; check scroll and reflow behavior.",
    "syn-table--striped": "Alternating row background variant for a native table.",
    "syn-table-wrap": "Responsive overflow wrapper for a native table.",
    "syn-textarea": "Native multiline text field styling; pair with a label.",
    "syn-timeline": "Chronological event or activity layout; preserve event text and order.",
    "syn-toolbar": "Aligned row of controls and actions; keyboard interactions are host-owned.",
    "syn-u-sr-only": "Screen-reader-only text utility; retains content for assistive technology.",
    "syn-upload-field": "File-selection field presentation; native input or host owns file upload.",
    "syn-workspace": "Responsive application workspace layout with primary and supporting regions.",
})


def _readable_name(name: str) -> str:
    return name.removeprefix("syn-").replace("-", " ").replace("_", " ").strip()


def describe_class(name: str, module: str) -> str:
    """Prefer reviewed semantics; avoid suggesting unverified JS behavior."""
    if name in CLASS_DOCS:
        return CLASS_DOCS[name]
    if name.startswith("syn-u-"):
        return f"Optional {_readable_name(name.removeprefix('syn-u-'))} utility; load {module} when used."
    if "__" in name:
        parent, part = name.split("__", 1)
        part_name, _, modifier = part.partition("--")
        suffix = f" with {modifier.replace('-', ' ')} styling" if modifier else ""
        return (f"{_readable_name(part_name).capitalize()} part of the "
                f"{_readable_name(parent)} component{suffix}; see {module} for markup.")
    if "--" in name:
        parent, modifier = name.split("--", 1)
        return (f"{modifier.replace('-', ' ').capitalize()} appearance variant of "
                f"the {_readable_name(parent)} component; see {module} for styles.")
    return (f"{_readable_name(name).capitalize()} presentation in the "
            f"{module} module; use semantic HTML and consult its component example.")


TOKEN_DOCS = {
    "--syn-accent": "Theme accent color; also check --syn-on-accent contrast.",
    "--syn-on-accent": "Foreground color for the primary accent.",
    "--syn-bg": "Theme background.",
    "--syn-text": "Default text color.",
    "--syn-grid-alpha": "Grid-line accent share; varies by scoped data-syn-intensity.",
    "--syn-glow-alpha": "Glow accent share; varies by scoped data-syn-intensity.",
    "--syn-wash-alpha": "Primary atmospheric wash share.",
    "--syn-wash-secondary-alpha": "Secondary atmospheric wash share.",
    "--syn-horizon-alpha": "Horizon line accent share.",
    "--syn-scanline-alpha": "Scanline overlay opacity percentage.",
    "--syn-panel-padding": "Per-panel padding; defaults to the existing fluid panel padding.",
    "--syn-panel-radius": "Per-panel border radius; defaults to square corners.",
    "--syn-panel-border-width": "Per-panel border width; defaults to 1px.",
    "--syn-button-padding-inline": "Per-button inline padding; defaults to 1rem.",
    "--syn-button-border-width": "Per-button border width; defaults to 1px.",
    "--syn-sheet-width": "Maximum inline width of an optional record sheet; defaults to 30rem.",
    "--syn-grid-min": "Minimum grid track width; defaults to 17rem.",
    "--syn-grid-gap": "Grid gap; defaults to 1rem.",
    "--syn-layout-min": "Minimum layout track width; defaults to 21rem.",
    "--syn-layout-gap": "Layout gap; defaults to 1.25rem.",
    "--syn-stack-gap": "Stack gap; defaults to --syn-space-3.",
    "--syn-inline-gap": "Inline flex gap; defaults to --syn-space-2.",
    "--syn-kpi-min": "Minimum KPI grid track width; defaults to 13rem.",
    "--syn-kpi-gap": "KPI grid gap; defaults to --syn-space-2.",
    "--syn-filter-gap": "Wrapping filter-bar gap; defaults to --syn-space-2.",
    "--syn-filter-field-min": "Filter field basis and minimum; defaults to 11rem.",
    "--syn-filter-query-min": "Query field flex basis; defaults to 18rem.",
    "--syn-detail-gap": "Detail shell gap; defaults to --syn-space-3.",
    "--syn-detail-main-basis": "Detail main flex basis; defaults to 32rem.",
    "--syn-detail-main-min": "Detail main minimum width; defaults to 22rem.",
    "--syn-detail-aside-basis": "Detail aside flex basis; defaults to 17rem.",
    "--syn-detail-aside-min": "Detail aside minimum width; defaults to 17rem.",
    "--syn-frame-cut": "Shared fallback corner size for optional geometry shapes.",
    "--syn-frame-cut-tl": "Optional top-left frame cut size.",
    "--syn-frame-cut-tr": "Optional top-right frame cut size.",
    "--syn-frame-cut-br": "Optional bottom-right frame cut size.",
    "--syn-frame-cut-bl": "Optional bottom-left frame cut size.",
    "--syn-frame-stroke": "Width of the optional shape-following border.",
    "--syn-frame-fill": "Interior fill paint for optional shaped frames.",
    "--syn-frame-outline": "Solid border paint fallback for optional frames.",
    "--syn-frame-border-paint": "Solid or gradient border paint for optional frames.",
    "--syn-frame-inlay-paint": "Optional translucent overlay on the inner shaped surface.",
}
# Reviewed token roles for common design and accessibility controls.
TOKEN_DOCS.update({
    "--syn-bg": "Theme background color for the scoped Syntyr root.",
    "--syn-text": "Default foreground text color; check contrast against the current surface.",
    "--syn-surface": "Primary surface color for panels and grouped content.",
    "--syn-surface-raised": "Raised surface color for elevated interface regions.",
    "--syn-surface-recessed": "Recessed surface color for inset interface regions.",
    "--syn-frame": "Default frame or border color within the current theme.",
    "--syn-muted": "Subdued text color for secondary content; retain readable contrast.",
    "--syn-danger": "Semantic danger color; do not communicate errors through color alone.",
    "--syn-success": "Semantic success color for positive states.",
    "--syn-warning": "Semantic warning color for attention states.",
    "--syn-focus-ring": "Focus indication styling for keyboard-visible focus states.",
    "--syn-control-height": "Shared native form control height; check accessible target sizing.",
    "--syn-control-padding-block": "Vertical padding used by shared form controls.",
    "--syn-radius": "Common corner radius for compatible components.",
    "--syn-shadow-raised": "Shadow treatment for visually elevated surfaces.",
    "--syn-shadow-overlay": "Overlay elevation shadow used by appropriate floating surfaces.",
    "--syn-type-body": "Body typography size role; override consistently across components.",
    "--syn-type-heading": "Heading typography size role for component and page hierarchy.",
    "--syn-type-display": "Large display typography size role for emphasized headings.",
    "--syn-type-section": "Section-heading typography size role.",
    "--syn-font-ui": "Font family used by common interface controls and components.",
    "--syn-font-display": "Font family used for display headings.",
})


def describe_token(name: str, module: str) -> str:
    """Explain token purpose conservatively when no reviewed description exists."""
    if name in TOKEN_DOCS:
        return TOKEN_DOCS[name]
    label = name.removeprefix("--syn-").replace("-", " ")
    if name.startswith("--syn-space-"):
        return f"Spacing scale token {name.removeprefix('--syn-space-')}; use for consistent layout spacing."
    if name.startswith("--syn-duration-"):
        return f"Motion duration token {label}; respect user reduced-motion preferences."
    if name.startswith("--syn-ease"):
        return f"Motion easing token {label}; use only for optional transitions."
    if name.startswith("--syn-type-"):
        return f"Typography scale role {label}; use consistently within the theme."
    if name.startswith("--syn-font-"):
        return f"Font family design token {label}; retain a readable fallback."
    if name.startswith("--syn-shadow-"):
        return f"Surface shadow design token {label}; reserve elevation for meaningful hierarchy."
    if name.startswith("--syn-chart-"):
        return f"Chart presentation design token {label}; provide non-color chart labels."
    return (f"{label.capitalize()} design token from {module}; "
            "override in the appropriate Syntyr scope when needed.")


# These overrides have CSS var() fallbacks, and are still valid documented API.
EXPLICIT_TOKENS = {
    "--syn-panel-padding": "components/layout.css",
    "--syn-panel-radius": "components/layout.css",
    "--syn-panel-border-width": "components/layout.css",
    "--syn-button-padding-inline": "components/buttons.css",
    "--syn-button-border-width": "components/buttons.css",
    "--syn-sheet-width": "recipes.css",
    "--syn-grid-min": "components/layout.css",
    "--syn-grid-gap": "components/layout.css",
    "--syn-layout-min": "components/layout.css",
    "--syn-layout-gap": "components/layout.css",
    "--syn-stack-gap": "components/layout.css",
    "--syn-inline-gap": "components/layout.css",
    "--syn-kpi-min": "recipes.css",
    "--syn-kpi-gap": "recipes.css",
    "--syn-filter-gap": "recipes.css",
    "--syn-filter-field-min": "recipes.css",
    "--syn-filter-query-min": "recipes.css",
    "--syn-detail-gap": "recipes.css",
    "--syn-detail-main-basis": "recipes.css",
    "--syn-detail-main-min": "recipes.css",
    "--syn-detail-aside-basis": "recipes.css",
    "--syn-detail-aside-min": "recipes.css",
    "--syn-animation-iterations": "motion.css",
    "--syn-frame-cut": "geometry.css",
    "--syn-frame-cut-tl": "geometry.css",
    "--syn-frame-cut-tr": "geometry.css",
    "--syn-frame-cut-br": "geometry.css",
    "--syn-frame-cut-bl": "geometry.css",
    "--syn-frame-stroke": "geometry.css",
    "--syn-frame-fill": "geometry.css",
    "--syn-frame-outline": "geometry.css",
    "--syn-frame-border-paint": "geometry.css",
    "--syn-frame-inlay-paint": "geometry.css",
}
# Only permit literal, CSS-implemented presentation states. Curated choices
# must not omit states used by optional server or visualization stylesheets.
CSS_STATE = re.compile(r'\[\s*data-syn-state\s*=\s*["\']([^"\']+)["\']\s*\]')


def source_state_values() -> list[str]:
    values = set()
    for path in SOURCE.rglob("*.css"):
        values.update(CSS_STATE.findall(CSS_COMMENT.sub("", path.read_text(encoding="utf-8"))))
    return sorted(values)


SNIPPET_CLASSES = (
    "syn-root", "syn-panel", "syn-button", "syn-button--primary",
    "syn-region", "syn-grid", "syn-stats", "syn-form",
    "syn-input", "syn-semantic", "syn-u-flex", "syn-u-w-full",
)


def collect():
    classes = {}
    tokens = {}
    # Honor the public build manifest. Source ownership differs by API kind:
    # class definitions live in base/components/recipes, while primary theme
    # token declarations live in tokens.css (not their print-mode overrides).
    sources = list(dict.fromkeys(path for modules in distributions().values() for path in modules))
    css_by_module = {
        path: CSS_COMMENT.sub("", (SOURCE / path).read_text(encoding="utf-8"))
        for path in sources
    }
    class_sources = sorted(sources, key=lambda path: (path == "tokens.css", path == "print.css"))
    for path in class_sources:
        for name in CLASS.findall(css_by_module[path]):
            classes.setdefault(name, path)
    token_sources = sorted(sources, key=lambda path: (path != "tokens.css", path == "print.css"))
    for path in token_sources:
        for name in TOKEN.findall(css_by_module[path]):
            tokens.setdefault(name, path)
    for name, path in EXPLICIT_TOKENS.items():
        content = (SOURCE / path).read_text(encoding="utf-8")
        if "var(" + name not in content:
            raise ValueError(f"Declared public token is not referenced: {name}")
        tokens.setdefault(name, path)
    if not set(SNIPPET_CLASSES).issubset(classes):
        raise ValueError(f"Missing class from snippets: {set(SNIPPET_CLASSES) - set(classes)}")
    themes = sorted(set(THEME.findall((SOURCE / "tokens.css").read_text(encoding="utf-8"))))
    return {
        "version": 1,
        "classes": [{"name": name, "module": classes[name],
                     "description": describe_class(name, classes[name])}
                    for name in sorted(classes)],
        "tokens": [{"name": name, "module": tokens[name],
                    "description": describe_token(name, tokens[name])}
                   for name in sorted(tokens)],
        "themes": themes,
    }



def validate_recipes(recipes, class_stylesheets, attributes):
    """Check curated multi-part recipes against actual source-discovered CSS.

    Recipes are compositional guidance, never runtime widgets or strict HTML
    authoring rules. Validation catches stale classes and missing modules.
    """
    ids = set()
    for recipe in recipes:
        ident = recipe["id"]
        if not re.fullmatch(r"[a-z][a-z0-9-]*", ident) or ident in ids:
            raise ValueError(f"invalid or duplicate recipe id: {ident}")
        ids.add(ident)
        stylesheet_names = recipe.get("stylesheets")
        if (not isinstance(stylesheet_names, list) or not stylesheet_names
                or any(not isinstance(name, str) or not name for name in stylesheet_names)):
            raise ValueError(f"{ident}: stylesheets must be a nonempty list of strings")
        stylesheets = set(stylesheet_names)
        distributions = all_distributions()
        unknown_stylesheets = stylesheets - set(distributions)
        if unknown_stylesheets:
            raise ValueError(f"{ident}: unknown stylesheet: {sorted(unknown_stylesheets)}")
        if any(name.startswith("components/") for name in stylesheets):
            supplied_sources = {
                source for name in stylesheets for source in distributions[name]
            }
            if not {"tokens.css", "base.css"}.issubset(supplied_sources):
                raise ValueError(f"{ident}: component CSS requires tokens and base")
        if not recipe["description"].strip() or not recipe["host_behavior"].strip():
            raise ValueError(f"{ident}: missing descriptive or host behavior contract")
        example = recipe["example"]
        if not example.startswith("examples/") or ".." in Path(example).parts or not (ROOT / example).is_file():
            raise ValueError(f"{ident}: example not found: {example}")
        root = recipe.get("root")
        if not isinstance(root, dict) or not all(
            key in root for key in ("tag", "classes")
        ):
            raise ValueError(f"{ident}: root requires tag and classes")
        slots = recipe.get("slots")
        if not isinstance(slots, list):
            raise ValueError(f"{ident}: slots must be an array")
        slot_names = set()
        for part in slots:
            if not isinstance(part, dict) or any(
                key not in part for key in ("name", "tag", "classes", "optional", "repeatable")
            ) or not isinstance(part.get("name"), str) or not part["name"].strip():
                raise ValueError(f"{ident}: required slot name, tag, classes and flags")
            if part["name"] in slot_names:
                raise ValueError(f"{ident}: duplicate slot: {part['name']}")
            slot_names.add(part["name"])
            if not isinstance(part["optional"], bool) or not isinstance(part["repeatable"], bool):
                raise ValueError(f"{ident}: required slot flags must be booleans")
        for part in [root] + slots:
            if not isinstance(part["tag"], str) or not re.fullmatch(r"[a-z][a-z0-9-]*", part["tag"]):
                raise ValueError(f"{ident}: invalid HTML tag: {part['tag']}")
            if not isinstance(part["classes"], list) or not part["classes"]:
                raise ValueError(f"{ident}: slot missing classes")
            for name in part["classes"]:
                if name not in class_stylesheets:
                    raise ValueError(f"{ident}: unknown class: {name}")
                if not class_stylesheets[name].intersection(stylesheets):
                    raise ValueError(f"{ident}: class {name} not loaded by {sorted(stylesheets)}")
        variants = recipe.get("variants", {})
        if not isinstance(variants, dict):
            raise ValueError(f"{ident}: variants must be an object")
        for attribute, values in variants.items():
            if (not isinstance(values, list) or not values
                    or any(not isinstance(value, str) for value in values)):
                raise ValueError(f"{ident}: variant {attribute} requires a nonempty list of strings")
            if attribute not in attributes or not set(values).issubset(attributes[attribute]):
                raise ValueError(f"{ident}: unsupported variant {attribute}: {values}")


def component_contract(api, html_data):
    """Full source-discovered inventory plus curated semantic component recipes.

    This is tooling metadata, not a second, separately maintained CSS API.
    The curated component list describes compositions, not class-by-class
    allowed elements; those must not be treated as strict static rules.
    """
    distributions_by_name = all_distributions()
    curated = json.loads((OUTPUT / "components.json").read_text(encoding="utf-8"))
    known_classes = {item["name"] for item in api["classes"]}
    for component in curated["components"]:
        unknown = sorted(set(component["classes"]) - known_classes)
        if unknown:
            raise ValueError(f"Curated {component['name']} uses unknown classes: {unknown}")
        if component["module"] not in distributions_by_name:
            raise ValueError(f"Unknown component distribution: {component['module']}")

    def with_stylesheets(items):
        return [
            {**item, "stylesheets": sorted(
                name for name, modules in distributions_by_name.items()
                if item["module"] in modules
            )}
            for item in items
        ]

    attributes = {
        attribute["name"]: [value["name"] for value in attribute["values"]]
        for attribute in html_data["globalAttributes"]
        if attribute["name"].startswith("data-syn-") and "values" in attribute
    }
    class_stylesheets = {
        item["name"]: set(item["stylesheets"]) for item in with_stylesheets(api["classes"])
    }
    validate_recipes(curated.get("recipes", []), class_stylesheets, attributes)

    return {
        "schema_version": 1,
        "source_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "completeness": "all-source-discovered-classes-and-tokens; curated-components",
        "note": "Curated component elements are guidance, not per-class tag restrictions.",
        "stylesheets": sorted(distributions_by_name),
        "classes": with_stylesheets(api["classes"]),
        "tokens": with_stylesheets(api["tokens"]),
        "themes": api["themes"],
        "attributes": attributes,
        "components": curated["components"],
        "recipes": curated.get("recipes", []),
    }


def outputs():
    api = collect()
    classes = api["classes"]
    themes = api["themes"]
    html = {
        "version": 1.1,
        "globalAttributes": [
            {"name": "class", "description": "Syntyr class names in the optional syn-* styling API.",
             "values": [{"name": c["name"], "description": c["description"]} for c in classes]},
            {"name": "data-syn-theme", "description": "Syntyr theme selector (on syn-root or a nested region).",
             "values": [{"name": theme} for theme in themes]},
            {"name": "data-syn-intensity", "description": "Opt-in decorative intensity independent of theme and density.",
             "values": [{"name": name} for name in ("quiet", "standard", "cinematic")]},
            {"name": "data-syn-density", "description": "Opt-in presentation density.",
             "values": [{"name": name} for name in ("compact", "comfortable", "spacious")]},
            {"name": "data-syn-color-space", "description": "Experimental opt-in OKLCH hover mixing; default remains sRGB.",
             "values": [{"name": "oklch"}]},
            {"name": "data-syn-state", "description": "Host-managed decorative state, not an ARIA substitute.",
             "values": [{"name": name} for name in source_state_values()]},
            {"name": "data-syn-featured", "description": "Decorative featured pricing card state."},
        ],
    }
    css = {
        "version": 1.1,
        "properties": [{"name": token["name"], "description": token["description"]} for token in api["tokens"]],
    }
    snippets = {
        f"Syntyr: {name}": {
            "prefix": name,
            "scope": "html,javascriptreact,typescriptreact",
            "body": name,
            "description": CLASS_DOCS.get(name, "Syntyr class."),
        }
        for name in SNIPPET_CLASSES
    }
    payloads = {
        "syntyr-contract.json": component_contract(api, html),
        "syntyr-api.json": api,
        "syntyr.html-custom-data.json": html,
        "syntyr.css-custom-data.json": css,
        "syntyr.code-snippets": snippets,
    }
    return {OUTPUT / file: json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            for file, data in payloads.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check committed exports against CSS")
    args = parser.parse_args(argv)
    failures = 0
    for path, result in outputs().items():
        if args.check:
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != result:
                print(f"STALE {path.relative_to(ROOT)}")
                failures += 1
            else:
                print(f"OK {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(result, encoding="utf-8")
            print(f"WROTE {path.relative_to(ROOT)}")
    return int(failures > 0)


if __name__ == "__main__":
    sys.exit(main())
