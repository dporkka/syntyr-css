# Syntyr for Squarespace: custom CSS and HTML blocks

**Squarespace CSS components for custom sections:** Syntyr can style ordinary HTML in a Squarespace Code Block where supported. Use it for a service comparison, event promotion or portfolio callout that needs a visual style distinct from your template. Keep Squarespace's native sections for layouts its editor already handles well.

## Why use Syntyr on Squarespace?

A Syntyr-styled region can be copied between sites and edited as semantic HTML without importing a JavaScript widget framework. Color, spacing and typography are controlled through CSS tokens, giving agencies a way to create consistent small features without rewriting an entire Squarespace theme. A lightweight static section does not need Syntyr-specific scripts or external fonts; this is useful when the rest of the page already contains several third-party embeds.

## How to install Syntyr in Squarespace

1. First confirm that your plan permits the necessary custom code facilities. Squarespace supports HTML in **Code Blocks** on all plans; **Code Injection** for a site-wide Head field is available on **Core, Plus, Advanced and some legacy plans**.
2. On a plan with Head Code Injection, add the stylesheet link once. Use a self-hosted candidate build for `syntyr.embed.css`:

```html
<link rel="stylesheet" href="https://YOUR-ASSET-HOST.example/syntyr.embed.css">
```

3. Edit the desired page, add a **Code Block**, choose **HTML** mode (not Display Source), and paste:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="sq-event">
  <div class="syn-panel">
    <h2 id="sq-event" class="syn-heading">Upcoming workshop</h2>
    <p class="syn-muted">A styled event summary on your Squarespace page.</p>
    <a class="syn-button syn-button--primary" href="/events">See events</a>
  </div>
</section>
```

4. Publish and open the site as a visitor. For plans without Code Injection, discuss the allowed CSS editor or an HTML Code Block with your site administrator; do not assume the full bundle can be pasted into any field.

## Limitations and Squarespace-specific considerations

A **Code Block** and **Embed Block** are different; a Code Block renders HTML. The Squarespace CSS editor is primarily intended for limited visual adjustments, and a complete third-party stylesheet is more appropriate as a hosted asset where Head injection is available. JavaScript and iframe support within Code Blocks is plan-dependent. Checkout pages and managed storefront components cannot be restyled by this Syntyr example. Preview/editor modes may suppress custom code, so inspect the public URL.

**Squarespace references:** [Custom code overview](https://support.squarespace.com/hc/en-us/articles/205815928-Add-custom-code-to-your-site), [Code Blocks](https://support.squarespace.com/hc/en-us/articles/206543167-Add-custom-code-to-a-page-with-code-blocks) and [Code Injection](https://support.squarespace.com/hc/en-us/articles/205815908-Customize-parts-of-your-site-with-code-injection).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
