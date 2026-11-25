# Using Syntyr with coding agents

Syntyr works with ChatGPT, Codex, Claude Code, Cursor and other agents that generate HTML or framework markup. No Syntyr-specific service, account, MCP server or runtime JavaScript is required.

## Recommended context to supply an agent

1. Specify **the exact Syntyr release and CSS modules installed** (published `0.3.0-alpha.4` versus unreleased source `0.3.0-alpha.5`).
2. Link to [AI quickstart](ai-quickstart.md) and the relevant [component reference](components.md). If the agent can fetch websites, include [`/llms.txt`](../llms.txt).
3. For complex UI, supply [recipes](recipes.md), [framework integrations](framework-integrations.md) and the [component manifest](../metadata/components.json). For unreleased alpha.5 source-only form patterns, use [copy-owned form recipes](component-recipes.md) and the optional [Radix styling adapter](radix-integration.md); do not attribute these to published alpha.4.
4. Ask it to state which stylesheets it used, avoid undocumented classes and verify keyboard/form semantics.

Suggested prompt for an existing application:

> Use Syntyr CSS to build a responsive, accessible account dashboard. My app uses the published v0.3.0-alpha.4 core and recipes CSS, with Studio as the theme. Read the Syntyr AI quickstart and relevant component docs. Generate semantic HTML compatible with my framework. Use only classes present in those stylesheets; if a needed component is unavailable, compose native HTML with application CSS instead. Keep data, auth and actions in the host app. Return the necessary markup, CSS links and a list of any custom styles.

## Project-level integration

A consumer may copy [`agents/syntyr/SKILL.md`](../agents/syntyr/SKILL.md) as an optional local skill in agent tooling that supports Skills. It is a portable instruction document, **not a published package, automatic installation, or guaranteed discovery mechanism**.

The repository's root `AGENTS.md` guides agents contributing to Syntyr itself. It does **not** automatically become instructions in a separate application repository.

## Offline first-run agent setup (source checkout)

An optional Python standard-library command installs a **portable consumer Skill**,
release-pinned CSS, and a small verified selector reference into an existing app.
It runs from a Syntyr source checkout and does **not** install any application
runtime dependencies, connect to services, or publish a package:

```sh
python3 scripts/syntyr_agent.py init --project /path/to/my-app --json
python3 scripts/syntyr_agent.py info --project /path/to/my-app --json
python3 scripts/syntyr_agent.py check --project /path/to/my-app --json /path/to/my-app/page.html
```

`init` defaults to the **published, immutable alpha.4 CSS** and writes
`syntyr.agent.json`, versioned CSS files under `vendor/syntyr/<release>/`,
and `.agents/skills/syntyr/SKILL.md` plus `references/api.json`. Rerunning is
idempotent. Different existing files or symlinked output paths are rejected
without overwriting project content. For tooling that expects another skill
location, specify `--agent claude` or `--agent cursor`; `--agent codex` and
`--agent generic` use the portable `.agents/skills/` path. Projects must still
load the copied CSS in their own HTML/framework entrypoint: installation does
**not** silently modify application code or guarantee CSS integration.

Choose `--release 0.3.0-alpha.5` only when deliberately testing the
**unreleased source candidate**. The generated `api.json` lists selectors
actually present in the selected CSS files; source-only selectors cannot
appear in an alpha.4 reference.

`info` is read-only project discovery for coding agents. It reports the configured
release (published or source candidate), its actual pinned CSS asset hashes and
integrity statuses, supported themes, and portable Skill/reference paths. Exit
code **0** means the pinned installation is healthy, **1** means degraded or
invalid, and **2** means the project was not initialized. Do not infer active
stylesheet imports or framework support from this inventory: the host
application must still load and test the appropriate CSS. The command does
not scan application code or need application dependencies.

`check` validates the installed CSS asset hashes and literal `.html` files\nagainst that project's pinned release, returning structured, source-located
JSON diagnostics. Its exit codes are **0** for checked and error-free HTML,
**1** for errors, and **2** for incomplete coverage (for example, JSX/TSX or
no HTML files). It is not a React/Vue/Svelte parser or a browser accessibility
test. Generated CSS assets are not proof that the app has actually imported
them. The separate local MCP adapter remains available for smaller markup
fragments and interactive catalog queries.

## Optional local MCP adapter

An optional **read-only local MCP server** can now expose the checked-in
component catalog and CSS API to supported coding agents. It is not needed to
use Syntyr CSS, is not installed by the npm package, and does not expose a
hosted endpoint. See the [MCP adapter source and installation guide](https://github.com/dporkka/syntyr-css/tree/main/agent_mcp)
for the separate Python SDK installation, version-safe tools, and limits.
It defaults to the published immutable `0.3.0-alpha.4` CSS rather than
silently offering source-only `0.3.0-alpha.5` selectors. The read-only
`validate_markup` tool reuses the [static checker](editor-integration.md#optional-static-html-diagnostics)
for source-located, machine-readable errors, available class suggestions, and
valid theme/state values. Responses are constrained to the selected release's
checked-in CSS rather than presenting candidate-only selectors as fixes.

## Documents and machine-readable inventory

- [`llms.txt`](../llms.txt): small navigation file following the community `llms.txt` convention; it is useful when deliberately retrieved, but not a universal automatic-discovery protocol.
- [`llms-full.txt`](../llms-full.txt): generated, version-stamped concatenation of selected public technical docs, for tools that benefit from one context file.
- [`metadata/components.json`](../metadata/components.json): small **curated, non-exhaustive** inventory with the CSS modules required by the included classes. Do not infer that a class is unavailable solely because this catalog omits it.
- [`metadata/syntyr-contract.json`](../metadata/syntyr-contract.json): full source-discovered Syntyr classes, tokens, known stylesheet distributions, themes, literal state values and curated component recipes. This candidate-version manifest is suitable for LLM tooling and optional [static HTML checks](editor-integration.md#optional-static-html-diagnostics); it is not a compiler or an accessibility certification.

Documentation follows the current source candidate; always check [release boundaries](api-stability.md) and the [distribution guide](distribution.md) before using candidate-only features.

## Documentation formats: HTML for people, Markdown for agents

Every approved public guide is published at two stable paths. Use the readable HTML page (for example, [`/docs/components.html`](components.html)) in browser navigation, search results and links to end users. Use the original Markdown (`/docs/components.md`) for coding-agent retrieval, repository editing and `llms.txt` references. The [complete HTML guide directory](reference.html) is the human entry point. Both formats contain the same authored guide content; the HTML is rendered ahead of time, not by client-side JavaScript.

These are **different representations of the same public documentation**, not user-agent cloaking. Anyone can request Markdown directly; agents can also read HTML. Markdown responses have a `text/markdown` content type and `X-Robots-Tag: noindex` so search engines favor HTML, while `robots.txt` and the sitemap advertise public HTML pages. Do not disallow Markdown in `robots.txt`: agents need to fetch it explicitly. HTML has canonical URLs and points back to its Markdown source via `rel="alternate" type="text/markdown"`.

When adding a guide for public consumption, review the explicit `PUBLIC_DOCS` allowlist in `scripts/build_cloudflare_site.py`. Regenerate the committed HTML with the maintainer-only generator (`python3 scripts/build_doc_pages.py`), and verify it with `--check`. The core static-site and CI builds require no Markdown parsing package or client runtime.

## Validation and maintenance

The repository uses Python standard-library scripts:

```sh
python3 scripts/build_agent_docs.py --check
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v
python3 scripts/build_cloudflare_site.py --check
```

The consolidated reference is deterministic and checked in CI through the Python test suite. The Cloudflare publisher uses a strict allowlist, so exposing new documentation does not expose internal files or business planning documents.

## What Syntyr does not do

Syntyr styles browser HTML/CSS. It does not supply a JavaScript component runtime, chart rendering engine, AI API, CRUD handlers, form submission or remote data access. The optional local read-only MCP adapter is a separate developer tool, never a CSS runtime dependency. Use your existing application technology for those responsibilities.

## Deterministic section composition (source candidate)

From a source checkout, optional Node.js 22+ authoring tooling can discover the
canonical website section fields and assemble ordinary HTML without a model
generating arbitrary tags. No npm install or browser-side JavaScript is needed.
This is separate from the Python-only CSS build and the immutable alpha.4 release.

```sh
node scripts/compose.mjs --list 0.3.0-alpha.5
node scripts/compose.mjs <<'JSON'
{"release":"0.3.0-alpha.5","title":"Product demo","theme":"studio","sections":[{"section_id":"hero-product","fields":{"text2":"A clearer workspace."}},{"section_id":"faq"}]}
JSON
```

The JSON result includes an editable `syntyr.page.v1` project, complete HTML,
required `syntyr.all.css` and a list of local image assets. Save the HTML next
to the matching candidate stylesheet from `dist/` and copy the listed assets
from `assets/` into an `assets/` directory alongside the HTML. The source
model validates field names and values, escapes content, scopes repeated IDs
and uses its existing safe-link fallback. Section order is preserved. Only
known canonical sections and 1–50 section instances are accepted.

This generator produces the static section layer; it does not compose or
install host widget controllers, implement routes/forms, generate production
copy, or certify accessibility. Review example content and destinations, and
use the release-pinned markup validator and real browser tests before shipping.

### Select sections from explicit intent IDs

The optional composer also supports an offline, deterministic planner. Use
`node scripts/compose.mjs --list-intents 0.3.0-alpha.5` to discover the
reviewed requirement IDs, corresponding section IDs and host obligations.

```sh
node scripts/compose.mjs --plan <<'JSON'
{"release":"0.3.0-alpha.5","title":"CRM dashboard","theme":"studio","requirements":["pipeline","metrics","inventory-search","account-management"]}
JSON
```

The plan preserves requirement order, deduplicates overlapping section
mappings and returns a separate coverage entry for every requirement.
A ready plan includes a `composition` object accepted by the normal
composer. Read every coverage entry before rendering. Generic resource
sections require domain-specific customization; they do not implement
account or inventory management. A presentation-only entry lists the
remaining host work, and even static content contains example copy and links.

Unknown, well-formed requirement IDs produce an unresolved plan, a null
composition and CLI exit code 2. Invalid input produces exit code 1.
The planner does not parse natural-language prompts, guess missing features,
select host controllers, certify functionality or make network calls.

### One-command validated generation

Use the optional source-checkout orchestration CLI (Python and Node.js)
to run intent planning, composition preflight, canonical HTML rendering
and the release-pinned markup validator in a single offline command.

```sh
python3 scripts/generate_ui.py <<'JSON'
{"release":"0.3.0-alpha.5","title":"CRM dashboard","theme":"noir","requirements":["pipeline","metrics","inventory-search","account-management"]}
JSON
```

A successful response contains `plan`, `preflight`, `validation` and
`output` (HTML, editable project and asset references). The preflight
lists exact individual module requirements; the output uses the aggregate
stylesheet, checked separately by the markup validator. A blocked response
has no generated artifact and identifies the stage that blocked it (exit 2).
Invalid input or tool failure returns exit 1.

Optional `interactions` declarations and `runtime_policy` are checked
against the interaction contract and recipe inventory. Three reviewed
canonical section equivalents can be emitted without adding a new renderer:
`combobox/native-select/fallback` selects the filter toolbar,
`sortable-table/native-table/fallback` selects a static data table, and
`disclosure/native-modal-dialog/example` selects the FAQ disclosure.
The response lists each equivalent in `rendered_interactions` with explicit
limitations. This is not the full recipe source or implementation of live
combobox filtering, table sorting or modal commands. The final preflight
includes the extra section requirements. Other recipes (including modal and
popover implementations) block the entire output, even if preflight is valid.
The local authoring pipeline validates entire documents up to 262,144 characters;
the public MCP markup tool retains its 20,000-character limit. Larger local
documents block rather than bypass validation.
The pipeline does not claim host functionality, live interaction behavior,
security or accessibility certification; review the returned host obligations,
sample content and destinations before deployment.

### Reproduce and share a generation demo

With the optional local Python and Node authoring tools, build one of three
portable demo ZIPs from the same validated generation pipeline:

```sh
python3 scripts/build_generation_demo.py saas syntyr-saas-demo.zip
python3 scripts/build_generation_demo.py crm syntyr-crm-demo.zip
python3 scripts/build_generation_demo.py native syntyr-native-demo.zip
```

Extract the ZIP and open `index.html` locally. It includes matching CSS,
the license, any required local images, original `request.json`, editable
`project.json`, and `validation.json` with coverage and host obligations.
Use the matching source candidate to regenerate or edit. Existing output
files are not overwritten. No model calls, API keys, or network requests
are needed for generation. These demos are illustrative static presentation
scaffolds; sample destinations and host-owned forms are not working
backend integrations. Do not deploy them unchanged as real applications.

### Try the browser composition playground

The [composition playground](composition-playground.html) shares the CLI's
deterministic intent planner and canonical renderer. Choose a SaaS or CRM
preset, change the selected requirements and theme, then preview in a
sandbox and download project JSON or a portable HTML/CSS ZIP. This browser
experiment performs structural planning and rendering only; it does not
run the Python preflight or release-pinned markup validator. Use the offline
generation command for validated artifacts and the reproducible demo command
for packages containing validation evidence.
