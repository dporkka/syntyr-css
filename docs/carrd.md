# Syntyr for Carrd: custom CSS for one-page sites

**Carrd HTML and CSS embed customization:** Use Syntyr for a self-contained pricing panel, product comparison or call-to-action section on a Carrd landing page. This approach makes sense when Carrd's native text, container and button elements are insufficient and you want the same styled component across multiple sites.

## Why use Syntyr on Carrd?

Carrd is built for compact landing pages. A CSS-only Syntyr component can add a consistent visual system to a small custom region without adding a large JavaScript widget. You can copy the same HTML and token overrides between a Carrd page and an ordinary static website. That preserves developer control over complex little sections while leaving the editor's existing native elements alone.

## How to install Syntyr in Carrd

1. Check whether your Carrd subscription supports **Embed** elements and custom HTML. The free plan should not be assumed to support these features.
2. Host the alpha.5 candidate `syntyr.embed.css` on an HTTPS origin you control. In an allowed custom-code Embed positioned in the document **Head**, load that asset:

```html
<link rel="stylesheet" href="https://YOUR-ASSET-HOST.example/syntyr.embed.css">
```

3. Add an inline, **visible Embed** element where your custom feature should appear. Use normal HTML instead of trying to apply Syntyr classes to Carrd's generated native element markup:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="carrd-pricing">
  <div class="syn-panel">
    <h2 id="carrd-pricing" class="syn-heading">Simple pricing</h2>
    <p class="syn-muted">A clear product offer on a Carrd page.</p>
    <a href="#contact" class="syn-button syn-button--primary">Get in touch</a>
  </div>
</section>
```

4. Publish the site, verify the embedded markup really renders inline, and check the component's width on a narrow mobile device.

## Limitations and Carrd-specific considerations

Not every Carrd subscription exposes custom HTML or advanced attributes. The Head Embed is intended for non-visible resource code, whereas your section must live in a **visible inline embed**. Syntyr does not turn a Carrd site into a CMS or ecommerce checkout. It is not intended to restyle all of Carrd's built-in elements, and a template update could change their generated class names.

**Carrd reference:** [Carrd's website builder and plan details](https://carrd.co/).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
