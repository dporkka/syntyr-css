# Syntyr + SvelteKit 3: progressive, server-rendered forms

An isolated, runnable demonstration of native HTML form actions, nested layouts
and named Svelte 5 composition snippets with **existing Syntyr CSS primitives**.

From this directory (Node.js 22.17 or newer):

```sh
npm install
npm run test
npm run build
npm run dev -- --host 127.0.0.1
# visit http://127.0.0.1:5173/settings
```

Syntyr itself has **no JavaScript runtime**, provider, router or hydration
requirement. SvelteKit handles routes and server-side action results; optional
`use:enhance` prevents a full-page reload if client JavaScript is enabled.
Disable JavaScript and submit the same **POST** form to verify the fallback.

## How the composition works

- `src/routes/+layout.svelte` imports Syntyr core and recipes CSS from the
  repository build; the root uses `syn-root`, `syn-app-shell`, and `syn-app-rail`.
- `src/routes/settings/+layout.svelte` adds a nested content/inspector region
  using existing `syn-detail-layout` and `syn-detail-aside` classes.
- `src/lib/AppPanel.svelte` demonstrates named `actions` and `footer` snippets
  and a `children` snippet. This is Svelte-owned composition, **not** a
  new Syntyr component language.
- `+page.server.js` returns a 400 action failure for invalid names; the view
  associates `aria-invalid`, `aria-describedby`, field messages and a
  focusable error summary. On successful responses, it shows a visible text
  status using the existing `syn-operation-feedback` pattern.
- `use:enhance` owns the pending indicator, disables the submit button
  while sending, and focuses the server-returned error summary. CSS alone
  does not prevent double submits or manage accessibility announcements.

The server trims and limits submitted names to 2–80 Unicode code points,
avoiding malformed surrogate-pair truncation and unbounded echoed payloads.
Native HTML `minlength`/`maxlength` count UTF-16 units rather than Unicode
code points, so this example leaves length checks to the server (while retaining
native `required`). The input becomes read-only while an enhanced POST is
pending to avoid overwriting newer edits with a stale server response.
Malformed multipart/form data receives a recoverable HTTP 400 response. This is a **demo-only validation endpoint**:
successful requests **do not persist anything**. Production code must
add authentication, per-record authorization, CSRF safeguards (retain the
framework's origin checking), persistent storage, rate limits, logging and
appropriate conflict/duplicate-submit controls. Do not deploy this fixture
as an account settings service.

## Validation

`npm run test` runs Node unit tests for validation and a Vite-backed HTTP
integration test of native GET/POST action responses, error semantics and HTML
escaping. `npm run build` compiles the real SvelteKit 3 application.
SvelteKit's built-in origin-based CSRF check is active in production, not in
its local development server; do not treat a development POST as a security test.
The host imports the existing CSS modules; **no Svelte-specific styles or
JavaScript become part of Syntyr Core**.

This reference intentionally doesn't use SvelteKit routing as a Syntyr API.
Users of Go/templ, Phoenix, Rails or React can copy the same HTML/CSS classes
while supplying their own server actions and state ownership.
