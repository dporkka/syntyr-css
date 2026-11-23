# Syntyr + Keystatic (optional editor schema)

This is a **drop-in Keystatic configuration**, not an independently deployed
CMS server. Add it to an existing Astro or Next.js application where Keystatic
has been installed and configured. It does not change the `@syntyr/css`
runtime or the public Syntyr website.

Keystatic's `fields.blocks` representation wraps each section as
`{ "discriminant": "hero", "value": { ... } }`. This example stores
`content/pages/home.json` in that editor-native format and exports the
**existing** portable contract shared by Syntyr's Git-backed CMS starter.

## Editor setup

1. In your own Astro project install `@keystatic/core@0.6.10`,
   `@keystatic/astro@6.0.0`, plus Astro's React integration. Follow the
   [official Keystatic Astro setup](https://keystatic.com/docs/installation-astro).
2. Copy `keystatic.config.ts` to that project's root and place
   `content/pages/home.json` relative to the editor project root.
3. Register `keystatic()` in the project's Astro integrations and start
   **local development** to edit the homepage singleton.
4. In Syntyr's repository, validate the export with:

   ```sh
   python3 scripts/export_cms_adapter.py keystatic \
     --input examples/cms-keystatic/content/pages/home.json \
     --output /tmp/syntyr-home.json
   ```

   For a standalone site, copy the exporter and the Syntyr portable CMS
   renderer into your **build process**, adapting paths as needed.
   Keep `home.json` out of a publicly writable asset directory.
5. Render the validated `/tmp/syntyr-home.json` with your preferred
   static-site templates, or use the existing Syntyr Python renderer by
   writing a copy to your **site's source** `content/pages/home.json`
   before invoking the renderer. Commit editor changes and build in CI.

To validate the configuration's types without installing Keystatic in the
Syntyr root:

```sh
cd examples/cms-keystatic
npm install
npm run typecheck
npm run smoke   # reads actual JSON with the real Keystatic Reader API
```

`npm run export` writes to `_portable/home.json` in this optional example
directory; it intentionally does not overwrite the canonical CMS starter.

## Deployment / security

The checked-in configuration is **local editor storage only**. It does not
install GitHub OAuth, a public admin UI, or a hosted CMS. Do not deploy the
Keystatic editor onto a public production site without configuring appropriate
authentication, authorization, and hosting routes. The published page can
remain static HTML/CSS with no Keystatic client JavaScript.

This adapter shares the existing **v1 Hero, Features, Pricing, FAQ and CTA**
shape. Stable section IDs and the first-hero rule are checked at export time.
Do not accept raw HTML blocks or bypass the export validator.
