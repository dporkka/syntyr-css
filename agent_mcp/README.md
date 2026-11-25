# Optional Syntyr read-only MCP server

Syntyr CSS remains MIT-licensed, independent of MCP, JavaScript-free at runtime,
and free of required API keys or network services. This **local developer
adapter** is not included in the npm CSS package, CDN, or static-site build.

The official MCP Python SDK is the *only optional server dependency*. Requires
Python 3.11+ and [uv](https://docs.astral.sh/uv/) (or install `mcp>=2,<3` in a
dedicated Python environment).

From a checked-out Syntyr repository:

```sh
uv run --no-project --with 'mcp>=2,<3' python -m agent_mcp.server
```

Example local stdio client configuration (replace absolute checkout path):

```json
{
  "mcpServers": {
    "syntyr": {
      "command": "uv",
      "args": [
        "run", "--directory", "/absolute/path/to/syntyr-css",
        "--no-project", "--with", "mcp>=2,<3",
        "python", "-m", "agent_mcp.server"
      ]
    }
  }
}
```

The server offers these **read-only** tools:

- `search_components(query, release)` — curated verified components.
- `get_component(name, release)` — native element guidance and stylesheets.
- `get_interaction_contracts(name, release)` — source-candidate-only anatomy,
  state hooks, behavior ownership, accessibility obligations, fallbacks and
  descriptive intentions. Use an empty name to list contracts and explicitly
  pin `0.3.0-alpha.5`. Stylesheet identifiers can be passed directly to
  `validate_markup`; the candidate-only `headless/interactions.css` identifier
  refers to the optional adapter in `integrations/headless/`. These are not
  executable tools or a conformance claim.
- `lookup_api(name, release)` — class or token existence.
- `get_theme_tokens(query, release)` — property names, not computed values.
- `validate_markup(html, release, stylesheets)` — unknown `syn-*` classes,
  allowed theme/state values, missing CSS files, and structured repair hints.
  This is not an accessibility conformance audit.

### Optional selector-based inspection (source candidate only)

The separate Go inspector is never built or downloaded by the server. To enable
it, build the checked-in tool yourself with Go 1.26+ and configure the absolute
path to the trusted executable before launching the server:

```sh
(cd tools/html-inspector && go build -o /tmp/syntyr-html-inspect .)
export SYNTYR_HTML_INSPECTOR=/tmp/syntyr-html-inspect
```

Call `inspect_markup(html, release, selector="")` with explicit release
`0.3.0-alpha.5` (unreleased source candidate). It accepts literal HTML, not
a path or URL, and returns selected elements, curated component names and
advisory recipe-slot counts. Inputs are capped at 20,000 characters and selectors
at 256 characters; results contain at most 40 elements and a `truncated` flag.
The local executable has a five-second timeout. An unconfigured binary,
unsupported release, or invalid selector is a tool error. There is no automatic
repair, browser evaluation, or source-file access. Use `validate_markup` for
release-pinned class and stylesheet checks, and browser tests for rendered behavior.

### Transactional variant previews (experimental)

After inspection, call `plan_variant_changes(html, release, document_sha256,
operations)`. Each operation contains `element_id`, `selector`, `from`, and
`to`. The planner accepts one to eight independent class replacements on
distinct elements in the same exact snapshot; one invalid operation rejects
the entire response. All operations are evaluated against the original HTML,
not sequentially applied. A shared five-second execution budget bounds the
local inspector subprocesses. Returned changes are decoded attribute
before/after pairs, not source diffs. No files are written. Use the canonical
validator and browser testing after any human-applied edit.

### Agent verification loop

Call `validate_markup` with the generated **literal HTML**, explicit release,
and the stylesheets actually installed. The response preserves
`classes_checked`, `unknown_classes`, `missing_stylesheets`, and
`installed_stylesheets`; it additionally includes a deterministic `diagnostics`
array with 1-based source positions, errors, class-name `suggestions` limited
to the selected release, `allowed_values` for known states, and
`required_stylesheets` / `loaded_stylesheets` when a CSS module is missing.
Recognized `<link rel="stylesheet">` paths are used if `stylesheets` is
omitted; explicit values override detected links. An explicitly empty array
means **no Syntyr CSS is loaded** and produces missing-module diagnostics.
When the field is omitted and no stylesheet link is found,
`missing_stylesheets` lists recommended CSS entrypoints, but the validator
cannot assert what the application already loads. Dynamic template expressions
are skipped conservatively. The MCP tool never edits files or installs CSS.

```json
{
  "html": "<button class=\"syn-buttn\">Save</button>",
  "release": "0.3.0-alpha.4",
  "stylesheets": ["syntyr.core.css"]
}
```

Validate again after applying an appropriate class or stylesheet correction,
and verify actual rendered behavior with native keyboard and browser checks.
Do not apply suggestions automatically. A typo near an alpha.5-only selector
is **not** proof that the class exists in published alpha.4.

Version defaults to **published and immutable `0.3.0-alpha.4`**; explicitly
select `0.3.0-alpha.5` only when using the unreleased current-source CSS
candidate. The adapter reads actual checked-in stylesheets and maintained
metadata. The component inventory is curated, not exhaustive. Invalid
releases, selectors, components, and stylesheet names produce tool errors
instead of invented API responses. Do not assume a module is installed simply
because a selector exists.

This is a local stdio tool, *not* an HTTP MCP server, paid API, hosted service,
chatbot, code execution endpoint, or license checker. It never reads user
projects or network resources and does not handle payment credentials.

## Tests

Run the metadata contract tests with Python's standard library:

```sh
python3 -m unittest tests.test_agent_mcp -v
```

Run the real SDK integration and complete repository suite using the optional
SDK in an isolated uv environment:

```sh
uv run --no-project --with 'mcp>=2,<3' python -m unittest tests.test_agent_mcp_sdk -v
uv run --no-project --with 'mcp>=2,<3' python -m unittest discover -s tests -q
```

No MCP dependency is added to `package.json` or to browser-facing assets.

### Browser evidence for interaction contracts

The candidate interaction contracts describe obligations, not certified behavior.
Maintainers can trace them to existing real browser fixtures without duplicating
the interaction implementation:

```sh
python3 scripts/check_interaction_conformance.py --list
# Optional tooling: install the pinned Python Playwright and its browsers.
# Install the locked headless React example dependencies with npm ci.
python3 scripts/check_interaction_conformance.py
# Or select particular contracts:
python3 scripts/check_interaction_conformance.py dialog disclosure
```

Native dialog/disclosure and dropdown scenarios exercise real browser controls;
combobox and sortable-table scenarios exercise the optional React Aria example.
Results apply to these fixtures only, not all host implementations.


### Discover runnable interaction recipes

Call `get_interaction_contracts` for anatomy, state and ownership obligations,
then `get_interaction_recipes(contract="combobox", release="0.3.0-alpha.5")`
for source and test references. Omit the contract filter to list all eight
candidate recipes. Each relationship explicitly distinguishes an implementation,
an alternative, a fallback, or an example; an empty link list means no matching
contract exists yet. In particular, a native select is a fallback for a searchable
combobox, not a searchable combobox implementation.

Recipe `stylesheets` identifiers are accepted by `validate_markup`. The
original `css` paths remain source references. Discovery never runs the tests,
executes interactions, or certifies accessibility. The published alpha.4 release
does not expose candidate recipes.
