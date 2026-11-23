# Framework-independent CMS integration

**Status:** optional MIT Syntyr starter for the **unreleased alpha.5 source
candidate**. It does not install a CMS into the core library or claim that the
public alpha.4 release contains these examples.

Syntyr stays the HTML/CSS presentation layer; Git-backed content is plain,
portable JSON. The [CMS starter](https://github.com/dporkka/syntyr-css/blob/main/examples/cms-starter/README.md) provides:

- A validated [content contract](https://github.com/dporkka/syntyr-css/blob/main/examples/cms-starter/blocks.schema.json)
  covering Hero, Features, Pricing, FAQ and CTA blocks.
- A [Sveltia CMS editor](https://github.com/dporkka/syntyr-css/blob/main/examples/cms-starter/admin/config.yml) with GitHub
  editorial pull-request workflow.
- An alternative [Pages CMS config](https://github.com/dporkka/syntyr-css/blob/main/examples/cms-starter/.pages.yml) with
  repeatable typed blocks editing the very same JSON file.
- A [Python standard-library static renderer](https://github.com/dporkka/syntyr-css/blob/main/scripts/render_cms_starter.py)
  that emits accessible HTML, escapes user content, validates URLs and ships
  no JavaScript in the site pages.

Use Sveltia for an easily hosted Git-based content interface. Choose Pages CMS
when your priority is editing assembled landing-page sections. Both operate
as **optional editors**; a simple Git checkout, a static generator, or a
custom server can read the same content without either CMS running.

Start from [the full setup and deployment instructions](https://github.com/dporkka/syntyr-css/blob/main/examples/cms-starter/README.md).
Production constraints: GitHub credentials and the optional Sveltia OAuth Worker
are external integrations, the editors are not covered by Syntyr's existing
strict Cloudflare documentation CSP, and Git content edits need an independent
build/deploy hook. Do not publish Syntyr's repository root, private files, or
unreviewed editor config as a static site.

A Directus/database-backed adapter may become a separate, optional commercial
example later. It is intentionally **not** included in this low-maintenance
starter: that would add a service, database, permissions and operational upkeep
to a problem solvable with Git and static files.

Blocks require unique stable lowercase `id` slugs; reordering sections does not change link targets. The first section must be a hero; later hero blocks use level-two headings.

## Keystatic and Payload adapters (optional)

Two additional build-time adapters can produce the **same portable v1 JSON**
as the Git-backed Sveltia and Pages CMS starter:

- [Keystatic singleton + schema](https://github.com/dporkka/syntyr-css/tree/main/examples/cms-keystatic):
  a local, typed `fields.blocks` editor that saves `discriminant/value`
  sections; the export converts them to Syntyr's portable section schema.
  Keystatic itself needs a separately configured Astro/Next editor host.
- [Payload 3 blocks](https://github.com/dporkka/syntyr-css/tree/main/examples/cms-payload):
  a typed, optional `GlobalConfig` factory with five block definitions.
  An authorized, build-time export drops **known database metadata** and maps
  `blockType/sectionId` to `type/id`, including nested pricing benefits.

Run the **standard-library** exporter from the repository root:

```sh
python3 scripts/export_cms_adapter.py keystatic --input examples/cms-keystatic/content/pages/home.json --output /tmp/home-keystatic.json
python3 scripts/export_cms_adapter.py payload --input examples/cms-payload/fixtures/home-document.json --output /tmp/home-payload.json
```

Both outputs are structurally identical to
`examples/cms-starter/content/pages/home.json`. Conversion rejects unsafe
URLs, unknown block types, nonportable fields and duplicate section IDs,
and writes atomically only after validation. The editor host or publishing
workflow must implement authentication, authorization, approval and deployment;
the exporter does not make CMS content production-approved.
