# Syntyr for Framer: reusable CSS components in embeds

**Framer site customization with plain CSS:** Embed Syntyr-styled pricing callouts, feature comparisons or lightweight technical content on a Framer site using the project's Custom Code settings and an HTML-capable Embed component. Prefer the built-in Framer elements for ordinary page structure; use Syntyr when you specifically need portable, source-owned HTML.

## Why use Syntyr on Framer?

The benefit is portability: a Syntyr component depends on its markup and stylesheet, not on a particular Framer component or generated CSS selector. It can reuse the same Studio/Grid/Noir token system as a separately hosted product site. A static Syntyr component uses no JavaScript runtime of its own and can be modified in source control independently of Framer.

## How to install Syntyr in Framer

1. Publish a versioned `syntyr.embed.css` asset to an HTTPS origin. In **Project Settings → Custom Code**, use the project's **Head** placement to load the stylesheet for site-owned markup.
2. Insert an **Embed** component where you want custom content. For an HTML-capable embed, paste Syntyr markup:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="framer-demo">
  <div class="syn-panel">
    <h2 id="framer-demo" class="syn-heading">Launch-ready design</h2>
    <p class="syn-muted">A source-owned section for your Framer page.</p>
    <a class="syn-button syn-button--primary" href="/features">Explore features</a>
  </div>
</section>
```

3. **Check the embed's document boundary.** If Framer renders it inside an iframe, the parent Head link cannot style it. In that case embed a full HTML document with its **own** stylesheet link, or host the component as an HTTPS page and embed its URL.
4. Publish and test the page at representative desktop and mobile widths.

## Limitations and Framer-specific considerations

Framer's Embed and Custom Code features serve different paths. Embedding another URL can be blocked by the destination's `frame-ancestors`/X-Frame-Options headers, and it adds frame sizing and accessibility considerations. Syntyr does not integrate with the Framer Canvas, CMS, custom animations or built-in interactions by itself. Use Framer's native controls when those are a better fit.

**Framer references:** [Adding custom code](https://www.framer.com/help/articles/how-to-add-custom-code/) and [Embed/iframe instructions](https://www.framer.com/help/articles/how-to-add-an-iframe-or-embed-script/).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
