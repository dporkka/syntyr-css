# Syntyr for Wix and Wix Studio: embedded CSS components

**Wix custom HTML styling:** Add a self-contained Syntyr feature to a Wix Editor or Wix Studio website through an HTML embed. Use it for branded lead magnets, comparison panels, resource listings or a custom information card that Wix's native builder does not readily produce. The reliable integration boundary is an iframe, not Wix's internal DOM.

## Why use Syntyr on Wix?

An HTML embed lets the custom widget keep its own CSS rules without changing the live Wix layout or relying on Wix-generated class names. The widget can use real buttons, links, headings and `details` disclosures with no Syntyr JavaScript runtime. This gives developers a reusable custom design layer while content editors continue to work with Wix's page and commerce features outside that embed.

## How to install Syntyr in a Wix HTML embed

1. Build the candidate stylesheet and host `syntyr.embed.css` at a stable **HTTPS** URL you control. An externally hosted CSS file must be reachable from inside the embed's document.
2. In Wix Studio, choose **Add Elements → Embed & Social → Embed Code**, or use the corresponding HTML embed element in Wix Editor.
3. Paste a complete small HTML document like this, replacing `YOUR-ASSET-HOST`, then apply the changes.

```html
<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://YOUR-ASSET-HOST.example/syntyr.embed.css">
</head>
<body>
  <section class="syn-root" data-syn-theme="studio">
    <div class="syn-panel">
      <h2 class="syn-heading">Our services</h2>
      <p class="syn-muted">A self-contained Wix feature.</p>
      <a class="syn-button syn-button--primary" href="/contact">Contact us</a>
    </div>
  </section>
</body>
</html>
```

4. Resize the iframe's element so text is not clipped, and check its mobile layout in the published Wix site.

## Limitations and Wix-specific considerations

A Wix **dashboard Custom Code** snippet is not a visible HTML embed; it cannot reliably style Wix-managed elements. The Syntyr stylesheet loaded in the parent page cannot pass through an iframe boundary. Relative link navigation may need adjustment to the site's actual domain or `target` behavior. If an embed must interact with Wix datasets or user state, that requires separate Wix APIs, custom elements or Velo code—CSS alone cannot supply it.

**Wix references:** [Studio HTML iframe instructions](https://support.wix.com/en/article/studio-editor-adding-an-html-iframe-element) and [dashboard Custom Code behavior](https://support.wix.com/en/article/wix-editor-embedding-custom-code-on-your-site).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
