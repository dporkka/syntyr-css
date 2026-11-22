# Console Kit: commercial validation operating plan

**Status (2026-11-15): research only; NOT FOR SALE.** This document is operational planning, not evidence of user demand. No checkout, preorder, commercial license, fulfilled order, verified customer, or buyer commitment is present.

## The offer to test

- **Audience:** developers and small agencies building SaaS, internal tools and operations consoles with server-side HTML, Go/templ + HTMX, Django, Rails or Astro.
- **Promise:** eight original, responsive, static application-screen compositions with Grid, Noir and Studio variations. The current private prototype has expanded to 12 screen types and 36 generated screen/theme combinations; the eight-screen pilot offer remains a research hypothesis, not a final deliverable.
- **Core:** the existing Syntyr library, themes, essential CSS and free demos remain MIT. Only separately authored premium screen compositions could receive a future commercial license.
- **Pilot price hypothesis:** **$59 one time** per developer; **$99 standard** is a later experiment, not an advertised available price. Team licenses require validated demand. No subscription, licensing server, hosted designer, or Studio bundle for the first product.
- **Upsell hypothesis:** scoped customization or server-side integration, quoted case by case (potentially $1,500+ depending on deliverables). Do not promise functional backend behavior in a static kit.

## Current observable evidence

- Public MIT v0.3.0-alpha.4 released; alpha.5 is experimental and unreleased.
- Private Console Kit has twelve source screen types, 36 static variants, deterministic builds, passing Chromium/Firefox automated checks, and unresolved manual accessibility and combined WebKit verification gaps.
- Eight original **static screenshots** are published on the public concept page; public site never distributes private kit HTML, CSS, or build products.
- A public issue-form feedback route and a 10-developer interview tracker exist. As last recorded, no real interviews or paid commitments have been verified.
- The product is not commercially launch-ready. Do **not** count page views, issue form responses or verbal interest as completed sales.

## Distribution experiment: next 30 days

**Week 1 — proof and buyer discovery**
1. Publish and manually inspect the public concept page on desktop and narrow mobile screens after reviewed merges and Cloudflare deployment. Do not claim a deployment until verified.
2. Invite up to ten *opt-in* qualified design partners through existing professional relationships and community-permitted threads; prioritize developers with recent production app experience.
3. Walk through the original screenshots and free HTML examples, emphasizing backend integration boundaries. Record specific objections, not generic approval.
4. Record the number of invitations, accepted interviews and usable technical critiques; do not publish respondent identities or contact information.

**Week 2 — offer and pricing research**
1. Ask whether the participant has paid for any comparable UI pack and what concrete work it saved.
2. Compare $59 pilot purchase intent against the work expected to integrate the kit. Distinguish "might buy" from confirmed commitments.
3. Do not accept payment until the below pre-sale gate passes. If useful, offer supervised private previews governed by appropriate preview terms.
4. Document a single high-value missing workflow, if one consistently appears; avoid adding a broad catalog based on one person's request.

**Week 3 — ship-or-hold decision**
1. Complete legal/brand, accessibility, packaging and support gates before enabling any checkout.
2. If cleared and buyers demonstrate real intent, publish the pilot commercial license, fulfillment bundle, payment/refund disclosures and a single checkout. Test completed purchase + customer receipt + fulfillment + refund end-to-end.
3. If gates remain open, keep collecting feedback; continue presenting the product as a **concept** with no paid order capability.

**Week 4 — evaluate evidence**
1. Inspect adoption: did buyers actually copy the markup into a real project, or was the preview merely attractive?
2. Review net contribution and owner-hours spent per buyer, plus refund/support friction.
3. Continue only with paid-use evidence; defer a second kit until the first one is useful in deployed applications.

## Non-negotiable pre-sale gate

All must be individually verified before accepting money:

- [ ] Commercial review and clearance of the SYNTYR name in intended sale territories (preliminary screen is **not** clearance).
- [ ] Executable premium license reviewed for file-level rights; MIT notices retained for vendored CSS; provenance of original assets documented.
- [ ] Manual keyboard, NVDA/VoiceOver/Orca screen-reader, 200%/400% zoom, forced-colors, and incomplete gradient contrast reviews on all eight screen types; disclose residual limitations rather than claim certification.
- [ ] Reproducible customer package produced from the final commercial source commit, including no private build files or credentials, accurate license, usage guide, and checksum.
- [ ] Honest product terms: static layouts, no live authentication, billing, filters or server actions; responsive support matrix and update entitlement.
- [ ] Checkout, taxes, payment processor, regional/consumer refund disclosures, contact/support channel and delivery path reviewed.
- [ ] Purchase, failed purchase, delivery, support request and refund tested end-to-end without exposing customer records.

## Weekly decision metrics

Track **unknown** separately from zero. The public GitHub tracker must not store personal data or confidential client details.

| Metric | Definition |
| --- | --- |
| Qualified kit visitors | Unique users meeting the target stack/project criteria who saw the commercial offer; requires an actual measurement source |
| Demo engagement | Unique qualified users who viewed the original sample screens |
| Feedback received | Unique, attributable submissions; **not** sales |
| Interviews | Completed conversations with qualified developers |
| Purchase commitments | Documented commitments separate from casual "would buy" answers |
| Orders and revenue | Completed paid orders and recognized gross receipts; **not** pre-launch interest |
| Net contribution | Revenue less refunds, payment fees, support cash costs, and estimated owner time |
| Actual integration | Buyers who used the kit in a real app, supported by voluntary evidence |

Do not infer visitors, conversion rate or revenue from GitHub stars. Never claim a 2% purchase conversion rate is observed for Syntyr; it is an example scenario, not history.

**Decision trigger:** Complete ten qualified conversations, then decide whether to prepare an actual order flow based on credible commitments. After launch, if 50+ qualified offer-page views yield fewer than two orders, interview the audience and revise the value proposition before shipping another premium kit. Stop or reduce investment when repeat interviews reveal no willingness to pay, legal clearance is unavailable, or support erases product margin.

## Reproducible preview provenance

The original eight Console Kit captures under `docs/previews/` were made from independently authored private source using an installed headless Chromium browser (1360×850 viewport), then resized to 1120×700 WebP. The original marketing captures used private repository `dporkka/syntyr-console-kit` source at commit `35a3b4c`. Source compositions remain private. All captures intentionally contain **synthetic** application data and no real payment or authentication operations. See the dated note below for the two newer, separately approved Pro/Studio screenshots; the public allowlist now permits exactly ten still images and no premium HTML, CSS or package archives.

Existing free HTML examples are MIT and usable immediately. Publishing promotional screenshots under the public repository's MIT license does **not** convert the separately maintained private source layouts into a free source package.

## Commercial funnel implementation (November 15, 2026)

- The public homepage now links to a Console Kit product-research preview and shows an authentic screenshot. The source kit stays private.
- Qualified prospects can initiate a **private email** request with prefilled research questions; this is a mailto link, not a hosted web form or a claimed submitted lead. It requires the visitor to have a working mail client.
- GitHub issue-form feedback remains available and is explicitly **public**. Never ask respondents to put private contact details or proprietary project information in public issues.
- A bespoke implementation quote route is distinct from the $59 research offer. No prices for bespoke services are binding without a written quote.
- No event analytics, delivery rate, qualified conversion, user count, or email response rate is verified by this source change. Replace mailto with a reviewed, consent-aware form and spam controls only after demand warrants an operated backend.
- Do not present the prototype screenshots as shipping functional authentication, billing, filtering, or backends. No production checkout exists.


### Product-specific premium proof captures (2026-11-22)

The public Pro and Studio research pages now also show **one** genuine static screenshot each from private `dporkka/syntyr-console-kit` source commit `9ae6040`: Studio-theme Pro work-order queue and Studio-theme fictional B2B SaaS homepage. Captured using locally installed headless Chromium at 1360×850, resized to 1120×700 WebP. The screenshots do not include premium CSS/HTML source, buyer data, credentials or real customer accounts. They have synthetic content and convey **no** live features, entitlement or purchase availability. The public allowlist deliberately includes only those two marketing images plus the eight previously approved Console Kit screenshots. This capture record documents image provenance, not trademark, screen-reader, commercial licensing or launch approval.
