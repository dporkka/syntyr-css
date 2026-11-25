# Syntyr + Axum + Askama: runnable Rust starter

This is a **read-only** server-rendered projects dashboard. It demonstrates
native GET search, accessible server-side validation and an HTML table. It uses
normal Syntyr classes and embeds the versioned CSS artifact directly from this
repository at compile time.

Run from this repository checkout:

    cd examples/rust-axum
    cargo test --locked
    cargo run --locked
    # Open http://127.0.0.1:3000

The example uses include_str! to consume dist/syntyr.core.css at compile time.
CSS travels inside the Rust binary, so no CDN, Node.js, npm, runtime JavaScript,
Sass, or runtime CSS dependency is needed. When copying this example to a
separate repository, vendor a **version-pinned** release CSS file and update
the include_str! path accordingly.

## Production boundaries

- Read-only GET search: no writes, login system or CSRF demonstration. Add
  framework-native authorization, CSRF and server validation before mutations.
- Askama performs automatic HTML escaping on dynamic template fields; do not
  mark user-controlled strings as safe HTML. Request errors are visible through
  aria-invalid and aria-describedby.
- The demo binds to localhost. Configure production listeners, HTTPS, cache
  versioning and error reporting in your actual application.
- Seed rows are illustrative, not a production access-control or multi-tenancy
  implementation.
- CSS is served from the same origin with an explicit text/css MIME type.
- Run a browser keyboard, zoom and contrast audit on adapted application pages.
