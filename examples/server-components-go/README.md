# Composable Syntyr Server HTML components — Go standard library

**Source-only example for the unreleased `0.3.0-alpha.5` candidate.** This is
an optional authoring integration, **not** a Syntyr runtime, a published Go
package, or a production application starter. There are no third-party Go
modules, JavaScript assets, build plugins or hydration requirements.

From the repository root:

```sh
python3 scripts/build.py
cd examples/server-components-go
go test ./...
go run .  # http://127.0.0.1:8767/
```

The `go run .` command selects the package in **the current directory**.
To launch from another directory, build the binary from this example first:

```sh
cd examples/server-components-go
go build -o /tmp/syntyr-server-components-go .
cd /your/application
/tmp/syntyr-server-components-go -dist /absolute/path/to/syntyr-css/dist
```

Only the development server and `html/template` render HTML.
Syntyr's existing `syntyr.core.css` supplies the styles, and `syn-*` selectors
remain identical across renderers.

## Copy-owned component contract

The `templates/components.html` file contains independent Go `html/template`
partials, called through the standard `{{template "name" .Data}}` syntax:

| Partial | Input shape | HTML contract |
| --- | --- | --- |
| `syn.field` | `textField{ID, Name, Label, Value, Help, Error}` | Native labeled search control; server error is linked with `aria-describedby` and `aria-invalid` |
| `syn.notice` | `notice{Message, Danger}` | Alert/status with `syn-alert` styles |
| `syn.button` | `button{Label, Primary, Submit}` | Native button with explicit type |
| `syn.table` | `[]record{Title, Description}` | Native caption, column and row headers; empty-state fallback |
| `syn.pagination` | `pagination{Page, Total, PrevURL, NextURL}` | Native links and current page with accessible nav label |

`templates/page.html` shows how to compose the partials into a complete
`<main>` without a component runtime. Copy and adapt the templates to your Go
application. Reserve **all rendered IDs** across the document: the field ID
and its derived `-help` and `-error` IDs must not collide with IDs belonging
to any other field or component. For example, two fields with IDs `query` and
`query-error` can collide when the first field renders its error paragraph.
The sample is one search form, not an automatic ID generator.

For other backends, reproduce the **rendered semantic HTML** with ERB, Jinja,
Blade, HEEx, Razor, templ, Astro or an ordinary server-side renderer. The
Go-specific template syntax and structs are not a cross-language API.

## Server and security responsibilities

- `html/template` escapes plain-text content and URL attributes. **Do not**
  convert untrusted input into `template.HTML` or other trusted-safe types.
- The application validates input on the server, bounds reflected query values,
  and builds pagination links using `net/url.Values`.
- The example uses GET-only read operations. For mutations, implement
  authentication, authorization, CSRF protection, idempotency and correct HTTP
  status handling **in your server**, not in a Syntyr component.
- `role="alert"` and field errors describe server state; CSS does not announce
  updates, prevent submission or perform validation.
- Use a pinned, self-hosted Syntyr CSS release for real deployments. This
  source example links the locally built, unpublished alpha.5 candidate.
- Server-side fragment responses for HTMX or Datastar are optional and
  application-owned; avoid treating this example as a replacement for either.

## Verification

```sh
cd examples/server-components-go
go test ./...
go vet ./...
```

The tests exercise escaping, error linkage, query-safe pagination, invalid
page handling, GET/HEAD, and non-GET rejection.
