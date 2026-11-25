# Syntyr Server Components — Node.js (standard library)

**Copy-owned example for the unreleased Syntyr `0.3.0-alpha.5` source candidate.**
This is not a published Syntyr component runtime or an npm dependency.
The example uses Node.js 20+ built-ins only (`http`, `fs`, `url`, `node:test`).
No Express, EJS, JSX, HTMX, client JavaScript or build tooling is required.

From the repository root:

```sh
python3 scripts/build.py
node --test examples/server-components-node/test/*.test.mjs
node examples/server-components-node/server.mjs
# Browse http://127.0.0.1:8768/
```

`SYNTYR_ADDR` and `SYNTYR_PORT` select the development bind address/port.
The server reads `dist/syntyr.core.css` and serves that **single explicit CSS
asset**; it does not expose filesystem paths as routes.

## Optional HTMX and Datastar fragments

The [fragment-response demo](fragments/README.md) reuses these **same** five
HTML component functions for HTMX partial responses and Datastar SSE patches.
It maintains native GET fallback, history-safe documents, encoded pagination,
and accessible server validation; no Syntyr runtime or CSS module is added.

## Copy-owned component contract

`components.mjs` exports five functions, `field`, `notice`, `button`, `table`
and `pagination`, plus `renderPage` for composition. The component inputs
match the Go `html/template` and Go templ reference examples:

| Function | Input | Output |
| --- | --- | --- |
| `field` | `{ id, name, label, value, help, error }` | Native labeled search input with linked server error/help |
| `notice` | `{ message, danger }` | Status/alert semantics and `syn-alert` |
| `button` | `{ label, primary, submit }` | Native submit/button with `syn-button` |
| `table` | Array of `{ title, description }` | Captioned table with header scopes, or empty state |
| `pagination` | `{ page, total, prevURL, nextURL }` | Link-based pagination and current-page marker |

The server owns data, request handling, validation, query URLs, status codes
and authorization. The functions output only HTML strings using existing
`syntyr.core.css` classes; they never create DOM nodes or attach listeners.

## Security and accessibility

- Dynamic content and attribute values are escaped at **every** interpolation
  boundary. Never concatenate untrusted HTML into a pre-rendered component.
- `pagination` accepts only root-relative URLs, rejecting external,
  scheme-relative, or `javascript:` links. The server constructs its links
  through `URLSearchParams` and HTML escaping.
- Invalid query encodings return HTTP **400**. Search terms longer than 80
  characters keep only a bounded value for accessible error display;
  **no results or pagination links** are rendered for rejected input.
- The demo uses **GET-only** search. For write operations your application
  must add authentication, authorization, CSRF defenses, idempotency and
  structured server validation. The example is not production middleware.
- Keep unique form IDs, `aria-describedby` references, and semantic table
  headers. State changes on navigation are handled by the browser; no live
  announcements or state manager are implied.
- Serve a pinned CSS release in production. This example consumes the
  repository's locally built alpha.5 candidate.

For full-page and fragment responses, use the same component functions but
have the host framework own routing, history handling, and response headers.
