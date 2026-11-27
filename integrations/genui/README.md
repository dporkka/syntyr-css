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

## Experimental surface lifecycle

Use one `SurfaceSession` per host-owned conversation. It accepts individual
A2UI 1.0 JSON messages for the same restricted basic-catalog subset:

```python
import json
from pathlib import Path
from integrations.genui.lifecycle import SurfaceSession

session = SurfaceSession()
message = Path("integrations/genui/example.a2ui.json").read_text()
session.apply(message)
html = session.apply(json.dumps({
    "version": "1.0",
    "updateComponents": {
        "surfaceId": "report",
        "components": [
            {"id": "summary", "component": "Text", "text": "New report available."}
        ]
    }
}))
session.apply(json.dumps({
    "version": "1.0", "deleteSurface": {"surfaceId": "report"}
}))
```

The initial create must contain a complete valid tree. Updates replace whole
component records by ID or add referenced components, not merge properties.
Each message is validated atomically against the complete resulting snapshot;
rejected events leave the last valid HTML and component graph untouched.
Orphans, unresolved references, shared children and cycles remain unsupported,
so deleting individual components and incomplete intermediate graphs are not
supported. Delete removes a whole surface; IDs cannot be reused in a session.

Defaults are at most eight active surfaces and 128 lifetime surface IDs;
hosts can lower either limit. Both incoming messages and cumulative serialized
snapshots are limited to 256 KiB, with the existing component and depth limits.
No persistent storage, function execution, actions, incremental
DOM patching or network transport are implemented. The session is synchronous
and not thread-safe; hosts must serialize message processing, isolate sessions
by authenticated user/conversation, manage their expiration and enforce access
control. HTML is a full body fragment, not a DOM mutation command.

## Experimental reactive text bindings

The stateful session (not the stateless snapshot adapter) accepts an optional
initial `dataModel` on createSurface and supports updateDataModel:

```python
import json
from integrations.genui.a2ui import BASIC_CATALOG_ID
from integrations.genui.lifecycle import SurfaceSession

session = SurfaceSession()
session.apply(json.dumps({
    "version": "1.0",
    "createSurface": {
        "surfaceId": "report",
        "catalogId": BASIC_CATALOG_ID,
        "dataModel": {"report": {"status": "Preparing report"}},
        "components": [
            {"id": "root", "component": "Text",
             "text": {"@path": "/report/status"}}
        ]
    }
}))
html = session.apply(json.dumps({
    "version": "1.0",
    "updateDataModel": {
        "surfaceId": "report",
        "path": "/report/status",
        "value": "Report ready"
    }
}))
```

Only Text.text supports a binding; it must resolve to a string in the current
surface's model. Models are nested JSON objects with string leaves only.
Numbers, booleans, arrays, null values in stored models, relative paths, empty
key names, reserved prototype keys, function calls and template bindings are
unsupported. JSON Pointer ~0 and ~1 escapes are decoded. Omitted update path
or "/" replaces the entire model with an object. Other paths replace/add a
key under an existing object parent; null deletes an existing key. Removing
a bound key or replacing it with a non-string fails atomically. Limits: 12
model levels, 1024 total keys, 128 characters per key, 4000 per string.
The serialized unresolved graph plus model and the resolved graph each have
the existing 256 KiB cap (ASCII-escaped JSON for the session). Values are
escaped by the existing renderer; no model-provided code runs.

Hosts must supply only data authorized for the current conversation; bindings
are not an authorization boundary within a model. The adapter returns a new
full HTML fragment after each valid event, not a live DOM mutation. The host
owns transport, DOM replacement, focus preservation and session cleanup.
This is a restricted A2UI interoperability experiment, not full conformance.

## Optional bounded NDJSON stream adapter

The host can consume a stream of UTF-8 JSON messages using the Python standard
library. This adapter defines host-side newline framing, not an A2UI transport
standard or a network client. Supply an iterable of bytes from an authenticated
source; a record is exactly one JSON message terminated by LF (CRLF accepted).

```python
from integrations.genui.lifecycle import SurfaceSession
from integrations.genui.stream import iter_surface_updates

session = SurfaceSession()
with open("messages.ndjson", "rb") as source:
    chunks = iter(lambda: source.read(8192), b"")
    for update in iter_surface_updates(chunks, session):
        # Host-owned rendering or deletion, keyed by update.surface_id.
        # update.html is None for deleteSurface.
        print(update.surface_id, update.html)
```

Chunk and record sizes are capped at 256 KiB (record bytes exclude LF but
include an optional CR). Each iterator is capped at 8 MiB of input and 1024
records; hosts may lower these limits. UTF-8 characters can span chunks.
Empty chunks are ignored, but blank records, BOMs, invalid UTF-8 and
unterminated final records are rejected. Use iter_messages for framing only;
iter_surface_updates additionally validates and applies each record using
SurfaceSession. A failed record ends iteration without applying subsequent
records; earlier accepted records remain committed. An entire chunk is counted
against the total byte budget before its records are processed. No prefetching
of later messages is required; close the iterator to cancel consumption.

The host must enforce authentication, authorization, stream timeouts and
rate limits across requests, serialize access to each session, close the
underlying transport on errors/cancellation, and safely place rendered HTML
in its own trusted surface container. This is not an SSE or WebSocket client,
does not perform incremental DOM patching and does not execute model actions.

## Optional native browser snapshot renderer

For applications that own a GenUI v1 JSON snapshot, import the source-only
ES module. No framework, network fetch, runtime package, HTML parser or
CSS changes are required. Serve the repository-owned module with the
unreleased alpha.5 stylesheet in your own application.

```js
import { mountJson } from './integrations/genui/browser.mjs';

const snapshot = JSON.stringify({
  version: 1,
  root: {type: 'Text', props: {text: 'Report ready'}}
});
mountJson(document.getElementById('report'), snapshot);
```

`validateJson(source)` validates a string and returns its parsed snapshot.
`renderJson(source, document)` returns a detached DOM subtree, and
`mountJson(container, source)` replaces the host-owned container only after
successful validation and construction. All twelve v1 components are
supported. Tags, classes and attributes are fixed by the implementation;
model strings are assigned as text or safe attribute values, never parsed as
HTML. The validator rejects duplicate decoded JSON keys, non-integer JSON
number spellings, invalid shape, unknown properties, invalid text and
oversized/deep trees. The browser and Python validators remain independent;
the optional tests check catalog coverage and actual DOM parity on the
example report.

This adapter accepts the internal GenUI snapshot format, not raw A2UI
messages, HTML from the server, or the NDJSON stream. Hosts must supply a
trusted mount container, manage their session and transport, and control
authorization. Full replacement does not preserve focus or disclosure state
across successful updates; keyed reconciliation is not yet implemented.
No action dispatch, URL handling, executable model expressions or package
exports are added.

Development verification:

```sh
node --test tests/genui_browser.test.mjs
python3 tests/genui_browser_smoke.py --chromium /path/to/chromium
```

The first command is included in the optional JS-adoption CI step.
The second uses an existing sandbox-capable Chromium installation to verify
DOM parity, semantics, focus, native disclosure, narrow/wide container
reflow, injection resistance and failed-mount rollback. It is not a
cross-browser or WCAG conformance certification.

### Opt-in incremental DOM reconciliation

Use `reconcileJson(container, source, {keys})` for subsequent snapshots in a
dedicated renderer-owned container. It validates and constructs the proposed
tree before touching the live DOM, then reuses compatible nodes. Existing
focus, open disclosures, and table scroll offsets are preserved when their
nodes survive. A failed validation leaves the rendered interface untouched.

```js
import { reconcileJson } from './integrations/genui/browser.mjs';

const keys = new Map([
  ['root/0', 'report-heading'],
  ['root/1', 'report-details'],
]);
reconcileJson(document.getElementById('report'), snapshot, {keys});
```

Keys are a separate host-supplied map from component paths (root, root/0,
root/1, and so on) to stable unique strings, not a change to the GenUI JSON
schema. Keys are held in private WeakMaps and do not become HTML attributes.
Supply the updated path map when reordering. Keyed siblings may move within
their existing parent; cross-parent moves or incompatible component types
create new nodes. Unkeyed nodes match by position and type, so the host must
key components whose logical identity can change with ordering. Unknown
paths and duplicate keys are rejected before any DOM mutation. Hosts must
not independently mutate renderer-owned descendants.

Reconciliation does not implement raw A2UI stream consumption, action
dispatch, form state, cross-parent identity or arbitrary host markup.
`mountJson` remains the explicit full-replacement API.
