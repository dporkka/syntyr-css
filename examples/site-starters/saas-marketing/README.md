# Waypoint — Syntyr CSS SaaS marketing starter

An original, **three-page**, static, framework-neutral marketing-site starter
inspired by the reusable-section approach used by modern Astro/Hugo themes.
The fictional brand is not a working product.

## Pages and compositions

- `index.html`: split hero and HTML-only dashboard illustration, audience strip,
  three feature cards, workflow steps, split story, native FAQ, and final CTA.
- `pricing/index.html`: responsive pricing cards, disclosure, pre-launch
  checklist, and native pricing FAQ.
- `about/index.html`: mission hero, split approach section, values cards, CTA.
- `assets/site.css`: starter-local layout composition. No public `syn-*`
  selectors or tokens are added to the Syntyr core.

All navigation is local, all layouts are keyboard accessible, and there are no
JavaScript files, webfonts, stock images, trackers, build dependencies or remote
assets. Buttons deliberately link to real local example pages; they do not
pretend to be checkout or lead-capture forms.

## Preview in the Syntyr repository

Open `examples/site-starters/saas-marketing/index.html` via a local static
server rooted at the repository, or use the Cloudflare preview once published:

`https://syntyr-css.pages.dev/examples/site-starters/saas-marketing/`

The source uses a relative link to `dist/syntyr.core.css`. Do not copy the
source folder in isolation without exporting it.

## Export a standalone site

From the repository root:

```sh
python3 scripts/export_site_starter.py --output /tmp/waypoint-static
python3 -m http.server 8000 --directory /tmp/waypoint-static
```

Visit `http://localhost:8000/`. The exporter pins the checked-in core
stylesheet as `assets/syntyr.core.css` and rewrites the page links, so the
exported site works offline without npm, a CDN, or the original repository.
The exporter refuses to overwrite an existing destination.

## Deploy to hosting providers

The reusable, independently deployable site (without publishing the repository
root or affecting the separate SaaS Admin Starter) has [Vercel, Netlify, Render,
Cloudflare Pages, GitHub Pages and static hosting instructions](../../../deploy/saas-marketing/README.md).

```sh
python3 scripts/build_saas_marketing_site.py
python3 scripts/build_saas_marketing_site.py --check
```

## Customize

1. Replace the fictional Waypoint name, product claims, plan prices and metrics.
2. Change `data-syn-theme="studio"` on all pages to another supported theme
   (e.g. `minimal` or `noir` in the unreleased alpha.5 source candidate).
3. Adjust the private `site-*` layout classes and CSS custom properties.
4. Replace navigation targets and add any real policies, consent, and terms.
5. Convert page content into Astro, Hugo, or Eleventy templates if desired;
   no framework adapter is required to render these HTML/CSS patterns.

The core CSS here is the **unreleased alpha.5 source candidate**. Validate
against the published version of Syntyr before distributing a production site.

## Scope

This is a first deployable marketing-site archetype, not a site generator or
CMS integration. It does not implement authentication, billing, analytics,
forms, theme-switcher JavaScript, or dynamic collections.
