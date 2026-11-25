# Syntyr for Shopify: CSS components for storefront themes

**Shopify storefront CSS without a JavaScript widget framework:** Use Syntyr to present campaign information, promotional callouts, comparison sections and branded content inside an Online Store theme. Syntyr supplies the presentation layer while Shopify continues to own products, inventory, cart behavior, checkout and Liquid data rendering.

## Why use Syntyr on Shopify?

Merchants often need an extra section that does not fit their theme's built-in choices. A Syntyr panel gives theme developers reusable CSS tokens, buttons and layouts while keeping editable Shopify section settings. There are no Syntyr runtime scripts or external web fonts to install. This is particularly useful for a small custom promotional section that should retain its own appearance when the main theme changes.

## How to install Syntyr in a Shopify Online Store theme

1. Duplicate the active theme before editing code in **Online Store → Themes**. In the theme code editor, upload the candidate `dist/syntyr.embed.css` into **Assets** as `syntyr.embed.css`.
2. Add the following tag **once** inside the `<head>` of `layout/theme.liquid`. The asset URL is resolved by Shopify.

```liquid
{{ 'syntyr.embed.css' | asset_url | stylesheet_tag }}
```

3. Copy the [Syntyr feature section for Shopify](https://github.com/dporkka/syntyr-css/blob/main/integrations/shopify/sections/syntyr-feature.liquid) into **Sections** as `syntyr-feature.liquid`. It uses Shopify `section.settings` for its heading, descriptive text, button label and URL, with escaped Liquid output.
4. Add **Syntyr feature** to a template in the theme editor, fill in its settings, and inspect the storefront preview on desktop and mobile.

**Example of the section's core content:**

```liquid
<section class="syn-root" data-syn-theme="studio">
  <div class="syn-panel">
    <h2 class="syn-heading">{{ section.settings.heading | escape }}</h2>
    <p class="syn-muted">{{ section.settings.description | escape }}</p>
  </div>
</section>
```

## Limitations and Shopify-specific considerations

This integration is for **Online Store theme markup**, not Shopify checkout. Shopify's Custom CSS boxes have length limits (**1,500 characters theme-wide, 500 per section**) and restrict some CSS features; upload the full stylesheet as a theme asset instead. Existing theme CSS may still beat Syntyr with a higher-specificity selector or `!important`. Syntyr does not supply product grids wired to Shopify APIs or a functioning cart—those remain your theme/application's responsibilities.

**Shopify references:** [Editing theme code](https://help.shopify.com/en/manual/online-store/themes/customizing-themes/edit-code) and [Custom CSS restrictions](https://help.shopify.com/en/manual/online-store/themes/customizing-themes/edit-code/add-css).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
