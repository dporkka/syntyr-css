# Syntyr CSS integration guide: server-rendered HTML and frontend stacks

Syntyr is a **CSS presentation layer**, not a state manager, request client, or component runtime.
It has no JavaScript initialization, no required build tool, and no runtime dependency.
Every example uses the same `syn-` classes, CSS tokens and standard HTML.

## Copy a catalog example into your stack

The [49-example component catalog](catalog.html) has a **Copy HTML** action for
snippets and an optional **Copy full page** action that includes the
**actual required stylesheets**, the document shell and `.syn-root` theme
scope. Copying uses docs-only JavaScript; view the ordinary HTML source
without JavaScript. For complete layouts, choose the existing
[91 MIT blocks](blocks.html) instead of rebuilding a pricing or dashboard
section from scratch.

The full-page option expects you to self-host the same **unreleased alpha.5**
CSS files under `/dist/`; change those paths if your app uses `/public/css/`,
`/assets/`, or a build-time import. Do not mix alpha.5 examples with
published alpha.4 assets. Only load the CSS modules your example names;
`syntyr.all.css` replaces these modules, not accompanies them.

### Plain HTML or server-rendered partial

Copy the full page, or add core once to your layout:

```html
<link rel="stylesheet" href="/dist/syntyr.core.css">
<main class="syn-root" data-syn-theme="studio">
  <article class="syn-panel">
    <h1 class="syn-heading">Overview</h1>
    <a class="syn-button" href="/reports">View reports</a>
  </article>
</main>
```

Use a real server route for `/reports`. For reusable HTML partials, place
`.syn-root` on an ancestor that survives page/fragment replacements.

### React / Next.js JSX

Copy the component's *markup*, not the full `<!doctype>` page, into JSX.
Import the CSS once in the application entry or root layout and use
`className` and `htmlFor` instead of `class` and `for`:

```jsx
// Import /dist/syntyr.core.css once from the app's supported global CSS entry.
export function SearchPanel() {
  return (
    <section className="syn-root syn-panel" data-syn-theme="studio">
      <form action="/search" method="get" className="syn-form">
        <label className="syn-label" htmlFor="search-term">Search records</label>
        <input className="syn-input" id="search-term" name="q" type="search" />
        <button className="syn-button" type="submit">Search</button>
      </form>
    </section>
  );
}
```

No client component or hydration is necessary just to style a form. The
application route owns request handling and escaping.

### Vue / Nuxt template

Vue's template retains `class` and `for`; load CSS once using the framework's
supported CSS entry. Native GET submission still works with scripting off:

```vue
<template>
  <section class="syn-root syn-panel" data-syn-theme="studio">
    <form class="syn-form" method="get" action="/search">
      <label class="syn-label" for="vue-search">Search records</label>
      <input class="syn-input" id="vue-search" name="q" type="search">
      <button class="syn-button" type="submit">Search</button>
    </form>
  </section>
</template>
```

### HTMX-enhanced native GET

Keep the exact same HTML contract, adding HTMX attributes only if your app
has deliberately loaded a pinned HTMX runtime:

```html
<section class="syn-root" data-syn-theme="studio">
  <form action="/records" method="get" class="syn-form"
        hx-get="/records" hx-target="#record-results" hx-push-url="true">
    <label class="syn-label" for="record-query">Records</label>
    <input class="syn-input" id="record-query" name="q" type="search">
    <button class="syn-button" type="submit">Find</button>
  </form>
  <div id="record-results" aria-live="polite"></div>
</section>
```

Without HTMX, this still submits an ordinary GET. With HTMX, the server must
return a safe HTML fragment for normal HTMX requests, a **complete page** for
direct navigation and history restoration, and correctly vary cached
representations. Do not swap the stable `.syn-root`. Read the more detailed
HTMX behavior and error contracts below before building production search.

Some catalog examples demonstrate static UI rather than complete application
behavior. Replace demo-relative URLs and duplicate IDs; validate accessibility,
form submission, CSRF and authorization in your own app. Check the catalog's
[browser compatibility and fallbacks](catalog.html#catalog-browser-support)
for `popover`, named disclosures and invoker commands.

## Choose one styling mode

1. **Explicit classes (recommended for apps):** load `syntyr.core.css`, use
   `.syn-root` on a stable ancestor, then `.syn-button`, `.syn-panel`, `.syn-input`, etc.
2. **Optional semantic HTML:** additionally load `syntyr.semantic.css` after core and
   add `.syn-semantic` to a scoped ancestor. Unclassed HTML receives semantic styles.
   For an element that an interaction framework will add classes to, opt it in once
   with `data-syn-semantic`. This preserves semantic styling while host-managed
   classes such as `htmx-request` are added and removed.

```html
<section class="syn-root syn-semantic" data-syn-theme="studio">
  <button data-syn-semantic hx-get="/status" hx-target="#status">Check status</button>
  <div id="status" aria-live="polite"></div>
</section>
```

**Host isolation:** Loading the CSS alone does not style a `.syn-button`,
`.syn-panel`, or other Syntyr class outside `.syn-root`. Existing host UI
components and CSS retain their presentation. Put `.syn-root` on the actual
Syntyr subtree (or on the component itself); do not assume a globally
scoped component class creates its own theme root. Syntyr uses native CSS
nesting for this boundary, so test embedding in each target browser.

The marker is only considered **inside** `.syn-semantic`, so it does not style
elements elsewhere. Do not put it on elements styled by a separate component
library unless you explicitly want Syntyr semantic styling there. Prefer
`.syn-button` for already-classed controls. The marker does **not** make the
control stateful, disabled, or accessible by itself.

For accessible advanced menus, comboboxes and toasts, see the [optional headless interaction guide](headless-interactions.md). All framework JavaScript remains application-owned.

## HTMX: progressive enhancement

For a dedicated collection of 12 copy-owned patterns (tables, search, forms, dialogs, polling and loading feedback), see the [HTMX components guide](htmx-components.html) and [live server-backed playground](htmx-playground.html). These recipes reuse existing Syntyr classes and an independently removable, CSS-only request-state adapter.

For a **Go standard-library runnable starter** with no third-party Go modules,
see [examples/go-htmx](https://github.com/dporkka/syntyr-css/tree/main/examples/go-htmx). The default server runs
without JavaScript; optional locally vendored HTMX uses the same GET endpoint.
Its Go tests verify full-page vs fragment responses, HTMX history restoration,
escaping, method handling and the CSS serving path. This is a development fixture, not a production auth
or CSRF implementation.

A complete example with a real stdlib Python HTTP server is at:
[examples/htmx.html](https://github.com/dporkka/syntyr-css/blob/main/examples/htmx.html),
[examples/htmx_server.py](https://github.com/dporkka/syntyr-css/blob/main/examples/htmx_server.py), and
[examples/htmx.css](https://github.com/dporkka/syntyr-css/blob/main/examples/htmx.css).
These links lead to source files, not a live Cloudflare demonstration.

From the repository root:

```sh
python3 examples/htmx_server.py
# open http://127.0.0.1:8765/examples/htmx.html
```

The optional demo loads **pinned HTMX 2.0.8** from a third-party CDN. The CSS
library doesn't load HTMX automatically. Production applications should
self-host the pinned HTMX asset for control over performance, integrity, and CSP.

The search form uses a real `action` and `method=get`. When HTMX sends
`HX-Request: true`, the server returns only the result fragment. Ordinary
navigation gets a complete HTML document. The server emits
`Vary: HX-Request, HX-History-Restore-Request` to keep caches from mixing
normal fragments and full history-restore documents, and escapes
user-controlled query text before inserting it in HTML.

For best results:

- Put `.syn-root` and `data-syn-theme` **outside** the swapped element.
- Swap the narrowest stable target (normally `innerHTML` inside a results container).
- Give labels and inputs stable IDs; preserve native form submission as a fallback.
- Use `hx-push-url="true"` when search/filter results should be bookmarkable.
  Ensure the same URL serves a complete document on reload, restores escaped
  field values, and returns only the intended fragment for normal HTMX requests.
- If full documents and partial responses share an endpoint, set
  `historyRestoreAsHxRequest: false` in HTMX 2 and return a complete HTML
  document when `HX-History-Restore-Request: true` is present, even if a
  proxy or client also sends `HX-Request: true`. Set `Vary` for both headers
  or disable caching. A history cache miss must not receive a fragment.
- Use `hx-disabled-elt` to lock an in-flight submit button when duplicate
  submissions are undesirable. An `hx-indicator` only provides feedback.
- If a control must survive a larger swap, consider `hx-preserve` with a stable
  ID on both sides of the swap; prefer narrow targets first.
- A loading cursor, `aria-busy`, and `hx-indicator` are only feedback:
  they do **not** block duplicate submissions by themselves.
- Do not create a permanent Syntyr HTMX runtime or register Syntyr lifecycle events.
- For strict CSP, use `includeIndicatorStyles: false` and an external stylesheet.
  The demo shows this pattern with a small **application-owned** `htmx.css`.
- Test initial document, request state, swapped fragment, form fallback, and
  failure paths in an actual browser.

The demo server intentionally exposes only four static assets and one GET route,
listens on localhost, and is **not** included in the Cloudflare static-site build.
A static host cannot serve its dynamic search endpoint without a backend.

### HTMX 4 migration (separate from Syntyr)

The runnable example intentionally pins HTMX **2.0.8**. HTMX **4.0.1**
uses the same Syntyr stylesheet and component HTML, but its *HTMX-owned*
API changes. A browser smoke test applies the migration in an isolated
fixture rather than silently changing the v2 example:

- Replace `hx-disabled-elt="#search-button"` with
  `hx-disable="#search-button"`. In HTMX 4 the *old* `hx-disable` meaning
  (ignore a subtree) moved to `hx-ignore`.
- Use `includeIndicatorCSS: false` (rather than the v2
  `includeIndicatorStyles: false`) with the application-owned
  `htmx.css` indicator stylesheet.
- HTMX 4 refetches full documents for history navigation, instead of
  depending on the v2 browser snapshot cache. Full-page GET rendering
  and escaped form-value restoration must still work.
- HTMX 4 makes attribute inheritance explicit and swaps HTTP errors by
  default; review the framework's migration guide before upgrading
  any application. Syntyr does not override these semantics.

To exercise both versions against the real browser runtime without
installing either into Syntyr:

```sh
curl -fsSL https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js -o /tmp/syntyr-htmx2.js
curl -fsSL https://cdn.jsdelivr.net/npm/htmx.org@4.0.1/dist/htmx.min.js -o /tmp/syntyr-htmx4.js
HTMX_JS_PATH=/tmp/syntyr-htmx2.js HTMX4_JS_PATH=/tmp/syntyr-htmx4.js python3 tests/htmx_browser.py
```

Playwright is an **optional testing dependency**. In the smoke test,
the HTML response uses HTMX 4's external script and renamed controls
while keeping the identical Syntyr CSS, class names, and stable theme root.
This is not a claim that every HTMX extension or version-specific behavior
is drop-in compatible.


## Composable server HTML components (Go standard library)

Syntyr components do not require a browser runtime or React-style hydration.
To make server-side **composition** concrete, the
[Go standard-library component example](https://github.com/dporkka/syntyr-css/tree/main/examples/server-components-go)
provides five copy-owned `html/template` partials: labeled search field,
status/error notice, button, result table and pagination. It includes a
runnable GET-only example and tests for HTML escaping, server validation,
`aria-describedby`, and encoded query-preserving links. No new stylesheet,
JavaScript dependency, component protocol or Go library is introduced.

```go-html-template
<form action="/" method="get" role="search" class="syn-form">
  {{template "syn.field" .Query}}
  {{template "syn.button" .SearchButton}}
</form>
{{template "syn.table" .Records}}
{{template "syn.pagination" .Pager}}
```

The input values come from your server. Each component emits ordinary HTML
with classes already in `syntyr.core.css`, and `html/template` contextually
escapes untrusted data. The app owns distinct IDs, request validation, query
encoding, CSRF for mutation forms, authorization and error status codes.
For HTMX/Datastar/Turbo responses, render the same partials into fragments,
but retain full-page rendering for direct navigation and history restoration.
This is an **example**, not a new Syntyr runtime API or a claim of an official
adapter for every backend language. See the
[copyable template README](https://github.com/dporkka/syntyr-css/blob/main/examples/server-components-go/README.md)
for the complete contract and setup instructions.

### Additional copy-owned server component adapters

The [Go templ adapter](https://github.com/dporkka/syntyr-css/tree/main/examples/server-components-templ)
uses the same five native HTML component contracts as the Go standard-library
example, with independent `Field`, `Notice`, `Button`, `Table` and
`Pagination` components. It has an isolated, pinned `github.com/a-h/templ`
build-time/runtime module dependency (Go 1.26+); run `templ generate` before
tests or starting the example. Generated Go code is not checked in.

The [Node.js standard-library adapter](https://github.com/dporkka/syntyr-css/tree/main/examples/server-components-node)
exposes corresponding composable HTML functions. It requires no npm packages;
Node owns request routing and escaping, and the example serves a single
allowlisted CSS asset. Pagination links are root-relative and use
`URLSearchParams`, not interpolation of arbitrary URLs. Run its built-in
`node --test` suite to exercise escaped values, safe links, error linkage,
HTTP methods and GET fallback.

These integrations are **copy-owned examples**, not npm exports or shipped
runtime packages. They reuse `syntyr.core.css` and the same semantic HTML;
none adds a JavaScript controller, hydration requirement, new `syn-*` class,
CSS module or runtime to Syntyr's core. Each server must still handle its own
user permissions, CSRF defenses for mutations, status codes, and navigation.

### HTMX and Datastar fragments built from the same components

The [Node.js HTML fragment demo](https://github.com/dporkka/syntyr-css/tree/main/examples/server-components-node/fragments)
reuses the **same copy-owned** `field`, `notice`, `button`, `table` and
`pagination` functions from the Node.js adapter for both initial HTML pages
and optional HTMX/Datastar updates. It requires no npm packages or new
Syntyr component runtime. Run `node examples/server-components-node/fragments/server.mjs`
from the repo root, after building CSS, to open `/htmx` and `/datastar`.

- **HTMX 2.0.8:** native GET fallback, fragments targeting a stable
  `#resource-workspace`, `hx-push-url` for searchable history, and complete
  HTML for `HX-History-Restore-Request`. A tiny app-owned external script
  explicitly permits swapping *only* server-marked HTTP 422 validation
  fragments, while normal GET errors retain HTTP 400. Cache output varies
  by the HTMX request/history headers.
- **Datastar v1.0.5:** ordinary GET fallback and a pinned, optional
  enhancement that sends `datastar` JSON signals, receives
  `event: datastar-patch-elements` through SSE and morphs the same component
  HTML. Signal input is bounded and type-checked; the serialized SSE patch
  is flattened to a single `data:` line *after* HTML escaping. `Vary: Accept`
  distinguishes ordinary pages from SSE. Bad signals receive HTTP 400;
  field-validation errors for valid SSE requests are represented accessibly
  inside a successful event response.

In both modes, `.syn-root` persists outside the replaceable fragment;
existing `syn-*` selectors and tokens are unchanged. Browser scripts belong
solely to the **demo app** (pinned external URLs in the example), not to
Syntyr Core. Self-host your browser dependencies and set an appropriate CSP
before production use. The example handles **read-only GET requests only**;
server authorization and CSRF protections for writes remain application-owned.
The [example README](https://github.com/dporkka/syntyr-css/blob/main/examples/server-components-node/fragments/README.md)
contains reproducible HTTP and optional Chromium browser tests.

## Server-driven HTML: optional request-state bridge

**No adapter is necessary to render Syntyr components.** Serve core CSS from
your application and output the same `syn-` classes in HEEx, Blade, ERB, templ,
Jinja, Twig or Razor. You only need a second CSS file if you want native
framework loading classes and attributes to show Syntyr's progress cursor:

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.server.css">
```

Or, when using a CSS-aware package build system, import
`@syntyr/css/core.css` followed by `@syntyr/css/server.css`.
The optional `syntyr.server.css` is included in `syntyr.all.css`, but not core.
The npm package is an unreleased alpha.5 candidate; self-host prebuilt
files or a pinned release until that version is actually published.

The bridge is **presentation-only**. It styles the cursor on Syntyr buttons
during `data-loading`, `.htmx-request`, `.up-active`,
`.phx-click-loading`, `.phx-submit-loading`, `.phx-change-loading`, or
`[data-syn-state="loading"]`. It also supports `turbo-frame[busy]` and
request classes on enclosing HTMX, Unpoly and LiveView forms.
Datastar can explicitly bind `data-syn-state` to its own request-indicator
signal; Syntyr does not inspect or create Datastar signals. It never manages
`aria-busy`, disabled state, network requests, focus, announcements,
morphing, DOM lifecycle, or retries. Native disabled buttons retain
their disabled cursor; visual feedback does not block double submissions.

Keep `.syn-root` and `data-syn-theme` on a stable ancestor **outside**
the element that Turbo/HTMX replaces or that LiveView/Livewire morphs.
Prefer stable, unique input and form IDs. A server-rendered validation
message must use an associated `aria-describedby` and `aria-invalid`
on the input. Do not use `phx-update="ignore"` or `wire:ignore` just to
make styling survive framework patches.

## Phoenix LiveView (HEEx)

[Copyable HEEx form](https://github.com/dporkka/syntyr-css/blob/main/examples/server-rendered/liveview.heex)
uses the normal `phx-change` and `phx-submit` handlers. Server assigns
control the value and validation error:

```heex
<section class="syn-root" data-syn-theme="studio">
  <form id="campaign-form" class="syn-form" phx-change="validate" phx-submit="save">
    <label class="syn-label" for="campaign-name">Campaign</label>
    <input id="campaign-name" class="syn-input" name="campaign[name]"
           value={@name} aria-invalid={if @error, do: "true", else: "false"} />
    <button class="syn-button syn-button--primary" type="submit"
            phx-disable-with="Saving...">Save</button>
  </form>
</section>
```

LiveView adds `phx-submit-loading`, `phx-click-loading`, and
`phx-change-loading` to the relevant element or form while awaiting the
server. Its own `phx-disable-with` and form behavior handle interaction
locking; Syntyr never duplicates that logic. Include LiveView's ordinary
JavaScript bootstrap in your Phoenix application, not in Syntyr.

## Laravel Livewire (Blade)

[Copyable Blade form](https://github.com/dporkka/syntyr-css/blob/main/examples/server-rendered/livewire.blade.php)
uses `wire:submit`, `wire:model.live`, and Blade validation messages:

```blade
<section class="syn-root" data-syn-theme="studio">
  <form class="syn-form" wire:submit="save">
    <label class="syn-label" for="campaign-name">Campaign</label>
    <input id="campaign-name" class="syn-input" wire:model.live="name"
           aria-invalid="{{ $errors->has('name') ? 'true' : 'false' }}" />
    <button class="syn-button syn-button--primary" type="submit">Save</button>
  </form>
</section>
```

**Livewire 4** automatically adds `data-loading` to request-triggering
elements. Syntyr's optional CSS recognizes it without Tailwind. In
**Livewire 3**, use `wire:loading`, `wire:loading.attr="disabled"`,
or your own native `aria-busy`/`data-syn-state` binding where needed;
do not assume the v4 automatic attribute exists. For loading text,
prefer Livewire's own `wire:loading` and `wire:target` controls. Its
client runtime comes from the Laravel application.

## Rails Hotwire / Turbo Frames

[Copyable Turbo form](https://github.com/dporkka/syntyr-css/blob/main/examples/server-rendered/turbo.html)
uses a normal GET form to update only a matching frame. For a running
server-backed fixture with a real Turbo 8.0.23 browser integration,
see [examples/turbo.html](https://github.com/dporkka/syntyr-css/blob/main/examples/turbo.html)
and [examples/hypertext_server.py](https://github.com/dporkka/syntyr-css/blob/main/examples/hypertext_server.py):

```html
<section class="syn-root" data-syn-theme="studio">
  <form action="/campaigns" method="get" data-turbo-frame="campaign-results">
    <label for="q">Campaign</label>
    <input id="q" class="syn-input" name="q">
    <button class="syn-button" type="submit">Search</button>
  </form>
  <turbo-frame id="campaign-results"></turbo-frame>
</section>
```

The server must return a matching `<turbo-frame id="campaign-results">`
element. Turbo toggles `turbo-frame[busy]` while it fetches a replacement. The
optional CSS bridge styles enabled Syntyr buttons **inside** a busy frame;
for a button outside that frame, bind an application-owned
`data-syn-state="loading"` rather than expecting CSS to infer cross-frame
request ownership.
For the runnable example, start `python3 examples/hypertext_server.py` and
open `http://127.0.0.1:8767/examples/turbo.html`. The server distinguishes
`Turbo-Frame: customer-results` from native navigation, returns a matching
frame for enhanced requests, returns complete HTML for native GET requests,
and sets `Vary: Turbo-Frame` to avoid cross-representation caching issues.
The Turbo browser dependency is pinned and demo-only; self-host the bundle
in production. Syntyr never includes it.

### Turbo Streams: independent server-updated regions

The same runnable Turbo 8 example now includes a **GET stream form** outside
the frame. Add `data-turbo-stream="true"` to the form, keep the target inside a
stable `.syn-root`, and return an action targeting that element:

```html
<form action="/customers/turbo-stream" method="get" data-turbo-stream="true">
  <label for="stream-q">Customers</label>
  <input id="stream-q" class="syn-input" name="q">
  <button class="syn-button" type="submit">Update</button>
</form>
<div id="turbo-stream-results" class="syn-panel" aria-live="polite"></div>
```

An enhanced request with `Accept: text/vnd.turbo-stream.html` gets a
`text/vnd.turbo-stream.html` response with a `<turbo-stream action="update"
target="turbo-stream-results">` and escaped, server-rendered HTML in a
`<template>`. Native GET navigation returns a complete document with
the result in the correct region, not duplicate results in both the frame
and stream target. Set `Vary: Accept` to distinguish the two representations.
The example uses normal HTTP responses rather than WebSockets or SSE; Turbo
Streams can also arrive over those transports when the application provides them.
The original frame remains mounted when the stream updates its separate target.

Turbo Streams and full-page visits must keep the Syntyr root appropriately
scoped. Where Turbo must preserve a client-managed element, use
`data-turbo-permanent` with a stable unique ID on both versions. Do not put
an entire theme root inside a routinely replaced frame.
Forms with mutations still need application-owned authentication,
CSRF protection and server validation. This recipe does not ship Turbo.

## Go templ and other server template engines

[Copyable Go templ search template](https://github.com/dporkka/syntyr-css/blob/main/examples/server-rendered/search.templ)
shows a native GET form with escaped templ values. Serve the same CSS
from Go's static assets. The request handler performs the search and
renders the next HTML response; Syntyr does not add a Go dependency.

Django/Jinja, Symfony/Twig, ASP.NET Razor, Spring Thymeleaf, Hugo/Zola,
and other HTML renderers need no special integration: render actual
`<label>`, `<input>`, `<button>` and `<form>` elements with `syn-`
classes, apply `aria-invalid` and `aria-describedby` from server
validation, and keep static assets versioned. Choose framework-native
partials/components and anti-CSRF mechanisms.

**Verification scope:** the optional bridge and copyable templates have
Python standard-library contract tests. HTMX has an existing opt-in browser
suite; Datastar has an opt-in browser test using a pinned bundle.
Unpoly 3.15.0 and Turbo 8.0.23 have real, opt-in browser tests in
`tests/hypertext_browser.py` that cover request feedback, DOM replacement,
Turbo Stream updates, Unpoly 422 validation/error recovery, theme-root
survival, and no-JavaScript form fallback in Chromium and Firefox
(and in WebKit only on a compatible Playwright container). The demo servers
also have request/response tests. Simulated browser checks confirm that
Livewire 4's `data-loading` and LiveView's `phx-*loading` cursor selectors
are scoped to Syntyr and do not override native disabled controls.
This is **not** a claim that Phoenix,
Laravel, Rails, or Go application runtime tests have run. Add framework-owned
end-to-end tests when adopting templates.

## Lit / Web Components

Syntyr works with Lit but does not depend on it. Lit components using light DOM
can use ordinary `.syn-*` classes within a Syntyr root. Components with Shadow
DOM need local internal styles consuming inherited `--syn-*` tokens, and may
expose supported styling surfaces with `::part()`. Stylesheets in the page do
not automatically style the inside of a shadow root. See the
[Lit integration guide](lit-integration.md), [optional runnable example](https://github.com/dporkka/syntyr-css/tree/main/examples/lit)
and [component-authoring conventions](component-authoring.md).

## Alpine.js

Use native attributes for real state, and Syntyr classes for presentation:

```html
<div class="syn-root" x-data="{ selected: false }">
  <button class="syn-button" type="button"
          :aria-pressed="String(selected)" @click="selected = !selected">
    Toggle details
  </button>
</div>
```

Mount Alpine once in the host app. For `x-cloak`, define a tiny application
rule `[x-cloak] { display: none !important; }` before Alpine initializes.
Syntyr doesn't manage Alpine state.

## Datastar (signals + HTML/SSE morphing)

[Runnable Datastar example](https://github.com/dporkka/syntyr-css/blob/main/examples/datastar.html)
and [stdlib HTTP server](https://github.com/dporkka/syntyr-css/blob/main/examples/datastar_server.py)
demonstrate a real GET fallback and a Datastar SSE response:

```sh
python3 examples/datastar_server.py
# open http://127.0.0.1:8766/examples/datastar.html
```

The demo opts into a **pinned Datastar v1.0.5** browser script. That is an
application/demo dependency, not bundled or injected by Syntyr. Self-host the
pinned script in production.

```html
<main class="syn-root" data-syn-theme="studio">
  <form action="/customers/search" method="get"
        data-indicator:_fetching
        data-on:submit="!$_fetching && @get('/customers/search')"
        data-attr:aria-busy="String($_fetching)">
    <label class="syn-label" for="q">Customer</label>
    <input id="q" name="q" class="syn-input" data-bind:q>
    <button type="submit" class="syn-button"
            data-attr:disabled="$_fetching"
            data-attr:data-syn-state="$_fetching ? 'loading' : null">
      Search
    </button>
    <output role="status" data-show="$_fetching" style="display: none">
      Searching…
    </output>
  </form>
  <section id="customer-results" aria-live="polite"></section>
</main>
```

The framework owns `data-indicator`, `data-bind:q`, `data-on:submit`,
disabled state, and the SSE morph. The server returns
`event: datastar-patch-elements` with a matching `id="customer-results"`
and escapes user content. Serialize each SSE patch as a single data line:
normalize carriage returns and line feeds *after* HTML escaping, since HTML
escaping alone does not prevent attacker-controlled SSE record boundaries.
Because Datastar GET requests send signal values
inside a `datastar` query parameter, the sample endpoint reads that JSON for
SSE requests and reads ordinary `q` for no-JavaScript GET requests.

**Keep `.syn-root` and the form outside the morphed results section.**
The native GET fallback re-renders the escaped search term into the form
value as well as the results, so users do not lose what they searched for.
Syntyr's `data-syn-state` bridge is optional; the native disabled state and
status message work independently of the progress cursor. Never rely on
`aria-busy` or a CSS class alone to prevent duplicate mutations.

Datastar `data-on:submit` automatically prevents native form navigation when
the framework has initialized. Keep a real `action` and `method` so the form
still works without Datastar. Prefer `data-class:*` to toggle state classes
without overwriting a stable `syn-*` component class; use `data-attr:aria-*`
to communicate interactive state. Keep the Syntyr theme root out of any
SSE morph target and return a stable ID for the target.

Datastar expressions execute JavaScript. Do not interpolate untrusted data into
`data-*` expressions, do not put secrets in signals, validate on the server,
and adopt Datastar's documented nonce-based **CSP** mode when forbidding
`unsafe-eval`. Syntyr requires neither `unsafe-eval` nor a nonce.
Neither framework owns the other's initialization lifecycle.

## Unpoly

[Runnable Unpoly 3.15.0 demo](https://github.com/dporkka/syntyr-css/blob/main/examples/unpoly.html)
shares the [local HTTP server](https://github.com/dporkka/syntyr-css/blob/main/examples/hypertext_server.py)
with the Turbo demo. Run `python3 examples/hypertext_server.py` and open
`http://127.0.0.1:8767/examples/unpoly.html`.
The example pins the JS and CSS bundles; both belong to the demo application,
not Syntyr. Self-host both in production.

Unpoly can update multiple fragments from a single response. The runnable
example uses `up-target="#customer-results, #unpoly-search"` so a successful
search refreshes the result and re-renders the form, including clearing any
previous validation error. An empty query returns HTTP **422**, with
`up-fail-target="#unpoly-search"` replacing only the form and an associated
`aria-invalid="true"` / `aria-describedby="unpoly-search-error"` message.
A subsequent valid submission clears both the invalid state and message.
The no-JavaScript fallback receives a complete document, including the
form error, instead of an orphaned fragment. These are **server-side application
behaviors**, not Syntyr CSS features.

Unpoly adds `.up-active` to an initiating link or form and `.up-loading`
to the targeted fragment. Syntyr's optional `syntyr.server.css` styles the
progress cursor on an enabled `.syn-button.up-active` or the enabled
submit button inside `form.up-active`, without hiding, dimming, or blocking
the target. Unpoly owns response handling, loading feedback and morphing.

```html
<section class="syn-root" data-syn-theme="studio">
  <form action="/customers" method="get"
        up-target="#customer-results, #customer-search" up-fail-target="#customer-search"
        id="customer-search">
    <label class="syn-label" for="customer-query">Customer</label>
    <input id="customer-query" class="syn-input" name="q">
    <button class="syn-button" type="submit">Search</button>
  </form>
  <div id="customer-results" aria-live="polite"></div>
</section>
```

The example server responds with an HTML document containing
`#customer-results`; Unpoly extracts and replaces the matching fragment.
Without JavaScript, a native GET responds with the same complete document.

Retain a real `action`, `method` and stable target ID. Keep the Syntyr root
outside any fragment Unpoly replaces; do not interpret `.up-loading` as a
reason to suppress keyboard interaction or hide results. Syntyr does not
include Unpoly or override its default CSS.

## React / Next.js

```jsx
import "./syntyr.core.css";

export function StatusCard({ status }) {
  return (
    <section className="syn-root" data-syn-theme="studio">
      <article className="syn-panel">
        <h2 className="syn-heading">Operations</h2>
        <p>{status}</p>
      </article>
    </section>
  );
}
```

Import CSS once from the app entry point (or root layout, as supported by
the framework). No Syntyr provider, hooks, hydration, or dependency on React.

## Vue / Nuxt and Svelte / SvelteKit

Import the same CSS once. Bind native classes, `aria-*`, and
`data-syn-state` using each framework's built-in template syntax.
Do not wrap simple visual classes in additional runtime components unless the
application benefits from reusable semantic component boundaries.

### Runnable SvelteKit 3 form-action and nested-layout reference

[examples/sveltekit](https://github.com/dporkka/syntyr-css/tree/main/examples/sveltekit)
is a self-contained SvelteKit 3 app with a native HTML POST form and optional
`use:enhance`. It uses existing Syntyr `syn-field`, `syn-error-summary`,
`syn-operation-feedback`, `syn-app-shell`, `syn-detail-layout`, and
`syn-panel` classes rather than introducing framework-specific CSS.

The root `+layout.svelte` provides the persistent application shell, while
`settings/+layout.svelte` composes a nested content and inspector layout.
A small `AppPanel.svelte` shows Svelte 5 named `actions` and `footer`
snippets; they are owned by SvelteKit, not by a new Syntyr templating runtime.
`settings/+page.server.js` handles server validation and sends either
an action failure or a success acknowledgement. A normal browser POST is
functional without JavaScript; enhancement only adds in-flight feedback
and error-summary focus management. The example **does not persist data**
and is not a production authentication or CSRF implementation.

From the repository root, first generate CSS with `python3 scripts/build.py`,
then run `cd examples/sveltekit && npm install && npm run test && npm run build`.
The root Syntyr package still has zero required JavaScript dependencies.

## Astro, Hugo, Zola, Django, Rails, Go/templ and Rust templates

Serve `syntyr.core.css` as a normal static asset. Write HTML partials
with real headings, forms and links. Optional interactive islands can use
HTMX, Alpine, Datastar, React or native browser elements without changing
Syntyr's HTML/CSS contract. In Rails, Hotwire/Turbo updates have the same
theme-root and swap-boundary considerations as HTMX.

## Existing Tailwind or component-library applications

- Syntyr's `.syn-root` scope and `@layer syn.*` layers limit unintended
  interference, but Tailwind Preflight can still change global element defaults.
- Prefer explicit Syntyr classes. Apply `.syn-semantic` only to designated
  regions, not to a whole React/Headless UI component tree.
- Override public `--syn-*` tokens in application CSS; avoid copying or
  rebuilding utility frameworks inside Syntyr.
- Test cascade ordering, focus rings, dark/light color schemes, zoom and
  third-party components after integration.

## Performance and compatibility contract

- CSS bytes are tracked by `python3 scripts/asset_report.py` with optional JSON baseline comparisons; no arbitrary gzip release gate.
- Syntyr runtime JS: **zero**. HTMX/Alpine/React are host-app dependencies.
- Self-host assets on the app's own origin when practical; pin external CDN
  versions. Don't load both `syntyr.all.css` and its constituent stylesheets.
- Use Playwright or equivalent browser automation to verify dynamic class
  changes, HTMX fragments, responsiveness and accessibility.
- Avoid large DOM swaps, expensive decorative effects on scrolling tables,
  and unnecessary hydration. Measure actual page LCP, CLS and INP.
