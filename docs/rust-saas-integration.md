# Optional Rust SaaS Foundation / Askama / HTMX integration

An opt-in Syntyr profile is implemented on the
`feat/optional-syntyr-skin` integration branch of
`dporkka/rust-saas-foundation`. It uses a separate Askama page template,
shares the original `catalog.html` fragment, and does not require npm,
external assets, or any additional runtime JavaScript.

The source adapter is `integrations/rust-saas-foundation/catalog.css`.
It scopes the existing `.wrap`, `.items` and `.item` classes beneath
`.syn-rust-foundation` so the default page is unaffected. Load a pinned
Syntyr core stylesheet first, then the adapter. The optional page sets
`class="syn-root syn-rust-foundation"` and `data-syn-theme="studio"`.

The Rust integration vendors the **published alpha.4 core CSS** and serves
versioned assets from the application binary. The optional Syntyr page includes
a keyboard-revealed skip link to its focusable main landmark; the adapter
styles that link in normal and forced-colors modes. The updated bridge is
versioned as `/assets/syntyr/bridge2/catalog.css` to avoid stale immutable CSS.
It exposes `APP_UI_SKIN=syntyr` at startup; unknown values are rejected. The backend's identity, tenants,
permissions, PostgreSQL queries and HTMX fragments are not touched.

This demonstrates a public catalog. It does not prove an authenticated admin
flow or certify accessibility. Browser, keyboard, contrast and zoom tests on
real application pages are required before production claims.

## Runnable independent Axum / Askama starter

The [Rust Axum starter](../examples/rust-axum/README.md) demonstrates a
fully runnable, read-only server-rendered project dashboard rather than
an illustrative template. It uses Askama's default HTML escaping, a normal GET
search form, accessible server-side search-length validation, a native table
and an explicit scoped Syntyr theme.

Run from the repository root:

    cd examples/rust-axum
    cargo test --locked
    cargo run --locked

The app compiles the repository's generated core CSS into its binary using
Rust include_str!; deployed applications should vendor and pin a released
stylesheet rather than relying on an upstream development tree. No additional
Syntyr Rust package or client-side JavaScript is involved. This sample makes
no claims about user authentication, authorization, mutation safety or
production readiness beyond the demonstrated read-only flow.
