# Syntyr for Joomla: CSS components inside site templates

**Joomla template customization with Syntyr:** Add scoped CSS components to a Joomla front-end template, child template or custom module output. Syntyr is useful for directory summaries, product-service cards and campaign callouts that need a more refined interface without changing Joomla's installed extensions or its administration template.

## Why use Syntyr on Joomla?

Joomla already separates a site's public template from its CMS content and extension logic. Syntyr can be added as an independent stylesheet and used only on specific module or article regions. Designers get token-based styling and native HTML patterns, while developers retain the ability to edit the component in template source. No Syntyr JavaScript runtime, frontend build process or proprietary editor plugin is required.

## How to install Syntyr in a Joomla template

1. Work in a custom or **child site template**, not in an unmodified core template that an update could replace. Copy the candidate `dist/syntyr.embed.css` into the template's static CSS directory.
2. Register **and activate** the stylesheet using Joomla's **Web Asset Manager**. Registering a style in the template's `joomla.asset.json` only makes the asset known to Joomla; it does **not** load the CSS until you mark it as used. For example, after registering the style under the name `syntyr.embed`, call the following from your site template's PHP rendering code:

```php
<?php
$wa = $this->getWebAssetManager();
$wa->useStyle('syntyr.embed'); // The name must match the registered style asset.
?>
```

   Alternatively, if your template does not use an asset JSON declaration, Joomla supports `$wa->registerAndUseStyle('syntyr.embed', 'YOUR-ASSET-URI.css')` to register and enable the style in one call. Replace the URI with the correct template asset URI for your Joomla installation. Confirm the stylesheet `<link>` is emitted on the rendered page; simply registering a file is insufficient.
3. Insert a Syntyr component in a custom module or template override that outputs permitted HTML:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="jm-services">
  <div class="syn-panel">
    <h2 id="jm-services" class="syn-heading">Service directory</h2>
    <p class="syn-muted">A reusable callout in the Joomla site template.</p>
    <a class="syn-button syn-button--primary" href="/services">Find a service</a>
  </div>
</section>
```

4. Verify the stylesheet order and HTML output on the public site, then compare with the active template's module and menu styling.

## Limitations and Joomla-specific considerations

Joomla's visual article editors may sanitize custom markup according to filtering and role settings. Styling a custom module does not automatically style third-party extensions, forms or ecommerce flows. If your template generates additional styles after Syntyr, a more specific rule may win; use a wrapper-scoped override rather than adding platform-internal CSS to Syntyr itself. Administrative styling is a separate template concern.

**Joomla references:** [Web Asset Manager: registering versus using styles](https://manual.joomla.org/docs/5.4/general-concepts/web-asset-manager/) and [official extension and template development overview](https://manual.joomla.org/docs/next/building-extensions/).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
