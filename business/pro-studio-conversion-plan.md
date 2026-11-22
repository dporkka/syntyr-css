# Pro & Studio: revenue-validation and conversion plan (2026-11-22)

## Decision

Keep the existing MIT Core freely usable and ship **one paid offering first**, not a paid tier hierarchy. Console Kit is the earliest potential pilot, subject to every gate in `commercial-launch-gates.md`. Private Pro and Studio source prototypes are research concepts, **not deliverables or presales**; proposals of $149 and $299 are price hypotheses. Agency annual pricing is deferred. Do not build Stripe checkout or a subscription before the licensing, accessibility, packaging and fulfillment gates are independently cleared.

**Pro positioning:** finished SaaS/internal-tool and operations screen compositions; ideal buyer is a developer integrating a real backend. **Studio positioning:** Pro plus cohesive multi-page website templates for agencies and founders; not the existing MIT Studio palette, not a hosted editor or a production ecommerce system. Continue testing whether Studio has enough additional willingness-to-pay to be a distinct product.

## Implemented public experiment (source branch)

- Homepage: a discoverable **Products** navigation link and contextual **Compare Pro & Studio research** links.
- Products: an above-the-catalog two-path buyer chooser, followed by scope and pricing hypotheses with no checkout.
- Separate private Pro and Studio research email links with product-specific subjects and optional qualification prompts. Opening `mailto:` is not a verified submitted lead.
- Retained optional public GitHub feedback with a confidentiality warning; never collect private project details in a public issue.
- Explicitly clarified that the MIT Studio **theme** and the proposed Studio **template bundle** are different things.
- No analytics beacon, tracking cookie, hosted form, sale or new customer record was added.

## Funnel definitions — do not conflate stages

| Stage | Definition | Current verified measurement |
| --- | --- | --- |
| Product page exposure | Unique human view of `docs/products.html` | **Unknown**; not measured by source code |
| Qualified discovery | Developer/agency with active product or paid client project | **Unknown**; require voluntary qualification |
| Research CTA | Pro/Studio private email compose intent | **Unknown**; mailto launches cannot establish delivery |
| Received inquiry | Distinct human email received and reviewed privately | Manual count; no observed values claimed |
| Qualified interview | Completed discussion with an active relevant buyer | Private tracker; do not infer from email |
| Purchase commitment | Written, specific willingness to purchase at a given scope/price | Private tracker; not a completed order |
| Paid order | Processor-confirmed paid order **after launch gate** | Not currently available |
| Usable installation | Buyer confirms privately that the purchased composition shipped in a real app | Not currently available |

Recording should happen in the **private** design-partner tracker, with duplicate contacts reconciled privately and only aggregate non-identifying figures reported publicly. Never store customer emails or confidential project details in a public GitHub issue, analytics URL or static source file.

## Two-week validation sequence

1. **Days 1–3:** check that homepage to chooser to product-scope anchors and the private email compose links work on mobile and desktop. Review all pricing disclaimers, alt text and links. Manually test mailto in common environments, and document that mail clients may not be configured.
2. **Days 4–10:** invite up to ten opt-in, qualified developers/agency owners; send them to the appropriate research path. Record actual use case, stack, most expensive screen to build, prior paid UI/template purchase and objections. Don't attribute private messages to anonymous site traffic.
3. **Days 11–14:** compare real interest in Console Kit ($59 pilot), Pro ($149 hypothesis) and Studio ($299 hypothesis). Seek **specific** willingness-to-pay and integration evidence, not “looks nice.” If no evidence after 10 qualified conversations, improve the offer rather than expanding the catalog.

Before any claims about conversion *rates*, establish a trustworthy, consent-reviewed event source or first-party aggregate server logs with clear privacy disclosures. If that is added later, measure source/landing/referrer, product exploration, inquiry initiations and downstream **confirmed** responses separately. Do not label opened mailto links as conversions to paid orders. Do not introduce consumer-runtime JavaScript into Syntyr Core.

## Pricing and unit-economics experiment

- **Console Kit:** $59 one-time pilot is first to validate after launch gates; $99 is an unproven follow-on test. Prefer perpetual rights to purchased files with a finite, disclosed update term.
- **Pro:** $149 one-time *hypothesis*; demonstrate incremental value over Console Kit in operations, governance and richer application screens before listing it for sale.
- **Studio:** $299 one-time *hypothesis*; prove willingness to pay for complete website kits. Do not sell a “Studio builder” when only static templates exist.
- **Agency / team:** no live pricing; quote actual multi-developer licensing or scoped services after qualified demand, with clear limits.
- **Integration services:** separate quote-based offer after discovery. Record delivery and support hours; $1,500+ in earlier documents is not a guaranteed minimum price.

Track **net contribution**, not gross orders: subtract tax obligations, payment processor fees, refunds, delivery/support cash costs and realistic founder labor. Do not treat a 2% visitor-to-buyer rate as a fact; it was an illustrative scenario.

## Pre-launch blockers and release gate

The current source documents **no** approved trademark clearance, final executable commercial license, all-screen manual accessibility sign-off, complete buyer package, completed payments/taxes/refund procedure or tested end-to-end order and delivery. Follow `commercial-launch-gates.md`; payment links must remain disabled until every gate is verified. A private screenshot is not a purchasable product or proof of backend functionality.

## Next experiments to rank

1. **High:** qualified buyer outreach and 10 actual conversations; catalog expansion without buyer evidence is low leverage.
2. **High:** showcase a genuinely installable, no-backend static sample with responsive checks to demonstrate how a real developer would integrate it. Keep private paid source separate.
3. **Medium:** test whether a focused product-specific landing page outperforms the unified chooser once there is sufficient measured traffic to learn from an experiment.
4. **Medium:** implement privacy-reviewed first-party funnel instrumentation and server-delivered opt-in inquiry if mailto is demonstrably losing qualified leads.
5. **Later:** gated checkout, fulfillment, license management and team pricing *only after* the pre-sale blockers have been signed off.

**Stop rule:** if ten qualified interviews produce no concrete project-level purchase commitment or adoption proof, do not create more premium screen variants just to increase the count. Reconsider the offer and audience.
