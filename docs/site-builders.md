# Use Syntyr with WordPress, Wix, Shopify, Webflow, Framer and other platforms

Syntyr styles **your own HTML**, without JavaScript, build tooling, framework
dependencies, plugins or proprietary APIs. It does **not** automatically reskin
native CMS widgets, checkout, platform data services or their editor interfaces.

## Platform-by-platform setup guides

Each guide covers benefits for that platform, installation steps, real HTML
examples, limitations, and checks for the published site. These are portable
CSS recipes, **not** official platform plugins, partnerships or end-to-end
certification for every platform account.

- [Syntyr for WordPress](wordpress.md) — Gutenberg and child themes
- [Syntyr for Shopify](shopify.md) — Liquid sections and storefront assets
- [Syntyr for Wix / Wix Studio](wix.md) — HTML iframe embeds
- [Syntyr for Webflow](webflow.md) — Code Embed and custom Head CSS
- [Syntyr for Framer](framer.md) — Custom Code and iframe-aware embeds
- [Syntyr for Squarespace](squarespace.md) — plan-aware HTML Code Blocks
- [Syntyr for Ghost](ghost.md) — HTML cards and editorial themes
- [Syntyr for HubSpot CMS](hubspot.md) — custom modules and landing pages
- [Syntyr for Drupal](drupal.md) — theme libraries and Twig
- [Syntyr for Joomla](joomla.md) — custom site templates and modules
- [Syntyr for Carrd](carrd.md) — one-page custom HTML sections
- [Syntyr for Duda](duda.md) — HTML Widgets for agency sites
- [Syntyr for Tilda](tilda.md) — T123 HTML blocks and Head code

## Pick the correct CSS

Use `syntyr.core.css` for a site that Syntyr owns. For a Syntyr feature inside
an existing site or CMS theme, use `syntyr.embed.css` from the **unreleased
alpha.5 source candidate**. It contains the same core tokens and components
but removes their outer CSS cascade layers. A typical unlayered theme declaration
otherwise overrides *all* normal layered rules, regardless of specificity.
The embed CSS remains scoped to the `syn-root` class. It does not guarantee
victory over more specific host selectors or `!important`, and it does not
inject CSS across iframe boundaries.

**Release boundary:** `syntyr.embed.css` is not in the published immutable
alpha.4 release; build it locally using `python3 scripts/build.py` and self-host
`dist/syntyr.embed.css` for alpha.5 development. Do not invent an alpha.5 CDN
URL. For production today, alpha.4 `syntyr.core.css` is published, but its
layered cascade needs validation against each host theme. Do **not** load both
core and embed stylesheets together.

Load the stylesheet once in your page's `<head>`:

```html
<link rel="stylesheet" href="/assets/syntyr.embed.css">
```

Then place this content in a platform-provided **visible HTML** block or theme
template (not in a head-code field):

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="syntyr-title">
  <div class="syn-panel">
    <h2 class="syn-heading" id="syntyr-title">Our services</h2>
    <p class="syn-muted">A self-contained, accessible feature.</p>
    <a href="/services" class="syn-button syn-button--primary">Explore</a>
  </div>
</section>
```

Keep `syn-root` on the *component wrapper*, not the site's `<body>`. Do not
apply the optional `syn-semantic` class to the whole CMS document or use
`syn-page` unless a full-height page is intended. Replace the sample URL with
your own site paths. For production, prefer a **self-hosted, immutable versioned
asset** over an unversioned CDN.

## Installation matrix

| Platform | Load CSS | Place visible HTML | Important boundary |
| --- | --- | --- | --- |
| **WordPress** (self-hosted/theme access) | Enqueue CSS in child theme or site plugin | Gutenberg Custom HTML, template or custom block | HTML may be sanitized by role; CSS is not automatically loaded by an HTML block |
| **Shopify** Online Store | Theme Assets + one Liquid stylesheet tag | Section, Custom Liquid or template | Storefront theme only; not checkout |
| **Wix / Wix Studio** | Inside HTML embed iframe | Embed HTML element or custom element | Dashboard Custom Code cannot reliably style managed Wix elements |
| **Webflow** | Site/Page Settings > Custom Code > Head | Designer Code Embed | Custom-code plan permissions and publishing apply |
| **Framer** | Project Settings > Custom Code > head | Embed component or supported HTML | If embed is an iframe, stylesheet must load inside it |
| **Squarespace** | Permitted Code Injection/Custom CSS | Code Block | Plan/security restrictions; CSS editor is intended for limited tweaks |
| **Ghost** | Code Injection header or theme CSS | HTML card or theme template | Site-owned markup only |
| **HubSpot CMS** | Theme / page / custom module stylesheet | Custom module/template | CMS policy and custom-code privileges |
| **Drupal / Joomla** | Theme library or template stylesheet | Custom block/template/module | Prefer theme-managed assets |
| **Carrd / Duda / Tilda / other builders** | Head code or iframe HTML when supported | Custom HTML/embed | Unavailable when custom HTML/CSS is prohibited |

### WordPress

Copy the alpha.5 build's CSS into a child theme at
`assets/syntyr.embed.css`, then adapt
[the WordPress enqueue example](https://github.com/dporkka/syntyr-css/blob/main/integrations/wordpress/syntyr-enqueue.php)
into the child theme's `functions.php` or a site-specific plugin. Add the
example `<section>` through a Custom HTML block. Do not assume a
`<link>` tag pasted into a post will be preserved; permissions determine
HTML sanitization. On block themes, Additional CSS may be available
through Site Editor > Styles, but is less convenient for a full distribution.
WordPress.com and managed hosts can restrict theme access and custom code.

### Shopify

Copy the CSS to theme `assets/syntyr.embed.css`, then load once in
`layout/theme.liquid` inside `<head>`:

```liquid
{{ 'syntyr.embed.css' | asset_url | stylesheet_tag }}
```

Copy [the Shopify feature section](https://github.com/dporkka/syntyr-css/blob/main/integrations/shopify/sections/syntyr-feature.liquid)
into theme **Sections** and insert “Syntyr feature” in the theme editor.
The sample uses editable text, URL settings, and HTML-escaped outputs.
This targets **Online Store themes**, not checkout extensions. Avoid
pasting the CSS into Shopify's Custom CSS field: its 1,500-character
theme-wide and 500-character section limits, as well as forbidden at-rules,
make it unsuitable for a complete CSS distribution.

### Wix / Wix Studio

For a visible standalone feature, add an **Embed HTML** element; this is
an iframe. Paste a complete iframe document containing the stylesheet link
and Syntyr `<section>`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://YOUR-HOST.example/syntyr.embed.css">
</head>
<body>
  <section class="syn-root" data-syn-theme="studio">
    <div class="syn-panel"><h2 class="syn-heading">Hello from Syntyr</h2></div>
  </section>
</body>
</html>
```

Use your own HTTPS-hosted stylesheet, and size the embed so its contents
aren't clipped. Styling in the parent Wix document cannot reach into
the iframe. Wix dashboard Custom Code is not the same as Velo/site code:
it cannot access Wix APIs and must not rely on Wix-generated classes or
page DOM nodes remaining stable. Custom elements and Velo can provide deeper
integrations but are optional and platform-specific.

### Webflow

Add the link tag to **Site Settings > Custom Code > Head** or page-level
Head, then insert the feature markup using a **Code Embed**. Publish the
site to confirm behavior. Embedded code and CSS may conflict with the native
Designer, and custom-code permissions vary by plan.

### Framer

Add the link tag to **Project Settings > Custom Code**, placed in the
head, and insert the feature markup using a supported Embed or code component.
An isolated iframe needs the stylesheet **inside its own document**.
Verify the published URL rather than assuming the editor canvas reflects
external code.

### Other builders

Squarespace Code Blocks, Ghost HTML cards, HubSpot CMS custom modules,
Drupal/Joomla theme templates, and other builders can use the same
asset + `syn-root` recipe when they allow both CSS and custom HTML.
If only an iframe is supported, host an HTML page that links Syntyr inside
the frame. If a platform forbids custom CSS or visible HTML, do not target
private generated classes: native widgets are **not compatible by default**.

## Verify on the published site

1. Verify the CSS URL succeeds, is served as CSS and matches the installed version.
2. Compare native site buttons/cards outside `syn-root` before and after.
3. Test the Syntyr feature at 320px, with keyboard navigation, reduced motion,
   forced colors, and the host theme's global typography/forms rules.
4. For an iframe, check sizing, accessibility, asset origin, CSP and sandboxing.
5. Host theme CSS with higher specificity/`!important` may still need a local,
   narrowly scoped override; the embed distribution addresses **cascade-layer
   precedence**, not every possible site builder rule.
6. Recheck after builder or theme updates; no provider account integration
   has been end-to-end verified by this source-only compatibility suite.

See [the static host-theme fixture](../examples/platform-embed.html)
for an offline, zero-JavaScript example with a host button outside Syntyr.

### Official platform references

- WordPress: https://wordpress.org/documentation/article/custom-html/
- Shopify CSS restrictions: https://help.shopify.com/en/manual/online-store/themes/customizing-themes/edit-code/add-css
- Shopify theme asset tags: https://shopify.dev/docs/storefronts/themes/best-practices/javascript-and-stylesheet-tags
- Wix code boundaries: https://dev.wix.com/docs/overview/site-features-tools/about-custom-code
- Wix embed: https://support.wix.com/en/article/wix-editor-about-embeds-and-codes-on-your-site
- Webflow custom code: https://help.webflow.com/hc/en-us/articles/33961357265299-Custom-code-in-head-and-body-tags
- Framer custom code: https://www.framer.com/help/articles/how-to-add-custom-code/
- Squarespace: https://support.squarespace.com/hc/en-us/articles/206545567-Add-custom-CSS-to-your-site
