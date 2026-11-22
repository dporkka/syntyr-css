# HTMX components and server-rendered UI patterns

Use Syntyr's existing CSS components with **HTMX as an optional enhancement** for server-rendered HTML. These are **12 copy-owned recipes**, not a JavaScript widget runtime or prebuilt backend. Each code sample assumes an application endpoint that returns complete documents on ordinary requests and an appropriate fragment on HTMX requests.

**Availability:** This page describes the **unreleased 0.3.0-alpha.5 source candidate**, not the published alpha.4 release. Core CSS works independently of HTMX; the optional adapter only styles request indicators and opt-in swap transitions.

## Install and compatibility

Self-host pinned copies of your chosen Syntyr release and HTMX. Add the optional adapter *after* core CSS, if you want its states. Do not bundle HTMX or load it automatically as part of Syntyr.

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.htmx.css">
<script defer src="/js/htmx.min.js"></script>
<main class="syn-root" data-syn-theme="studio">
  <!-- Keep this root outside hx-target replacements. -->
</main>
```

The additional CSS is the copy-owned file [`integrations/htmx/syntyr.htmx.css`](https://github.com/dporkka/syntyr-css/blob/main/integrations/htmx/syntyr.htmx.css), or the optional `@syntyr/css/htmx.css` package export **once an alpha.5 package actually ships**. You can omit it entirely and reuse [`syntyr.server.css`](framework-integrations.md) for a loading cursor. The adapter uses opt-in `.syn-htmx-indicator` and `data-syn-htmx-transition`; both are scoped under `.syn-root`. The adapter is not part of core or the all-in-one CSS bundle.

For strict Content Security Policy, self-host the HTMX script and disable its injected indicator CSS. In **HTMX 2**, set `includeIndicatorStyles: false`; in **HTMX 4**, use `includeIndicatorCSS: false`. HTMX 4 also renames the v2 `hx-disabled-elt` attribute to `hx-disable`. Check the relevant HTMX release documentation before choosing a version; avoid mixing configuration names.

**Server rules for all recipes:** Authenticate and authorize each request, escape all untrusted HTML, validate and bound query values, use CSRF protection on mutations, and return the right status codes. For cacheable endpoints that serve both pages and fragments, set `Vary: HX-Request, HX-History-Restore-Request`. A request with `HX-History-Restore-Request: true` must receive a complete document, even if `HX-Request: true` is also present. In HTMX 2, configure `historyRestoreAsHxRequest: false` when using split responses. Treat 422 error-fragment swapping as **app-owned**: HTMX 2 does not automatically swap all error responses.

## Search and tables

### 1. Live search

A native GET form remains functional when HTMX is absent. Return a list fragment for HTMX and a full results page for ordinary GET requests.

```html
<form action="/customers" method="get" role="search" class="syn-stack">
  <label for="customer-query">Search customers</label>
  <input id="customer-query" class="syn-input" type="search"
         name="q" maxlength="120" placeholder="Customer name"
         hx-get="/customers" hx-trigger="input changed delay:300ms, search"
         hx-target="#customer-results" hx-push-url="true"
         hx-indicator="#search-indicator">
  <button class="syn-button" type="submit">Search</button>
  <span id="search-indicator" class="syn-htmx-indicator" role="status">Searching…</span>
</form>
<section id="customer-results" aria-live="polite" aria-label="Search results">
  <p>Enter a name or submit the form.</p>
</section>
```

### 2. Pagination

Server-render the entire table-and-pager region on each page. Real links preserve keyboard and no-JavaScript navigation.

```html
<section id="customer-list">
  <div class="syn-table-wrap">
    <table class="syn-table"><caption>Customers</caption>
      <thead><tr><th scope="col">Name</th></tr></thead>
      <tbody><tr><td>Acme</td></tr></tbody>
    </table>
  </div>
  <nav aria-label="Customer pages">
    <a href="/customers?page=2" class="syn-button"
       hx-get="/customers?page=2" hx-target="#customer-list"
       hx-swap="outerHTML" hx-push-url="true">Next page</a>
  </nav>
</section>
```

### 3. Sortable table

The backend owns sort direction, allowlisted sort keys and updated `aria-sort` attributes. Replace the full region so table headings and rows stay synchronized.

```html
<section id="orders-table" aria-label="Orders">
  <div class="syn-table-wrap">
    <table class="syn-table">
      <caption>Recent orders</caption>
      <thead><tr>
        <th scope="col" aria-sort="ascending">
          <a class="syn-table-sort" href="/orders?sort=name_desc"
             hx-get="/orders?sort=name_desc" hx-target="#orders-table"
             hx-swap="outerHTML" hx-push-url="true">Name</a>
        </th>
        <th scope="col">Amount</th>
      </tr></thead>
      <tbody><tr><th scope="row">Invoice A</th><td>$120</td></tr></tbody>
    </table>
  </div>
</section>
```

## Forms and workflows

### 4. Inline edit

The GET link displays the edit form inside a stable record container; the endpoint also provides a full document for native navigation. The POST form sends a CSRF token and returns a refreshed record fragment to HTMX, or redirects after native POST.

```html
<article id="contact-42" class="syn-panel">
  <h3>Acme contact</h3>
  <p>Owner: Alex</p>
  <a href="/contacts/42/edit" class="syn-button"
     hx-get="/contacts/42/edit" hx-target="#contact-42"
     hx-swap="outerHTML">Edit</a>
</article>
<!-- Example fragment returned by GET /contacts/42/edit: -->
<article id="contact-42" class="syn-panel">
  <form action="/contacts/42" method="post" hx-post="/contacts/42"
        hx-target="#contact-42" hx-swap="outerHTML">
    <input type="hidden" name="csrf_token" value="SERVER_ISSUED_TOKEN">
    <label for="contact-owner">Owner</label>
    <input id="contact-owner" class="syn-input" name="owner" value="Alex" required>
    <button type="submit" class="syn-button">Save</button>
    <a href="/contacts/42">Cancel</a>
  </form>
</article>
```

The second article represents a **response fragment**, not markup to render alongside the first article at the same time.

### 5. Dependent select

The button provides a no-JavaScript fallback to the regions page. HTMX updates the dependent field on change, without changing the form's native GET behavior.

```html
<form action="/regions" method="get">
  <label for="country">Country</label>
  <select id="country" class="syn-input" name="country"
          hx-get="/regions/options" hx-trigger="change"
          hx-target="#region-field" hx-swap="outerHTML">
    <option value="">Choose a country</option>
    <option value="BR">Brazil</option>
    <option value="US">United States</option>
  </select>
  <div id="region-field">
    <label for="region">Region</label>
    <select id="region" class="syn-input" name="region">
      <option value="">Choose a country first</option>
    </select>
  </div>
  <button class="syn-button" type="submit">View regions</button>
</form>
```

The fragment must replace `#region-field` with a labeled, escaped selection. Validate `country` against an allowlist on the server.

### 6. Validated form

Keep native required fields and an error summary. The backend should return a full document on native validation failures; if sending HTMX error fragments with HTTP 422, configure an application-specific error-swap handler.

```html
<form action="/leads" method="post" class="syn-stack"
      hx-post="/leads" hx-target="#lead-feedback">
  <input type="hidden" name="csrf_token" value="SERVER_ISSUED_TOKEN">
  <label for="lead-email">Email</label>
  <input id="lead-email" class="syn-input" type="email"
         name="email" autocomplete="email" required>
  <button class="syn-button syn-button--primary" type="submit">Add lead</button>
  <div id="lead-feedback" aria-live="polite" aria-atomic="true"></div>
</form>
```

On invalid input, server-render `aria-invalid="true"`, an associated `aria-describedby` error, and a clear message in the response. The CSS alone does not add validation.

## Navigation and overlays

### 7. Lazy-loaded navigation

These are **links**, not ARIA tabs. Native navigation works with JavaScript disabled; the server should render the active link state on the next full page or swapped navigation fragment.

```html
<nav aria-label="Account sections" class="syn-inline">
  <a href="/account/profile" hx-get="/account/profile"
     hx-target="#account-content" hx-push-url="true">Profile</a>
  <a href="/account/billing" hx-get="/account/billing"
     hx-target="#account-content" hx-push-url="true">Billing</a>
</nav>
<section id="account-content" aria-live="polite">
  <h2>Account</h2>
  <p>Choose a section.</p>
</section>
```

### 8. Popover details

Use the browser's native popover for opening/closing; HTMX optionally loads the detail body. Provide a full-page link in the fallback content.

```html
<button type="button" class="syn-button"
        popovertarget="invoice-popover"
        hx-get="/invoices/42/summary"
        hx-target="#invoice-summary">Preview invoice</button>
<div id="invoice-popover" popover class="syn-panel">
  <h2>Invoice summary</h2>
  <div id="invoice-summary" aria-live="polite">
    <p><a href="/invoices/42">Open full invoice</a></p>
  </div>
  <button type="button" class="syn-button"
          popovertarget="invoice-popover" popovertargetaction="hide">Close</button>
</div>
```

## Lists, updates and feedback

### 9. Infinite scroll

A real link gives an explicit fallback when `revealed` never fires. The response is a sequence of `<li>` elements ending with the next-page sentinel, or no sentinel at the end.

```html
<ul id="activity-list" class="syn-stack">
  <li>Invoice created</li>
  <li>Campaign approved</li>
  <li hx-get="/activity?page=2"
      hx-trigger="revealed" hx-swap="outerHTML">
    <a href="/activity?page=2">Load more activity</a>
  </li>
</ul>
```

Limit page size and consider explicit pagination for users who cannot or prefer not to scroll.

### 10. Bulk actions

Native POST behavior remains available. Verify that each submitted record belongs to the authenticated tenant; never trust selection values as authorization.

```html
<form action="/contacts/archive" method="post"
      hx-post="/contacts/archive" hx-target="#contact-workspace">
  <input type="hidden" name="csrf_token" value="SERVER_ISSUED_TOKEN">
  <fieldset>
    <legend>Contacts to archive</legend>
    <label><input type="checkbox" name="contact_id" value="42"> Acme</label>
    <label><input type="checkbox" name="contact_id" value="43"> Northstar</label>
  </fieldset>
  <button class="syn-button" type="submit">Archive selected</button>
</form>
<section id="contact-workspace" aria-live="polite"></section>
```

The server must provide a full native response or redirect for POST and an accessible fragment for HTMX. Avoid optimistic deletion of records before the server succeeds.

### 11. Polled status

Polling is optional and must be bounded server-side. The link is a manual refresh fallback; do not poll extremely frequently or announce unchanged text on every interval.

```html
<section aria-label="Export status">
  <div id="export-status" class="syn-panel"
       hx-get="/exports/42/status"
       hx-trigger="every 15s" hx-swap="innerHTML">
    <p>Export pending.</p>
  </div>
  <a href="/exports/42/status">Refresh status</a>
</section>
```

### 12. Request feedback

Loading feedback is not an optimistic mutation. HTMX marks the configured indicator while the request is active; the backend owns the final success or error message.

```html
<form action="/reports" method="get"
      hx-get="/reports" hx-target="#report-results"
      hx-indicator="#report-loading">
  <button type="submit" class="syn-button">
    Generate report
    <span id="report-loading" class="syn-htmx-indicator" role="status">
      Loading…
    </span>
  </button>
</form>
<div id="report-results" aria-live="polite"
     data-syn-htmx-transition>
  <p>Run a report to see results.</p>
</div>
```

In HTMX 2, consider `hx-disabled-elt="find button[type='submit']"` for duplicate-submit prevention; in HTMX 4 use the newer `hx-disable` semantics. Indicator visibility and loading cursors do not block duplicate actions. Avoid moving focus without user intent; test focus and keyboard navigation after fragment replacement.

## Runnable server examples and recipes

The repository already contains [a real Python HTTP-server HTMX search demo](https://github.com/dporkka/syntyr-css/tree/main/examples), [a Go standard-library HTMX starter](https://github.com/dporkka/syntyr-css/tree/main/examples/go-htmx), and [a Node.js fragment server](https://github.com/dporkka/syntyr-css/tree/main/examples/server-components-node/fragments). They test concrete server response behavior and do not require Syntyr runtime JavaScript.

**Go/templ:** Apply the same `hx-*` attributes to the HTML emitted by your templ components; render a full page for ordinary navigation and component fragments for HTMX requests. See the [copy-owned templ component adapter](https://github.com/dporkka/syntyr-css/tree/main/examples/server-components-templ).

**Django:** Use standard Django templates with `request.headers.get("HX-Request") == "true"` to select a fragment *only when the request is not a history restore*. Use Django's `{% csrf_token %}` for POST forms, HTML autoescaping, method checks, and template-rendered validation errors. This is an integration recipe, not a runnable Django project included in this repository.

**Pro / Studio boundary:** This entire set of basic recipes and optional CSS is MIT-licensed. Advanced data-grid controllers, tenant-aware workflows and full SaaS templates would require separately developed application code; they are not included or available for sale here.
