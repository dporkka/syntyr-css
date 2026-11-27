# Experimental Syntyr GenUI HTML renderer

Opt-in source-only Python 3 standard-library adapter for rendering untrusted,
read-only agent-produced JSON using the unreleased alpha.5 CSS candidate. No
changes to CSS, release exports, or consumer runtime dependencies. This is not
an A2UI implementation or a published package.

Run at the repository root:

```sh
python3 -m integrations.genui < integrations/genui/example.json
python3 -m unittest discover -s tests -p test_genui.py -v
```

To preview a complete locally served HTML page:

```sh
{ printf '%s\n' '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GenUI preview</title><link rel="stylesheet" href="dist/syntyr.core.css"><body class="syn-root syn-shell"><main><h1>Example report</h1>'
  python3 -m integrations.genui < integrations/genui/example.json
  printf '%s\n' '</main></body></html>'
} > genui-preview.html
python3 -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000/genui-preview.html locally. Remove the generated
preview before committing. The native details disclosure is interactive
without JavaScript; the other primitives are informational.

## Contract

The machine-readable [catalog](catalog.json) defines the version, CSS target,
component names, required properties and child eligibility. The envelope is
`{"version":1,"root":{...}}`. Every node has a `type`, optional `props` (all
declared properties are required), and a nonempty `children` array only for
containers. Extra fields are rejected. Property types: text (string), label
(nonblank string), heading (integer 1–6), integer (0–1 billion), strings
(nonempty string list), labels (nonempty labels list), rows (array of string
arrays). Table rows must match column count; progress max must be positive and
value may not exceed it. Hosts determine heading hierarchy and where the
fragment is inserted.

Limits: 256 KiB UTF-8, depth 12, 256 nodes, 4000 characters per text field, 100
list items or table rows, 20 table columns. Duplicate keys, unknown types and
fields, booleans in integer properties, malformed JSON, invalid text characters
and nonfinite numbers fail closed. Text and attributes are escaped; no raw HTML,
URLs, custom selectors, scripts, model-defined IDs, actions or event handlers
are supported. CLI errors return status 2 without emitting partial HTML.
The Python API accepts a JSON string and returns a scoped HTML fragment or
raises GenUIError.

Validation guarantees the supported presentation contract, not truthfulness,
privacy, or WCAG compliance of arbitrary content. Hosts must source authoritative
data, enforce authorization before supplying it, avoid exposing sensitive data,
provide semantic heading context, and test their own accessibility and layout.
Treat the rendered HTML as a fragment for an HTML body, never as a script,
attribute, or URL. The host should apply its usual CSP.

## Follow-up

Keep A2UI interoperability, event streaming, action dispatch, bindings and
browser adapters separate and experimental until conformance and authorization
tests exist. Do not add any dependency from CSS to this adapter.

## Experimental A2UI 1.0 snapshot adapter

Based on the [A2UI 1.0 wire schema](https://github.com/a2ui-project/a2ui/blob/main/specification/v1_0/json/agent_to_renderer.json)
and [basic catalog](https://github.com/a2ui-project/a2ui/blob/main/catalogs/basic/v1/catalog.json).
Accepts one complete createSurface message with inline components, the exact
basic catalog identifier, a root ID of "root", and fixed child references.
The supported subset is Card, Column, body Text (plain text only, Markdown
is not interpreted), and horizontal Divider. No catalog is fetched.
Every component must be reachable once; cycles, shared child references,
orphans and duplicates are rejected. No state is retained between calls.
Unsupported properties, bindings, function calls, actions, metadata, data
models, catalog mixing, other message types and other protocol versions
are rejected rather than partially rendered.

```python
from pathlib import Path
from integrations.genui.a2ui import render_a2ui

html = render_a2ui(Path("integrations/genui/example.a2ui.json").read_text())
```

This is an interoperability experiment, **not** a complete A2UI renderer,
catalog conformance claim, streaming transport or agent client. The resulting
HTML is validated by the same bounded Syntyr renderer.
