# Optional package-manager installation (alpha.5 candidate)

**Status: prepared for distribution, not published to npm.** `@syntyr/css` is the intended package name, pending registry ownership/availability verification and an approved prerelease. Until then, use the [published alpha.4 release](distribution.md) or locally pack the alpha.5 candidate. Do not claim that `npm install @syntyr/css` currently succeeds.

Syntyr's canonical artifact remains the ordinary CSS files in `dist/`. The npm package is a second **distribution path** for projects that already use a package manager; it adds **no JavaScript code, runtime dependencies, compiler, provider, or CSS-in-JS runtime**. Plain HTML and server templates can continue to self-host the versioned CSS with no toolchain.

## Local verification before publication

From this repository checkout:

```sh
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v
npm pack --dry-run --json --ignore-scripts
npm pack --ignore-scripts
python3 scripts/audit_npm_package.py  # verifies the real tarball, requires npm only for this check
```

The `npm pack` command creates `syntyr-css-0.3.0-alpha.5.tgz` locally; it does not publish to a registry. The subsequent audit packs a **separate temporary tarball**, validates every exported CSS file and its bytes against source, rejects extra files (including secrets), links and archive traversal, and deletes the temporary archive. For an already-created tarball, run `python3 scripts/audit_npm_package.py --archive /path/to/package.tgz` without invoking npm. This maintainer check is not a consumer build step. For a real Vite/React/Astro/Next application using a package manager, install that local archive for testing:

```sh
npm install /path/to/syntyr-css-0.3.0-alpha.5.tgz
```

After the scoped name is verified, the release is approved, and the package is actually published, consumers can use `npm install @syntyr/css@<published-version>` instead.

## Import the CSS

In an application CSS entrypoint processed by a bundler that supports package CSS imports:

```css
@import "@syntyr/css/core.css";
/* Optional application layout recipes: */
@import "@syntyr/css/recipes.css";
```

Alternatively, import once from a supported JavaScript application entrypoint:

```js
import '@syntyr/css/core.css';
```

This is a **build-time stylesheet import** in the host application, not Syntyr JavaScript. For a browser `<link>` tag, serve a **copied CSS asset** at a real URL: browsers do not resolve the bare `@syntyr/css/...` package specifier in `href`.

Available subpaths: `core.css` (default), `semantic.css`, `server.css` (optional server-HTML state bridge), `semantic-bundle.css` (one-file core + semantic), `recipes.css`, `effects.css`, `geometry.css`, `symbols.css`, `viz.css`, `utilities.css`, `print.css`, `syntyr.css` (core + effects), `all.css`, and the opt-in **Tailwind v4 build-time** bridge `tailwind.css` and scoped shadcn semantic bridge `shadcn.css`. These exports are tested against the standard-library `scripts/build.py` distribution registry. Future CSS modules must update the exports and their contract test.

The default import is deliberately `core.css`; `all.css` is opt-in. Do not import `all.css` alongside its component stylesheets or import `syntyr.css` alongside `core.css` and `effects.css`: doing so duplicates CSS and can complicate cascade debugging.

## Release safety

- **No package publication is performed by the repository build.** Publishing is a separate release-owner action.
- The `VERSION` and `package.json` version must match. Tagged alpha.4 CDN assets remain immutable.
- npm package file inclusion is restricted to the generated `dist/` folder, the optional `integrations/tailwind/` and `integrations/shadcn/` CSS bridges, `README.md` and `LICENSE` (plus npm's required package metadata). It excludes business notes, local configuration, unpublished premium designs and tests.
- CSS exports and the published asset set are checked in the standard Python unit test suite. `npm pack --dry-run --json --ignore-scripts` confirms what the npm client would actually package.
- The package contains no runtime JavaScript and requires no npm lifecycle scripts to install or consume.
- The scoped name and release version must be verified before any publish command is attempted.

Individual CSS component exports (alpha.5 source candidate) are described in [native patterns](native-patterns.md). Load tokens and base before selected components. Do not combine full core with individual component imports.
