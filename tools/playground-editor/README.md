# Syntyr documentation editor (CodeMirror 6)

This isolated tool builds the optional self-hosted CodeMirror 6 HTML editor used
only by `docs/playground.html`. Syntyr's CSS distributions, npm exports and
consuming applications do not import CodeMirror or require Node.

To rebuild the checked-in browser asset and its third-party license notices:

```sh
npm ci --prefix tools/playground-editor
npm run build --prefix tools/playground-editor
python3 tools/playground-editor/build_licenses.py
```

The lockfile pins the complete build graph; source is
`tools/playground-editor/src/editor.mjs`. Commit changes to the bundle,
notices and lockfile together. The public Cloudflare publisher has a strict
allowlist for the two generated documentation assets.

The editor synchronizes edits back to the native `#playground-markup`
textarea, which the existing controller uses for live preview and copy.
Catalog changes send `syntyr:load-example` to update CodeMirror. The
original textarea remains visible if CodeMirror cannot initialize or if
JavaScript is disabled; no network CDN or runtime package manager is needed.

The preview iframe retains `sandbox="allow-same-origin"` **without**
`allow-scripts`, and its CSP blocks script execution and form submission.
