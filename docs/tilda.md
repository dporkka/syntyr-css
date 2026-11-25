# Syntyr for Tilda: HTML embeds and CSS for landing pages

**Tilda custom HTML styling:** Use Syntyr inside a Tilda T123 HTML block or a supported Zero Block HTML element to create a distinctive feature panel, service summary or reusable product callout. The Syntyr bundle styles its own HTML and does not replace Tilda's built-in blocks, animations or site publishing process.

## Why use Syntyr on Tilda?

Tilda's block-oriented editor is convenient for landing pages, but custom sections are sometimes easier to maintain as portable markup. A Syntyr feature can be shared with other sites and updated using the same CSS tokens. Its native HTML patterns also avoid a separate UI framework just to render buttons, headings, lists and disclosures. You still get to use Tilda's native layout for the rest of the page.

## How to install Syntyr in Tilda

1. Generate the alpha.5 candidate `syntyr.embed.css` and host it over HTTPS at a stable URL. Tilda allows code in the Head area through **Site Settings → More → HTML code for the head section**, or a page-level **Page Settings → Additional → HTML code for the head section**.
2. Load the stylesheet once in the Head code field:

```html
<link rel="stylesheet" href="https://YOUR-ASSET-HOST.example/syntyr.embed.css">
```

3. Open **Block Library → Other → T123 (Embed HTML Code)**, then paste the HTML for a Syntyr feature:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="tilda-feature">
  <div class="syn-panel">
    <h2 id="tilda-feature" class="syn-heading">What's included</h2>
    <p class="syn-muted">A custom product summary styled with Syntyr.</p>
    <a class="syn-button syn-button--primary" href="#contact">Learn more</a>
  </div>
</section>
```

4. Publish the page before judging visual results. Tilda may display custom code as text only while editing, rather than rendering it in the editor.

## Limitations and Tilda-specific considerations

Tilda's own blocks and Zero Block interactions remain outside Syntyr's control. The T123 code feature should not be treated as a backend: PHP or server-side application behavior needs a separate hosted service. Respect editor restrictions and the site's Content Security Policy. If the platform changes its embedded-code rendering rules, re-test your code. Using an inline custom HTML block is not the same as styling Tilda's existing native blocks.

**Tilda reference:** [Official T123 and HTML embed instructions](https://www.help.tilda.cc/html).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
