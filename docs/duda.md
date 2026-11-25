# Syntyr for Duda: HTML widget styling for agency sites

**Duda website HTML widget CSS:** Add Syntyr to a Duda site when an agency needs a branded offer panel, resource callout or consistent cross-client component. The integration uses the site's supported HTML Widget for visible content, with the stylesheet loaded through an allowed Head code field.

## Why use Syntyr on Duda?

Duda agencies often reuse elements across several client websites. Syntyr's source-owned CSS classes and design tokens let developers keep a familiar component contract without replacing Duda's design editor or copying a complete JavaScript framework into each website. A scoped `syn-root` prevents intentional Syntyr selectors from targeting the rest of the client's navigation or existing widgets.

## How to install Syntyr in Duda

1. Back up or duplicate the site before working with code. Build the candidate `syntyr.embed.css` and host it at an HTTPS URL; Duda's editor rejects insecure external asset references.
2. Open the site's **Settings → Header HTML** or a supported page-specific Head code field and load the stylesheet once:

```html
<link rel="stylesheet" href="https://YOUR-ASSET-HOST.example/syntyr.embed.css">
```

3. In the side panel, select **Add → Elements**, locate the **HTML Widget**, and drop it into a row or column on the target page. Edit the widget's content to insert:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="duda-offer">
  <div class="syn-panel">
    <h2 id="duda-offer" class="syn-heading">Agency services</h2>
    <p class="syn-muted">A portable offer card for your client site.</p>
    <a class="syn-button syn-button--primary" href="/contact">Request a quote</a>
  </div>
</section>
```

4. Publish the site and verify it in the visitor-facing view, not solely within the editor's design preview.

## Limitations and Duda-specific considerations

The **HTML Widget** is appropriate for visible HTML, whereas **Header HTML** is for asset links and other head metadata. Developer Mode is plan-dependent and is not required for this basic widget workflow. The platform does not execute arbitrary PHP in the widget, and custom code is outside normal Duda support. Syntyr does not automatically connect Duda dynamic content, forms or client data. Use the host's existing data bindings and permissions when those features matter.

**Duda references:** [HTML Widget](https://support.duda.co/hc/en-us/articles/26519240974487-Widgets-HTML) and [Custom Code locations](https://support.duda.co/hc/en-us/articles/26519250445079-Custom-Code).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
