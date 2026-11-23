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
- An [optional Decap CMS configuration](https://github.com/dporkka/syntyr-css/tree/main/examples/cms-starter/decap/)
  targeting the **same** JSON section types with a pinned 3.18.0 editor
  bundle (admin-only, opt-in; requires external GitHub auth setup).
- A [runnable Hugo adapter](https://github.com/dporkka/syntyr-css/tree/main/examples/hugo-cms/)
  that stages validated JSON and emits Hugo-rendered HTML/CSS under a
  project-subpath deployment without a client runtime.
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

## Optional Decap and Hugo workflow

To use Decap instead of Sveltia, copy `examples/cms-starter/decap/config.yml`
and `index.html` to the **standalone site's** `admin/` directory. Replace
`REPLACE_OWNER/REPLACE_REPO`, configure a GitHub OAuth service as required
by your hosting environment, and route editorial changes through PR review.
Decap does not ship with public pages, and the optional CDN-hosted editor
requires a separately reviewed CSP and asset supply-chain policy. Never
commit authentication secrets.

For Hugo, run `python3 scripts/build_hugo_cms_starter.py --output <output>`
after building local CSS, with the Hugo executable installed. The builder
validates the JSON **before** passing it to Hugo. See the
[Hugo fixture](../examples/hugo-cms/README.md) for custom base URLs and
deployment caveats. The editor must be connected to a Git-to-deploy pipeline;
saving in the CMS alone does not publish changes.
