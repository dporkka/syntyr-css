# Native Custom Elements + Syntyr CSS (optional)

This fixture uses the browser's built-in `HTMLElement`, Custom Elements, native events,
Shadow DOM, and Declarative Shadow DOM. It has **no Lit, React, runtime package,
or build requirement**. It is **not** a Syntyr JavaScript package or public widget API.

- `index.html`: a framework-free custom element with a readable light-DOM fallback.
- `ssr.html`: server-delivered Declarative Shadow DOM remains visible with scripts disabled;
  its action button stays disabled until JavaScript attaches its handler; upgrade
  reuses the existing shadow tree *without clearing* server-rendered content.
- `status-toggle.js`: attributes/properties, native events, safe text rendering,
  and connection-scoped event listeners. The action button has changing
  "Mark online/offline" text, so it does **not** use `aria-pressed`.
  A live status message remains outside the `aria-busy` region and is changed
  only when the message actually differs. Repeated module imports do not
  redefine an already-registered example tag.
- `status-toggle.css`: isolated Shadow DOM styles using public inherited Syntyr tokens
  and `::part()` for controlled host customization.
- `form-associated.html`: optional **form-associated Custom Element (FACE)** conformance
  fixture, with a real native GET form and two visibly labeled number inputs.
- `asset-range.js`: progressive enhancement for a *pair* of inventory-count
  filters. `ElementInternals.setFormValue(FormData, state)` makes them one
  form-associated unit and adds cross-field validation without hidden inputs.
  It covers reset, disabled fieldsets, restoration and reconnection.
- `form-result.html`: local static GET destination. It is not a search backend.

Run `python3 scripts/build.py` if the built CSS is missing, then at repository root
run `python3 -m http.server 8765 --bind 127.0.0.1`.
Visit `http://127.0.0.1:8765/examples/web-components/index.html`.
For automated cross-engine checks, run `npm ci --prefix examples/lit`,
`npm run build --prefix examples/lit`, and `npm test --prefix examples/lit`.
The Playwright dependency belongs exclusively to the optional Lit test harness.

The status toggle modifies local demo state only, not any backend resource.
The form-associated fixture **works without JavaScript**: native named inputs
submit the same two values in a normal GET request. After upgrade, the native
input `name` attributes are removed to prevent duplicate values and the FACE
supplies the pair through `ElementInternals`. The server must still validate
both numeric bounds and the relationship `minimum <= maximum`; client-side
validation is not security or business-rule enforcement. This fixture is
educational, not a production component recommendation. Prefer two native
inputs directly unless encapsulated multi-field validation is justified.

For real mutations use application-managed authorization, persistence,
CSRF protection, and server validation, plus a working native form or link
for users without scripting. The toggle fallback is deliberately **read-only**.

See [the authoring contract](../../docs/component-authoring.md) and
[Lit interoperability](../../docs/lit-integration.md).
