# Syntyr editor autocomplete and metadata

Syntyr's editor integration is **optional**. Applications still consume ordinary
prebuilt CSS, HTML, and custom properties without Node, JavaScript, or a build step.

## VS Code and compatible editors

For an opt-in local extension package that bundles these files without an extension runtime, see [ecosystem interoperability](ecosystem-integrations.md). The extension is not yet published to the VS Code Marketplace; the manual workspace integration below remains supported.

Copy these four generated files from the Syntyr release or repository into
your project, e.g. `./vendor/syntyr/metadata/`:

- `syntyr.html-custom-data.json` — HTML attribute values, including themes
- `syntyr.css-custom-data.json` — documented `--syn-*` custom properties
- `syntyr.code-snippets` — a curated set of class completion snippets
- `syntyr-api.json` — complete machine-readable index of classes, tokens and themes

Add the following to your **workspace** `.vscode/settings.json` (not required
for Syntyr consumers using other editors):

```json
{
  "html.customData": ["./vendor/syntyr/metadata/syntyr.html-custom-data.json"],
  "css.customData": ["./vendor/syntyr/metadata/syntyr.css-custom-data.json"]
}
```

Optionally copy `syntyr.code-snippets` to `.vscode/syntyr.code-snippets`.
This provides snippets for common `syn-*` classes in HTML and JSX/TSX. The
custom HTML data includes all classes as possible `class` attribute values,
but the extent of **class-name completion** varies by editor and extension;
do not assume it works identically in every language mode. CSS custom
property autocomplete also depends on the editor's CSS language support.

The JSON files are standard, inspectable data; other editors and integrations
can consume `syntyr-api.json` directly.

## Audit CSS class and token collisions

The optional standard-library namespace audit compares actual class selectors
and `--syn-*` **declarations** in another stylesheet with the
source-derived public Syntyr inventory. It does not require npm or install
anything in the consuming application.

```sh
python3 scripts/audit_class_collisions.py --css /path/to/host.css
python3 scripts/audit_class_collisions.py --css /path/to/bootstrap.css \
  --css /path/to/other.css --json
# Optional CI check (nonzero exit on any exact public-name collision):
python3 scripts/audit_class_collisions.py --css /path/to/host.css --fail-on-overlap
```

The JSON report includes the number of external class selectors, exact class
overlaps, externally defined `syn-*` selectors, exact CSS custom-property
overlaps, and externally declared `--syn-*` properties. A collision is not
automatically a defect, but investigate which stylesheet owns the name and
whether the two regions are intended to coexist.

**Scope:** explicit CSS selectors and custom-property declarations only.
The auditor does not execute a utility compiler, expand dynamic class
generation or concatenated nesting suffixes, or analyze global element
selectors, CSS resets, layer priority, specificity, Shadow DOM, or actual
browser rendering. For Tailwind and other generated systems, audit the
**compiled output for the particular app**, then test the combined page in
a browser. The `.syn-root` scope and zero-specificity wrappers reduce
interference but do not provide complete isolation from host styles.

A point-in-time audit of pinned public distributions (Bootstrap 5.3.3,
Bulma 1.0.2, daisyUI 5.8.0) found **zero exact public `syn-*` class or
`--syn-*` declaration collisions**. This is a limited three-package
sample, not an ecosystem-wide collision-rate estimate.

## Regenerate after CSS changes

From the Syntyr source repository:

```sh
python3 scripts/export_api_metadata.py
python3 scripts/export_api_metadata.py --check
```

The Python standard-library exporter scans `src/**/*.css`, strips comments,
deduplicates discovered classes and declared custom properties, adds
documented component override variables, and writes stable JSON and snippets.
`--check` fails if the checked-in outputs differ from source.
Descriptions are human-reviewed for common components and design tokens;
remaining entries use conservative class/token-name and source-module labels.
Automatically derived descriptions are discovery hints, not guarantees of
behavior, accessibility or applicable HTML elements.

This is an editor convenience layer, **not** a Tailwind-style CSS compiler.
A class being present in the metadata does not mean its optional stylesheet
is already loaded. Check each item's `module` in the generated catalog and
load the corresponding Syntyr CSS distribution.

## Generated portable component gallery for builders

The source-tree candidate also ships [component-gallery.v1.json](../metadata/component-gallery.v1.json),
an **optional, framework-neutral** static contract for documentation,
visual editors and AI-assisted composition. It is derived automatically from
the curated `metadata/components.json` and the actual native HTML examples
in `docs/catalog.html`, not another manually authored component registry.

The manifest also carries the curated `recipes[]` with slots and variants,
plus theme names from the generated CSS API metadata (not a new theme
registry). Each `components[]` entry is the existing curated metadata. Each
`examples[]` entry has a stable `id`, title, description, searchable
keywords, native HTML, semantic element names, actual `syn-*` classes, and
`required_stylesheets`. The stylesheet list can include the separately opt-in
semantic CSS module; loading `syntyr.core.css` alone is not always sufficient.
The `module` field preserves the primary stylesheet shown in the gallery.

### Select HTML examples by task and installed CSS

Every example now includes **curated, non-exclusive `use_cases`** tags, stable
`catalog_url` and `playground_url` fragments, plus the exact
`required_stylesheets` list. The top-level `use_case_definitions` explains
the five supported tags: `marketing-site`, `saas-dashboard`,
`forms-workflow`, `content-docs`, and `navigation`.
The `adoption_guidance` field describes CSS order, framework guidance,
release boundaries, and browser fallback obligations. These are **discovery
hints**, not a guarantee that a component implements application behavior.

An editor or agent can select candidates deterministically without executing
a runtime or downloading packages:

```python
import json
from pathlib import Path

gallery = json.loads(Path("metadata/component-gallery.v1.json").read_text())
installed = {"syntyr.core.css", "syntyr.recipes.css"}  # actual installed files
candidates = [
    example for example in gallery["examples"]
    if "saas-dashboard" in example["use_cases"]
    and set(example["required_stylesheets"]).issubset(installed)
]
for example in candidates:
    print(example["title"], example["catalog_url"], example["required_stylesheets"])
```

Use the selected example's `html` with a stable `.syn-root` ancestor and
honor its CSS dependencies in order. Follow `playground_url` to inspect or
edit it, and check `native_feature_requirements` before shipping. An empty
feature list only means no *tracked* native interaction APIs were detected.
The gallery's CSS-module and use-case dropdowns use the **same authored
catalog card labels and use-case tags** as this generated JSON; scripts are
needed only for gallery convenience, not for rendered Syntyr components.

The additive `native_feature_requirements` array on each example records only
three *detectable native HTML interaction contracts*: `popover`,
`invoker-commands`, and `details-name`. These are derived from the example's
parsed HTML, not its title or CSS theme. The companion
`native_browser_features` dictionary supplies a short fallback description
and an MDN documentation URL for each feature. Empty requirements mean **none
of these three detected features**, not universal browser compatibility.
The metadata intentionally omits unsupported browser-version guarantees, CSS
feature detection, and false claims that application behaviors are complete.
The optional gallery filter uses the same native element/attribute criteria,
without JavaScript dependencies for consuming Syntyr CSS.

From a source checkout, regenerate and verify with:

```sh
python3 scripts/build_component_gallery.py
python3 scripts/build_component_gallery.py --check
```

The public documentation catalog adds optional theme and compact-width preview
controls. Without JavaScript, all previews and visible source snippets remain
available. None of these controls or generator scripts ships in core CSS.

**Safety and compatibility:** the JSON is a library of trusted, checked-in
examples, not an HTML sanitizer or a guarantee that examples implement business
behavior. Treat incoming user markup separately. Component classes require a
`.syn-root` ancestor, the installed release must provide the listed CSS
modules, and the **unreleased alpha.5 source candidate** must not be mistaken
for the published alpha.4 release. HTML form actions, billing, data, dialogs,
and application state are controlled by the host platform.

## Optional static HTML diagnostics

The generated `metadata/syntyr-contract.json` is Syntyr's machine-readable
development contract. It combines the **full source-discovered** class and token
inventory with the existing **curated** semantic component recipes, supported
theme/state values, and CSS distribution filenames. The contract is generated
by `python3 scripts/export_api_metadata.py` and checked by `--check`. Do
not edit it directly. The existing `metadata/components.json` remains a
curated subset and is not a complete list of classes.

To validate static HTML during development (Python 3.10+, standard library only):

```sh
python3 scripts/syntyr_check.py index.html examples/saas.html
python3 scripts/syntyr_check.py --format json index.html
# Opt-in, conservative native HTML checks (warnings do not fail the CLI):
python3 scripts/syntyr_check.py --semantic --format json examples/semantic-starter.html
python3 scripts/syntyr_check.py --stylesheets syntyr.core.css,syntyr.recipes.css partial.html
# Pipe generated markup into the same deterministic checker without a temporary file:
printf '<button class="syn-buttn">Save</button>' | python3 scripts/syntyr_check.py --format json -
# For fragments, supply the CSS modules actually installed in the consumer app:
cat fragment.html | python3 scripts/syntyr_check.py --format json --stylesheets syntyr.core.css -
```

### Agent-ready composition recipes

The same generated `metadata/syntyr-contract.json` includes an optional
`recipes` array curated in `metadata/components.json`. Each recipe declares:

- A stable `id`, purpose, example page and required CSS distributions.
- A native HTML `root` element and named `slots` with `tag`, `classes`,
  `optional` and `repeatable` fields.
- `variants` restricted to real, CSS-supported `data-syn-*` attribute values.
- `host_behavior` explaining what CSS **cannot** perform (server requests,
  selection, pagination, validation, focus or authorization).

Available recipes cover a CRM filter form, semantic resource table, app shell,
and validated form. Use a `.syn-root` ancestor for every composition, and load
all listed stylesheets in the documented order (core before optional recipes).
The contract's `slots` describe roles, **not a strict DOM nesting validator**;
authors must still use accessible native HTML in context. The host application
supplies state and behavior. No JavaScript component engine is required.

Source truth is the existing curated `metadata/components.json`, not another
hand-maintained metadata registry. After editing a recipe, run
`python3 scripts/export_api_metadata.py` to regenerate the contract;
`python3 scripts/export_api_metadata.py --check` detects drift. The exporter
rejects stale class names, missing CSS modules, unsupported variant values,
invalid example paths and duplicate slot names before publication.

The checker reports source positions, unknown literal `syn-*` classes, invalid
literal `data-syn-*` values, and missing optional CSS modules **when a Syntyr
stylesheet is linked or explicitly specified**. For full HTML documents with
an explicit `<html>` element, it also reports `unscoped-class` when a known
Syntyr component class is outside every `.syn-root` ancestor. Since CSS
selectors are scoped, those classes would otherwise silently render without
Syntyr styles. Plain HTML fragments are exempt because the embedding app may
supply the root; dynamic ancestor classes and inert `<template>` contents are
also exempt because their rendered scope is unknown.

### Inspect stylesheet loading with CSS Doctor

Use the same validator with `--doctor` to inspect literal stylesheet links:

```sh
python3 scripts/syntyr_check.py --doctor --semantic --format json index.html
```

Repeated Syntyr links and distributions sharing canonical CSS sources produce
advisory warnings; different explicit semantic-version pins in `/v/<version>/`
paths produce errors. The source-ownership map comes from the generated current
candidate contract, including presets and atomic component files. Conditional
stylesheets may overlap intentionally; review warnings rather than automatically
removing files. Unpinned local paths, bundler imports and actual downloaded CSS
versions are not inferred. This is static inspection, not browser cascade,
security or accessibility certification. Default validation is unchanged.

### Inspect design token references

Add `--tokens` to inspect literal inline `var(--syn-…)` references against
the selected contract's token inventory. Unknown names include suggested
canonical spellings and provider stylesheets. Known references without a
declared provider produce advisory warnings. The check does not determine
computed values, resolve inheritance or infer custom host definitions.
It skips locally declared tokens, templates, CSS strings/comments and
ambiguous escaped or URL-bearing inline styles; external CSS and style
blocks are not analyzed. Warnings do not alter default validation or fail
the CLI.

```sh
python3 scripts/syntyr_check.py --doctor --tokens --semantic --format json index.html
```

With `--semantic`, a second standard-library pass checks literal HTML for
duplicate static IDs, missing form labels (including an unnamed `input
type="image"` or `type="button"`), unmatched `label for` and
`aria-labelledby`/`aria-describedby` ID references (the latter two only in
complete documents). For complete HTML it also detects missing `popovertarget`
or `commandfor` IDs and popover triggers that point to elements without a
`popover` attribute. Controls in a `hidden` subtree are exempt from
accessible-name checks, but still have literal invoker targets validated.
A nonempty `title` is accepted as an accessible-name fallback for native
button/image inputs; dynamic names do not suppress static target validation.
It advises when an ordinary table row uses
`aria-selected` instead of `data-syn-state`, or when a headed data table
lacks a caption or other accessible name. Errors produce exit code 1; advisory
warnings are included in text/JSON output but do not fail the command.
The mode is **off by default** to preserve existing integrations.

This is not an HTML conformance parser, a WCAG audit, or a template renderer.
It deliberately skips inert template content and avoids guessing what dynamic
attributes resolve to. Validate rendered server/framework templates and actual
screen-reader behavior separately. Static fragments may reference IDs supplied
by their embedding document, so cross-document references are checked only
when a full `<html>` document is supplied.

The checker recognizes local and version-pinned stylesheet paths (including
query parameters). Without a known Syntyr stylesheet, module-presence checks
are skipped, but root-scope checks still run for complete documents. Explicit
`--stylesheets` overrides stylesheet-link discovery.

Exit code 0 means no diagnostics, 1 means findings, and 2 means invalid
arguments or unreadable files. JSON diagnostics contain `file`, `line`,
`column`, `severity`, `code` and `message` fields. Input `-` reads HTML
from standard input and identifies findings with `file: "<stdin>"`; JSON stays
a top-level diagnostics array for backward compatibility. Agent-friendly
optional fields include `suggestions` (up to three real source-contract class
names with available stylesheet distributions), `class_name` and
`required_root` (unscoped component classes), `attribute` and
`allowed_values` (invalid theme or state), and `required_stylesheets` and
`loaded_stylesheets` (missing CSS modules). Suggestions are hints, **not**
automatic edits; confirm the target class exists in the **installed** release.

**Boundaries:** This is a static HTML checker, not a full HTML accessibility
auditor, runtime type checker, or an HTML/CSS build requirement. Dynamic
template class expressions are conservatively skipped. Component `elements`
describe composite examples rather than allowed tags for every constituent
class; the validator deliberately does not enforce those as strict rules.
JSX/TSX, HEEx, Blade, and Nulang template adapters would need separate
language-aware parsing. Semantic accessibility and actual loaded CSS still
need browser and keyboard checks. No script or generated manifest is shipped
to the browser by this integration.
