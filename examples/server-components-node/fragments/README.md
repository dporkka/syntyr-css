# Copy-owned HTMX + Datastar HTML fragments

**Optional source example for the unreleased Syntyr `0.3.0-alpha.5` candidate.**
This is a **Node.js standard-library** server that imports the same `field`,
`notice`, `button`, `table`, and `pagination` HTML functions from the sibling
[`server-components-node`](../README.md) adapter. It does not ship a new
Syntyr CSS component, browser runtime, JavaScript controller, npm package,
server renderer or network requirement for the Syntyr library.

## Run

From the repository root:

```sh
python3 scripts/build.py
node --test examples/server-components-node/fragments/test/*.test.mjs
node examples/server-components-node/fragments/server.mjs
# http://127.0.0.1:8770/htmx
# http://127.0.0.1:8770/datastar
```

The demo binds to `127.0.0.1` and can use `SYNTYR_PORT`/`SYNTYR_ADDR`.
Both pages work as ordinary GET forms when browser JavaScript is disabled.
For enhancement, their **demo-only browser scripts** use pinned URLs:
HTMX 2.0.8 (`unpkg.com`) and Datastar v1.0.5 (`jsdelivr.net`). Those scripts
belong to the example app, not Syntyr. Production adopters should self-host
pinned assets and set a suitable Content Security Policy (CSP).

## HTMX fragment flow

- `GET /htmx?q=...` produces a complete document, including the form,
  escaped query, result table, pagination, and server errors.
- `GET /htmx?q=...` with `HX-Request: true` returns only the replaceable
  `#resource-workspace` **fragment**, which reuses the same HTML functions.
- `HX-History-Restore-Request: true` **always gets a complete document**,
  even if HTMX also sends `HX-Request: true`.
- The server sends `Vary: HX-Request, HX-History-Restore-Request` and
  `Cache-Control: no-store` to prevent fragment/document cache confusion.
- The form keeps a native `action` and `method="get"`. HTMX 2's `hx-get`,
  `hx-swap="outerHTML"`, `hx-target`, and `hx-push-url` enhance it only when
  its app-owned library loads. The `.syn-root` ancestor is never replaced.
- Invalid native GET requests return HTTP **400** with a complete, accessible
  error document. HTMX fragment validation returns HTTP **422** and
  `X-Syntyr-Validation: invalid`. The tiny **application-owned**
  `htmx-validation.js` selectively opts those 422 responses into HTMX swapping;
  HTMX otherwise ignores error responses by default. Do not use this hook to
  enable arbitrary cross-route HTTP error swapping.

## Datastar fragment flow

- `GET /datastar?q=...` returns a complete HTML document using the same form,
  result and pagination component functions, including native GET fallback.
- With `Accept: text/event-stream`, Datastar GET sends a serialized `datastar`
  query-signal object. The server allows only a bounded JSON object with a
  string `q` field. Invalid, oversized, missing or non-string signals return
  HTTP **400** without an SSE patch.
- Valid signals return an event named `datastar-patch-elements`, with a
  **single-line** `data: elements <div id="resource-workspace">…` fragment.
  Interpolated values are HTML escaped; CR/LF are removed from the complete
  serialized patch *after* rendering to prevent SSE record injection.
- The server sends `Vary: Accept`, `Cache-Control: no-store`, and
  `X-Content-Type-Options: nosniff`.
- Read-only search validation errors are delivered as successful SSE
  transport responses with accessible `aria-invalid`, `aria-describedby`,
  and `role="alert"` in the patched markup. Native invalid GET gets HTTP 400.
  This is an intentional distinction between a successful patch transport
  and an invalid submitted search value.

## Component boundaries and security

All invalid percent-encoded query strings return HTTP 400, while rejected
search terms display bounded, accessible validation feedback **without any
stale result table or actionable pagination** in full-page and fragment modes.

The app owns request routing, query validation, URL encoding, cache variation,
SSE/HTML content types, and status codes; the component functions just render
semantic HTML using Syntyr's existing `syn-*` CSS contract. The app's
replaceable `#resource-workspace` is inside a persistent Syntyr theme root.
Pagination always stays within `/htmx` or `/datastar` and preserves URL-encoded
filters. All static files are explicitly allowlisted.

This demo is **GET-only** and intentionally does not implement authentication,
authorization, CSRF, form mutations, rate limiting, or production CSP. Those
must be enforced by the host application before reusing components for writes.
Do not treat the example's external scripts as safe for unrestricted production
network loading. Syntyr Core needs neither HTMX nor Datastar.

## Tests

The Node tests cover full-page/fragment routing, history restoration,
422 validation, malformed Datastar signals, HTML escaping, SSE event framing,
URL scoping, method handling and static asset allowlisting:

```sh
node --test examples/server-components-node/fragments/test/*.test.mjs
```

Optional real Chromium interaction coverage is at
[`tests/server_html_fragments_browser.py`](../../../tests/server_html_fragments_browser.py).
Install Python Playwright and Chromium separately; download pinned HTMX and
Datastar bundles to local test fixture files, then run (from repo root):

```sh
HTMX_JS_PATH=/tmp/syntyr-htmx2.js \
DATASTAR_JS_PATH=/tmp/syntyr-datastar-v1.0.5.js \
python3 tests/server_html_fragments_browser.py
```

The browser test routes the two pinned external URLs to local fixture files,
checks actual HTMX fragment/history and validation recovery, checks Datastar
SSE DOM morphing, and checks native GET fallback with JavaScript disabled.
The optional browser tooling is **not** part of the Python standard-library
or CSS build requirements. Test only against your pinned browser/tool versions.
