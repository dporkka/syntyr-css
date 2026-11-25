# Developer adoption experiment and launch copy (draft)

Not a launch authorization or announcement. Alpha.4 is published; alpha.5, npm and paid kits are not approved for publication. Verify the exact release, name clearance, and public URLs before using this copy. Keep this planning document out of the website and CSS distributions.

## Measurement plan — issue #343

Start with existing aggregate sources before adding instrumentation. No cookies, identifiers, generated code, form values, or third-party tracking should be introduced for this experiment.

| Stage | Metric | Evidence source |
| --- | --- | --- |
| Discovery | Non-branded impressions, clicks and CTR by canonical landing URL | Verified Search Console property |
| Evaluation | Aggregate visits to docs and starter wizard | Approved site analytics, if available |
| Install intent | Release asset downloads and pinned CSS requests, separately | GitHub release asset counts; approved aggregate CDN logs |
| Actual adoption | Confirmed integration into a real project | Voluntary design-partner feedback |
| Retention | Projects still using Syntyr at 30 days | Consented follow-up |

Do not combine requests, downloads, users or page views as if they were the same unit. Do not infer installation from a CSS request, or attribute downloads to a particular documentation visit without reliable data. Baseline is not yet available. Record weekly counts with dates, collection windows, source and missing-data flags. Only add an optional first-party click measurement after privacy, CSP, data retention and consent review. Never collect user-provided content.

## Release checklist

- Approved immutable tag and verified downloadable CSS; no hypothetical version claim.
- Verified production documentation, screenshot accuracy, tutorial and links.
- Manual accessibility, security and release gates resolved or clearly disclosed.
- Brand and commercial clearance where applicable.
- No claim of universal performance superiority or accessibility certification.
- Collect feedback in existing GitHub issues, not fabricated testimonials.

## Show HN draft — hold until approved

Title: Show HN: Syntyr CSS – a scoped, native HTML design system

I am building Syntyr for teams that want reusable application UI without making a component runtime part of their CSS stack. The MIT-licensed library uses native HTML, scoped component classes and theme tokens. You can self-host a pinned stylesheet and keep forms, navigation and application behavior in your own stack.

I would like feedback from developers building server-rendered apps, especially Go, Django and HTMX projects: which real screens are easiest to adopt, and where does the component contract get in your way?

Try the starter wizard and inspect the actual HTML before deciding whether it fits your app.

## Product Hunt draft — hold until approved

Tagline: Native HTML, reusable UI, less runtime machinery.

Description: Syntyr is an MIT-licensed CSS-first design system for SaaS, websites and developer tools. Compose scoped components and themes using ordinary HTML, or integrate them into the renderer you already use. Start with a pinned stylesheet and generate a copy-owned starter. Application logic remains yours.

## Developer community draft — hold until approved

I'm looking for feedback on a CSS-first approach to server-rendered interfaces. Syntyr provides scoped UI classes and theme tokens, without a required library JavaScript runtime. The starter wizard outputs ordinary HTML with Go, Django, HTMX and React integration guidance. Would you try it on one real screen and tell me what was missing? Please include the installed version and framework.

Before posting, include verified live links, the actual approved release version and any important limitations. Do not imply npm or paid product availability.
