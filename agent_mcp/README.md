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
  pin `0.3.0-alpha.5`. These are not executable tools or a conformance claim.
- `lookup_api(name, release)` — class or token existence.
- `get_theme_tokens(query, release)` — property names, not computed values.
- `validate_markup(html, release, stylesheets)` — unknown `syn-*` classes,
  allowed theme/state values, missing CSS files, and structured repair hints.
  This is not an accessibility conformance audit.

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
