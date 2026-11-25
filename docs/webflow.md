# Syntyr for Webflow: custom CSS components and HTML embeds

**Webflow custom component styling:** Syntyr works with site-owned HTML inserted through Webflow's Code Embed and styled by a separately hosted CSS asset. Use it to build a distinct feature panel, technical product comparison, small design-system element or interactive-looking static layout while leaving your Webflow CMS collections and Designer components intact.

## Why use Syntyr on Webflow?

Webflow's visual Designer is useful for building most page layouts, but teams sometimes need a portable component shared across several projects. Syntyr provides stable `syn-` component names, token-based themes and semantic HTML. The same HTML block can be reused outside Webflow without exporting your whole site. No Syntyr client-side runtime is required, although your existing Webflow site may use scripts.

## How to install Syntyr in Webflow

1. Self-host the candidate `syntyr.embed.css` at a versioned HTTPS asset URL or another approved asset endpoint.
2. In **Site settings → Custom code → Head**, add a single stylesheet link. Alternatively, use the page-level custom Head field if only one page needs the bundle. Save and publish.

```html
<link rel="stylesheet" href="https://YOUR-ASSET-HOST.example/syntyr.embed.css">
```

3. In Webflow Designer, add a **Code Embed** element where the feature belongs. Paste ordinary content markup—**not** an entire HTML page:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="wf-offer">
  <div class="syn-panel">
    <h2 class="syn-heading" id="wf-offer">Compare plans</h2>
    <p class="syn-muted">Use a portable component alongside Webflow sections.</p>
    <a class="syn-button syn-button--primary" href="/plans">View plans</a>
  </div>
</section>
```

4. Check the published Webflow page and verify the stylesheet appears in its Network panel.

## Limitations and Webflow-specific considerations

Custom code availability depends on the Webflow **Site/Workspace plan and permissions**. Head custom code and Code Embed serve different purposes. Do not place `<html>`, `<head>` or `<body>` inside a Code Embed; and do not depend on Webflow's generated internal class names. CMS collection data, forms, animations and Ecommerce interactions still need Webflow's own features or independently developed logic.

**Webflow reference:** [Custom code in head and body](https://help.webflow.com/hc/en-us/articles/33961357265299-Custom-code-in-head-and-body-tags).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
