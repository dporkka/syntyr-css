# Optional Syntyr HTML inspector (experimental)

Read-only, local HTML inspection using goquery and Cascadia. This independently
removable Go module is not part of the CSS build, npm package, or browser
runtime. Requires Go 1.26 or newer. The catalog is the repository's existing
`metadata/components.json`; no second component registry is maintained.

From the repository root:

```sh
(cd tools/html-inspector && go build -o /tmp/syntyr-html-inspect .)
/tmp/syntyr-html-inspect examples/operations-console.html
/tmp/syntyr-html-inspect --selector '.syn-app-shell' examples/operations-console.html
/tmp/syntyr-html-inspect --selector 'main > button, nav a' examples/operations-console.html
(cd tools/html-inspector && go test ./... && go vet ./...)
```

Use `--catalog FILE` to explicitly select a matching version 1 component catalog.
The default inventory finds elements with literal `syn-*` class tokens;
an explicit CSS selector can also select unstyled elements. JSON reports contain
the catalog source version, selected elements in document order, Syntyr class
tokens, matching curated component names, and matching recipe slot counts.
Recipe slots are checked within their root, excluding nested instances of the
same recipe and inert template content. A missing required or repeated
nonrepeatable slot is advisory (`missing` or `multiple`); otherwise `ok`.
Successful inspections exit zero, input/selector/catalog failures exit 2.

The catalog is curated, not exhaustive. This tool analyzes rendered static HTML
or fragments (up to 8 MiB), not JSX, Go templates, browser state, computed CSS,
accessibility conformance, or arbitrary framework source. Selector support
is Cascadia's static selector subset; HTML5 parsing can normalize source
markup. Recipe checks are structural hints, not a complete component contract.
No source changes, HTML output, network fetching, or automatic repairs occur.
The JSON schema is experimental. Use the existing
`python3 scripts/syntyr_check.py FILE` for canonical class, attribute,
stylesheet and optional semantic validation.
