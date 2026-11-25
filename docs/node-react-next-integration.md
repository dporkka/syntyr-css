# Node.js, React and Next.js adoption (experimental)

**Status:** This guide describes the unreleased alpha.5 source candidate and
its unpublished **optional** React package. Neither npm package has been
approved for publication. Install local packages from this repository to try
the examples; never assume these names are available on the public registry.

Syntyr's permanent contract remains standard CSS and HTML:
`syn-*` classes, `--syn-*` tokens, `data-syn-*` attributes,
and the scoped `.syn-root` boundary. The CSS package has no browser
JavaScript, React or Node.js runtime dependency. These examples exercise
actual consumers instead of asserting compatibility from snippets.

## Run real consuming builds

Requires Node.js 20.9+ and npm, plus Python 3 for the runner.
From the repo root:

```sh
python3 scripts/test_js_adoption.py --install
```

The runner builds and runs server-rendered React tests, builds the React,
Preact and Solid Vite consumers and the Next.js app, then performs a real
Express HTTP smoke test. After the
first installation, omit `--install`. npm fixture lockfiles and node_modules
are intentionally ignored to avoid consumer dependencies in the CSS project.

## Optional browser validation

After a successful build, a real Chromium smoke checks both applications at
390px for CSS application, mobile overflow, React interaction, JavaScript
exceptions and hydration errors:

```sh
python3 -m venv /tmp/syntyr-js-browser
/tmp/syntyr-js-browser/bin/pip install playwright
/tmp/syntyr-js-browser/bin/python -m playwright install chromium
/tmp/syntyr-js-browser/bin/python tests/js_adoption_browser.py
```

The separate Woodpecker `js-adoption` pipeline builds the same consumers
without imposing Node.js on the standard CSS quality pipeline. Its npm step
runs when CSS, package, adapter, build or relevant consumer fixture paths
change; it remains manually runnable for release verification. Documentation-
only PRs skip that step. Such a skip is not proof of passed consumer builds;
run the adoption suite before a release regardless of PR path filtering.
The optional browser smoke is a maintainer check, not a claimed CI browser gate.

For direct JSX/TSX use without the experimental wrappers, and Preact and Solid
fixtures, see [JSX and TSX adoption](jsx-tsx-integration.md).

## React + Vite

Source: [examples/react-vite](../examples/react-vite/).

```tsx
import "@syntyr/css/core.css"; // src/main.tsx, once
import { SyntyrRoot, Card, Button } from "@syntyr/react";

export function Example() {
  return (
    <SyntyrRoot theme="studio">
      <Card><Button variant="primary">Save</Button></Card>
    </SyntyrRoot>
  );
}
```

The optional React package uses TypeScript and React peer dependencies.
It exposes only presentational wrappers with native DOM props and forwarded
refs: SyntyrRoot, Button, Card, Badge, Input, Select and Textarea.
It imports **no** CSS automatically; it introduces **no** context provider,
hooks, event handlers, or browser globals. Interactive behavior belongs
to the consuming app. Button defaults to `type="button"` to avoid accidental
submissions, and can explicitly accept `type="submit"`.

## Next.js App Router

Source: [examples/next-app-router](../examples/next-app-router/).
The root layout loads CSS once and establishes the stable `SyntyrRoot`
boundary. Server Components render Card, Badge and Input without a client
directive. A small standalone counter explicitly uses `"use client"`,
`useState` and Button for optional interaction.

```tsx
// app/layout.tsx (server by default)
import "@syntyr/css/core.css";
import { SyntyrRoot } from "@syntyr/react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>
    <SyntyrRoot theme="studio">{children}</SyntyrRoot>
  </body></html>;
}
```

The local Next.js 16 fixture also contains `next.config.mjs` with an explicit
`turbopack.root` pointing to the repository root. Turbopack otherwise infers
the example app as its filesystem root and cannot resolve the locally linked
`file:` `@syntyr/css` and `@syntyr/react` dependencies outside that directory.
This is a **development monorepo setting**, not a required configuration for
normal published npm packages or a change to Syntyr's CSS runtime. Keep it
rooted to the narrowest common ancestor of the app and local packages; avoid
absolute machine paths or a global filesystem root.

In Pages Router projects, import global CSS once in `pages/_app.tsx`
rather than in individual pages. No separate `@syntyr/next` package is
necessary. Keep client boundaries small; no Syntyr-specific hydration step
is needed. Keep theme values stable across server and client rendering and
place Radix portals inside the theme root or explicitly scope their styles.

## Node.js backend with Express/EJS

Source: [examples/node-express](../examples/node-express/).

Express serves the package's installed CSS asset using
`import.meta.resolve("@syntyr/css/core.css")`, and EJS uses `<%= ... %>`
for escaped dynamic values. A GET search form works without JavaScript.
The HTTP test verifies stylesheet delivery, filtering and HTML escaping.
For Fastify, NestJS or other Node HTML engines, serve a pinned local CSS
asset and output identical `syn-*` classes. Syntyr itself should not
provide a backend middleware, authentication handler or form state engine.

Only use long-lived immutable caching with fingerprinted/versioned **URLs**.
This example serves a short-cache unversioned `/css/` path intentionally.

## Integration guarantees and boundaries

- **CSS isolation:** Load the core once; style descendants under a stable
  `.syn-root` element. Load `recipes.css` separately only if used.
- **React compatibility:** Native attributes, refs, ARIA and semantic HTML
  remain application-controlled. Complex accessible widgets should use
  native primitives or application-owned Radix, not CSS imitation.
- **Server rendering:** Presentational wrappers do not force a client
  boundary. The Next.js example verifies an actual production compilation.
- **Packaging:** React wrappers are private/unpublished. The local
  `file:` references require building `packages/react` before installing
  fixtures. The runner enforces this order.
- **Verification:** Python source contracts are always included in the
  repository's standard tests; npm builds are opt-in and require external
  developer tooling. Browser-based hydration, keyboard, forced-colors and
  screen-reader testing remain independent release checks.

Do not split CSS implementation across React/Next/Node-specific forks.
Components and tokens must remain authored once in the framework-neutral
Syntyr stylesheet contract.
