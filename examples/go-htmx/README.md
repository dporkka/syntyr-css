# Syntyr + Go html/template + optional HTMX

This is a runnable, dependency-free Go application demo, not a screenshot or
an example of an authenticated production backend. It uses checked-in Syntyr
CSS and HTML templates. Syntyr itself has no Go or JavaScript dependency.

## Run

From the Syntyr repository root:

~~~sh
cd examples/go-htmx
go test ./...
go run .
# open http://127.0.0.1:8766/contacts
~~~

The server serves CSS from `../../dist/` and binds to localhost by default.
Use the generated alpha.5 source assets (`python3 scripts/build.py`) when
working in a source checkout; don't assume they exist in published alpha.4.

The search form uses `action="/contacts"` and `method="get"` so it works
with **no browser JavaScript**. Go's `html/template` autoescapes the search
query and contact data. The `/contacts` endpoint renders a complete document
for ordinary requests, or the results partial for `HX-Request: true`. The
server sets `Vary: HX-Request, HX-History-Restore-Request` and
`Cache-Control: no-store`. HTMX history-restoration requests receive a
complete page, even when `HX-Request: true`. No external requests are made.

To enable HTMX, put a vetted, pinned copy of `htmx.min.js` at
`examples/go-htmx/vendor/htmx.min.js` (the file is intentionally not
bundled), and then run:

~~~sh
go run . -htmx
~~~

The application emits a local script tag only with that flag. The server
checks the file exists before serving traffic. HTMX swaps the result region,
keeps the `.syn-root` outside the swapped subtree, and updates the URL.
Do not use an unpinned third-party CDN in production.

Optional real-browser smoke from the repository root (after installing
Playwright and its Chromium browser for development):

~~~sh
python3 tests/go_htmx_browser.py
~~~

The test exercises the actual native GET submission on a narrow viewport
without loading HTMX or any application JavaScript.

The illustrative contacts are not persisted. There are no write endpoints,
authentication, user accounts or payments; production mutations require
application-owned authorization, input validation and CSRF protection.
