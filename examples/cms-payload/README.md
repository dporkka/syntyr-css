# Syntyr + Payload CMS 3 (optional blocks for an existing application)

This integration supplies **typed Payload block definitions** plus a
**build-time converter** to Syntyr's existing portable v1 JSON format.
It is **not** a deployable Payload application: a real site must supply
authentication, database and transport security, and a controlled publishing
pipeline. Nothing is added to the Syntyr CSS core's dependencies.

The Payload Global uses the same five section types as the Git-backed editor
examples: `hero`, `features`, `pricing`, `faq`, `cta`.

## Configure Payload in the host application

Install Payload 3.94.1 in your own app, and import the helper:

```ts
import { createSyntyrHomepageGlobal } from './SyntyrHomepage';

const syntyrHome = createSyntyrHomepageGlobal({
  read: ({ req }) => Boolean(req.user),
  update: ({ req }) => Boolean(req.user),
});

// Add syntyrHome to globals in your existing Payload config.
```

The sample access policy above only illustrates a **login requirement**.
Replace it with an appropriate role-/tenant-aware authorization check; in
particular, not every authenticated user should have publishing permissions.
The helper throws if you omit read/update policies.

Payload stores each block under `blockType`, adds persistence row IDs, and
uses a `sectionId` field for Syntyr's **stable** anchor slug. Do not confuse
`sectionId` with Payload's internally generated `id`. Nested rows also carry
internal IDs, and pricing benefits use `{feature: '...'}` row objects.

## Exporting content

Fetch the Global **server-side** through your application's authenticated
Payload Local API or another authorized export job. Save the result to a
build-only JSON file (for example `/tmp/payload-home.json`). Never publish
admin API secrets or raw internal documents to a public assets bucket.

```sh
python3 scripts/export_cms_adapter.py payload \
  --input examples/cms-payload/fixtures/home-document.json \
  --output /tmp/syntyr-home.json
```

The converter strips only the allowlisted Payload metadata and checks all
other data against Syntyr's existing strict CMS validator. Unsupported block
types, unknown properties, unsafe URLs, invalid IDs and duplicate anchors
abort the build **without replacing** the existing output.

Place the **validated** JSON into your website's static build source, then
render with Syntyr HTML templates and locally hosted CSS. This does not deploy
or operate a server-side Payload application for you.

To type-check the optional block factory:

```sh
cd examples/cms-payload
npm install
npm run typecheck
npm run smoke   # imports the real block config and checks its access guard
```

`npm run export:fixture` writes a test export to `_portable/home.json`,
never overwriting the canonical Git-backed CMS document.

## Operational boundary

- Do not expose the Payload Global's updates to anonymous visitors.
- Prefer a reviewed publishing/build job over live API calls from a static page.
- Keep private/draft content separate; the converter validates structure, **not**
  whether a document has editorial approval.
- Payload, its admin JavaScript, and its database remain optional and separate
  from the CSS-only Syntyr distribution.
