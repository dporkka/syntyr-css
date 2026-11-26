# Syntyr Server Components — Go templ

**Copy-owned, optional Go templ example for unreleased Syntyr alpha.5.**
This is not a new Syntyr runtime, a published Go package, or a production
application starter. `github.com/a-h/templ` is isolated in this example's
`go.mod` and is **not** a dependency of Syntyr Core or the Go standard-library
server component example.

Requires patched Go 1.26.11+ and pinned `github.com/a-h/templ v0.3.1100`. From the repo
root, with network access to obtain the optional compiler when not cached:

```sh
python3 scripts/build.py
cd examples/server-components-templ
go mod verify
go tool templ generate
go test ./...
go vet ./...
go run .  # http://127.0.0.1:8769/
```

The `tool` directive pins the templ generator and its transitive module graph
in the same isolated fixture. `golang.org/x/net` is pinned to v0.62.0 or
later patched versions to address the Go HTTP/2 and HTML advisories identified
in November 2026. The Go 1.26.11 minimum includes the relevant standard-library
HTTP/2 fixes. Run `go mod tidy`, generation, tests and vet after dependency
changes; verify the selected versions and the checksums rather than hand-editing
`go.sum`. None of these packages are Syntyr CSS dependencies.

Generated `components_templ.go` is **local and ignored**; do not commit it.
The checked-in `.templ` source, module version and Go tests remain the source
of truth. The server uses the existing `dist/syntyr.core.css` as a pinned
local fixture only. `-dist` can set another directory containing that file.

## Copy-owned component contract

`components.templ` provides `Field`, `Notice`, `Button`, `Table` and
`Pagination`, composed in the `Page` component. Inputs are defined in
`models.go` and correspond to `syn.field`, `syn.notice`, `syn.button`,
`syn.table`, and `syn.pagination` in the `html/template` example.

- `Field`: native `<label>` and input, unique server-owned ID, and linked
  `aria-describedby`/`aria-invalid` for errors.
- `Notice`: semantic status/alert with existing `syn-alert` CSS.
- `Button`: native button type and optional existing `syn-button--primary`.
- `Table`: caption and scoped row/column headings, or native empty state.
- `Pagination`: server-generated links with current page marker.

Malformed percent-encoded queries are rejected with HTTP **400**. Searches that
exceed 80 characters preserve a bounded value for error display but render
**no actionable results or pagination links**.

Go templ escapes interpolated untrusted text and attributes, and sanitizes
unsafe URL schemes. Do not bypass this protection by treating user input as
trusted HTML/URLs. The GET-only example bounds queries, encodes pagination
with `net/url.Values`, and returns 400 for invalid input or page numbers.
For mutations, implement authorization, CSRF and idempotency in the host app.
Syntyr is only the presentation layer; this demo requires no browser JS.
