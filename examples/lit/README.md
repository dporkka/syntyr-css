# Optional Syntyr + Lit example

This is **not** a Syntyr runtime dependency or part of the Cloudflare static-site
allowlist. It demonstrates two independent Web Component styling strategies:

- **Light DOM**: Lit renders normal Syntyr classes into the page. The standard
  `syntyr.core.css` stylesheet applies without copying it into a Shadow Root.
- **Shadow DOM**: Lit keeps its default shadow boundary. Local `static styles`
  consume inherited `--syn-*` custom properties and expose `::part()` hooks.

## Additional integration fixtures

- `react-interop.html` uses React 19 custom-element event interop and Lit
  light DOM with the unchanged Syntyr core stylesheet.
- `htmx-interop.html` uses a native GET form, real HTMX 2.0.8, and a local
  HTML response. With JavaScript disabled, the form navigates normally; with
  HTMX it swaps the custom-element host while the theme root remains stable.

The sample uses no remote runtime assets and neither framework is a Syntyr
package dependency. These are integration tests, not production applications.
Backend authorization, persistence, mutation validation and CSRF protection
remain application concerns.

## Run locally

From this directory, with Node.js and npm available:

```sh
npm ci
npm run build
cd ../..
python3 -m http.server 8765 --bind 127.0.0.1
# Open http://127.0.0.1:8765/examples/lit/index.html
```

The pages use local bundled modules and the repository's built CSS. The lockfile
pins the opt-in example dependencies. There is no runtime network request to a
third-party CDN. Run `python3 scripts/build.py` at repository root if CSS
artifacts need regeneration.

To run Lit, React 19, and HTMX browser coverage after building:

```sh
cd examples/lit
npm test
```

Requires the locally pinned `@playwright/test` development dependency and
installed browser binaries. The dedicated CI pipeline supplies all three browser
engines; unavailable engines fail visibly rather than being counted as passing.

The HTML includes static fallback markup for both components. Without JavaScript,
this remains readable; enhanced buttons intentionally operate on **local demo
state only**. The real application must own persistence and authorization.

See [the Lit integration guide](../../docs/lit-integration.md) and
[component-authoring contract](../../docs/component-authoring.md).
