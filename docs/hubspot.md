# Syntyr for HubSpot CMS: CSS for custom modules and pages

**HubSpot CMS design components:** Use Syntyr in a custom HubSpot CMS module, coded template or selected landing-page region. This works well for lead-generation panels, agency campaign components and product comparisons where content marketers need fields they can edit while developers own the HTML and CSS.

## Why use Syntyr on HubSpot CMS?

HubSpot CMS modules already provide fields and template rendering through HubL. A Syntyr component can style that generated HTML without requiring a React bundle or external component runtime. The CSS namespace keeps the new module separate from unrelated HubSpot forms and theme styling. Developers can retain reusable, MIT-licensed design primitives in source control and still let a marketer change the displayed heading or call to action in the HubSpot page editor.

## How to install Syntyr in HubSpot CMS

1. In **Design Manager**, create or open a custom coded module with fields for a heading, body copy and optional CTA link. Keep existing HubSpot module authoring and permission conventions.
2. Upload a pinned `syntyr.embed.css` candidate asset and attach the stylesheet to the relevant **template, page or module**. HubSpot also supports attaching a stylesheet from a page's advanced settings; avoid loading it site-wide when only one module needs it.
3. In the module's HTML/HubL template, render a `syn-root` wrapper and escape field content as appropriate for its context. For example, a static markup scaffold is:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="hs-heading">
  <div class="syn-panel">
    <h2 class="syn-heading" id="hs-heading">Talk to our team</h2>
    <p class="syn-muted">A styled HubSpot campaign module.</p>
    <a class="syn-button syn-button--primary" href="/contact">Contact sales</a>
  </div>
</section>
```

4. Connect your own module fields via HubL, preview, then publish and confirm the linked CSS asset resolves correctly.

## Limitations and HubSpot-specific considerations

Syntyr does not provide the HubSpot Form API, CRM integration, personalization, analytics tracking or native module fields. Those remain HubSpot features. Page, module and domain stylesheet attachments have a defined cascade and **some domain-level settings require higher subscription plans or permissions**. Prefer local module CSS when feasible, and never assume a stylesheet attached to an unrelated page is inherited elsewhere.

**HubSpot references:** [Create and attach CSS files](https://knowledge.hubspot.com/design-manager/create-edit-and-attach-css-files-to-style-your-site) and [Understanding page styling](https://knowledge.hubspot.com/design-manager/understand-the-source-of-a-page-s-styling).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
