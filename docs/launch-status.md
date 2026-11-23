# Syntyr release and commercial readiness

**Decision record reviewed November 23, 2026.** This is an orientation page, **not** a live CI status board, a legal finding, or a release approval. Evidence always belongs to an **exact source commit**. Recheck the relevant upstream issue, CI run, registry or approval record before changing any row.

## What is available today?

| Channel | Evidence-supported status | Safe action |
| --- | --- | --- |
| Free CSS v0.3.0-alpha.4 | [Published immutable GitHub prerelease](https://github.com/dporkka/syntyr-css/releases/tag/v0.3.0-alpha.4) | Download, pin and self-host the versioned CSS. MIT terms apply. |
| v0.3.0-alpha.5 CSS and site previews | **Unreleased source candidate**; does not have an approved immutable tag | Evaluate from a verified source checkout, clearly labeled as experimental. Do not mix with alpha.4 CSS. |
| `@syntyr/css` on npm | Prepared in source; public publication is **unverified/not claimed** | Use a local audited tarball or the published alpha.4 CSS until actual registry ownership, approved tag and public package are independently verified. |
| Console Kit, Pro, Studio | Private prototypes, **not for sale** | Review original screenshots or request a qualified research conversation. Do not accept payment, issue customer licenses or promise delivery. |
| Syntyr Studio visual editor | Separate local-first experimental repository; not a hosted SaaS | Use only its documented local preview/export workflows and pinned compatible CSS. |

## Alpha.5 release blockers

The detailed **technical process and exact-SHA review** live in [release-freeze.md](release-freeze.md). This page only summarizes gates; it cannot attest that any reviewer has completed them.

| Gate | Present status / evidence needed |
| --- | --- |
| Final source, packaging and regression tests | New exact-head test/build/browser results after the approved PR set is frozen; earlier passing results do not transfer to a different SHA |
| Automated contrast triage | [Historical November 18 report](accessibility-alpha5-review.md) had 165 axe-incomplete elements on 37 pages; **rerun for the frozen SHA** and manually adjudicate each current target |
| Assistive technologies | Manual keyboard and named screen-reader/browser workflows, real 200% and 400% zoom, and native OS forced-colors evidence remain unsigned |
| Supported browser matrix | Independently approved browser versions and real-browser checks, not only Playwright emulation |
| Brand clearance | [Issue #4](https://github.com/dporkka/syntyr-css/issues/4): appropriate trademark/name review is unresolved |
| Release owner authorization | Exact-SHA, version-matched evidence and reviewer approval recorded via [release-freeze procedure](release-freeze.md), not inferred from green automated checks |

**Fail closed:** Do not freeze the alpha.5 CDN directory, tag/publish it, or claim accessibility certification just because a test suite passes. The package-manager flow has a separate ownership and tarball audit in [package-managers.md](package-managers.md).

## Commercial readiness is independent

The [commercial launch gates](../business/commercial-launch-gates.md) and private kit's [commercial readiness issue #51](https://github.com/dporkka/syntyr-console-kit/issues/51) cover license rights, manual accessibility, tax/refund/support terms, verified checkout, entitlement-controlled delivery, and end-to-end purchase/refund evidence. No order or buyer commitment should be inferred from a demo, a mailto click, a screenshot or GitHub engagement.

**Next commercial experiment:** ten qualified developer/agency conversations with code-level integration feedback and documented, separate purchase intent; use the [design-partner research plan](../business/design-partner-pilot.md). These interviews guide investment but do not replace legal, payment or release requirements.

## Change-control sequence

1. Prioritize overlap removal and low-risk work in [open pull requests](https://github.com/dporkka/syntyr-css/pulls) before selecting one release-candidate SHA. Do not merge a stale stacked branch merely because similar functionality already exists on main.
2. Run `python3 -m unittest discover -s tests -q`, `python3 scripts/build.py --check`, and `python3 scripts/build_cloudflare_site.py --check` on that SHA, then the full browser/reflow/axe matrix.
3. Complete all manual accessibility and brand reviews; store their evidence separately with the exact SHA. A historical numerical result is **never** a release-pass flag.
4. Follow [release-freeze.md](release-freeze.md) and verify the frozen assets and HTTP cache/content hashes before public prerelease announcement.
5. Only then evaluate npm distribution; paid products must separately clear their own commercial gates.

Related: [published distribution guide](distribution.md), [commercial conversion hypothesis](../business/pro-studio-conversion-plan.md), [a11y gate issue #24](https://github.com/dporkka/syntyr-css/issues/24), [quality gate issue #26](https://github.com/dporkka/syntyr-css/issues/26).
