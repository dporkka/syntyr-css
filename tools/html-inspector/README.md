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

The standalone CLI also accepts `-` for stdin and `--limit N` for a bounded
report; zero (default) is unlimited. The `truncated` flag is true only if
additional matching elements were omitted.

Optional integration with the existing source-checkout agent CLI:

```sh
export SYNTYR_HTML_INSPECTOR=/tmp/syntyr-html-inspect
python3 scripts/syntyr_agent.py inspect-html --release 0.3.0-alpha.5 --selector '.syn-app-shell' examples/operations-console.html
```

This command and the optional MCP tool require an explicit candidate release,
limit HTML to 20,000 characters, return at most 40 elements, and do not build
or discover executables automatically. See [the MCP README](../../agent_mcp/README.md).

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
No source changes, full HTML output, network fetching, or automatic repairs occur.
The JSON schema is experimental. Inspection also returns a SHA-256 digest of
the exact input bytes and an `element_id` for each selected parsed element.
IDs are document-order ordinals independent of selector and output limit; they
are valid only against that exact input digest and the same inspector version.
They are not DOM id attributes, persistent editor identifiers or source offsets.
HTML5 parsing can insert implicit elements and discard duplicate attributes.

## Preview a curated class variant (experimental)

The standalone CLI can propose a **single decoded class-attribute replacement**.
Inspect first, then copy the digest and element ID from the JSON report:

```sh
/tmp/syntyr-html-inspect --selector '.syn-button--primary' page.html
/tmp/syntyr-html-inspect --selector '.syn-button--primary' \
  --document-sha256 DIGEST_FROM_REPORT --element-id ID_FROM_REPORT \
  --preview-from syn-button--primary --preview-to syn-button--outline page.html
```

The result reports `before`, `after`, `attribute: "class"` and
`preview_only: true`. No HTML is serialized or written. It requires a matching
digest and selector, exactly one base class and original modifier, and two
known modifiers from the same curated class family; competing modifiers,
unknown variants, and recognizable dynamic class expressions are refused.
All unrelated decoded class tokens and whitespace are preserved. The result is
a semantic suggestion, not a source patch: HTML parsing decodes entities,
normalizes line endings, and uses the effective first duplicate attribute.
Do not apply the plan automatically or interpret IDs as byte offsets.
The preview checks class-family membership, not visual compatibility or
complete component semantics. The MCP and agent CLI also expose bounded multi-operation previews.
Save a local JSON request with the inspected `document_sha256` and an
`operations` array of objects containing `element_id`, `selector`, `from`,
and `to`, then run:

```sh
python3 scripts/syntyr_agent.py plan-html --release 0.3.0-alpha.5 --request plan.json page.html
```

The MCP tool is `plan_variant_changes`. The planner permits at most eight
distinct targets and rejects the entire request if any operation fails.
It never applies changes or emits source patches.

 Use the existing
`python3 scripts/syntyr_check.py FILE` for canonical class, attribute,
stylesheet and optional semantic validation.
