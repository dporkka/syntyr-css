# Syntyr Console Kit — 10-interview design-partner pilot

**Public baseline (2026-11-15): no verified prospects contacted.**
This is the repository's initial research snapshot, not a claim about later offline activity. Run the private scorecard below for current evidence.
A [public invitation is posted](https://github.com/dporkka/syntyr-css/issues/3), but no actual participants have been recruited. This is a zero-budget qualitative validation experiment, not a marketing
automation or a promise to ship premium assets. Core CSS, Grid and Noir themes,
the full component library, and the free examples remain MIT-licensed.

## Hypothesis and decision

An independent developer building server-rendered dashboards (Go/templ,
HTMX, Rails/Hotwire, Django, Astro, Rust templates) will pay **$59 one time**
for *complete polished and accessible application screens*, instead of
needing a new JavaScript component framework. The current two example screens
are already free. Only **future**, separately authored screen compositions
could be sold under a commercial license.

Qualifying participants must have shipped or be currently building a
commercial/internal web application and be able to critique *actual code*
rather than screenshots. Upvotes, GitHub stars, and generic compliments are
not purchase evidence.

**Niche priority for the ten slots:** five commercial SaaS builders using
server-rendered HTML, two CRM/ERP or field-operations software builders, two
small agencies delivering admin software or client portals, and one independent
founder with a previous paid UI-kit purchase. Focus on people who have a
*current interface to ship*, not those who merely enjoy a CSS aesthetic. This
deliberately tests Syntyr's SaaS/operations niche, rather than pretending to
sample all web developers.

For each interview, establish the buyer's spending authority, the specific
application screen they need, approximate engineering hours they currently
spend building it, prior paid template purchases, and whether they can adopt
the actual HTML/CSS preview. Keep these qualitative findings separate from
would-buy answers; ten interviews cannot establish a reliable market-wide
conversion rate.

## Recruitment scope

Public review issue: https://github.com/dporkka/syntyr-css/issues/3


Use the ten **uncontacted** slots in
[design-partner-pilot.csv](design-partner-pilot.csv). They are target segments,
not fabricated identities or sales leads. Recruit only through opt-in responses
or respectful, permitted community posts; **consent** and community rules
matter. Do not scrape or mass-DM members.

Good first channels:

- **Go/templ:** the official templ guide lists Gopher Slack's `#templ`
  channel and GitHub Discussions at https://templ.guide/help-and-community/.
- **HTMX:** the official community page lists Discord and GitHub Discussions:
  https://htmx.org/talk/. Ask moderators before sharing project links.
- **SaaS and operations app builders:** prioritize opt-in discussions where Go,
  Django, Rails, LiveView or Livewire developers are shipping customer-facing
  dashboards, CRMs, service portals and internal applications. Ask for feedback
  on the actual admin screens, not just color palettes.
- **Independent SaaS developers:** ask for one-to-one critique from existing
  contacts who use server rendering and actively buy design templates.

## Public research prompt (adapt to rules of each community)

> I'm testing a tiny, MIT-licensed, zero-runtime-JS CSS design system for
> dashboards with Grid/Noir themes. Two original HTML screens are free:
> https://dporkka.github.io/syntyr-css/examples/console.html and
> https://dporkka.github.io/syntyr-css/examples/resources.html.
> I'm looking for 10 developers building real SaaS or internal tools to review
> the markup and tell me which *complete screens* are genuinely time-consuming.
> I'm also testing whether a separately authored eight-screen kit might be
> worth $59 once built. It is not on sale. Interested in giving a 15-minute
> critique? You can reply via
> https://github.com/dporkka/syntyr-css/issues .

## One-to-one message, only for an appropriate existing relationship

> Would you review two free, framework-independent HTML/CSS SaaS screens?
> I want feedback on accessibility, integration friction, and which complete
> layouts would save development time. This isn't a sales pitch; the existing
> library is MIT and the proposed $59 Console Kit has a private prototype,
> but it is not yet for sale or publicly distributed.
> A quick code-level critique would be more useful than a general opinion.

## Five questions, 15 minutes

1. What framework/backend do you actually use, and what did you ship recently?
2. Have you personally bought UI template kits? What triggered the purchase?
3. Review the two live demos, copy HTML into your app if relevant, and identify
   the first piece that creates integration or accessibility friction.
4. Which three *finished screens* are missing, and what functionality is
   expected to be included versus left to your backend?
5. After seeing this actual scope, would you commit $59 when delivered? Ask
   what budget line or comparable purchase supports that answer; mark **paid
   intent**, not actual revenue.

## Logging and thresholds

### Private, reproducible research scorecard

The committed `design-partner-pilot.csv` contains **ten synthetic target slots, not real people**. Do not commit names, email addresses, identifying descriptions, client data, interview notes, or private contact histories to this public repository.

Copy it to the ignored `business/private/` directory and record real, consented research there:

```sh
mkdir -p business/private
cp business/design-partner-pilot.csv business/private/design-partner-pilot.csv
python3 scripts/commercial_pilot_report.py --csv business/private/design-partner-pilot.csv
python3 scripts/commercial_pilot_report.py --csv business/private/design-partner-pilot.csv --json
```

The private CSV preserves the existing ten slots. Set `status` to exactly one of `not_contacted`, `invited`, `accepted`, `interviewed`, or `declined`. Set `intent` to `would_buy`, `maybe`, or `would_not_buy` **only after an interview**. Set `paid_commitment` to `documented` only if a completed interview includes explicit, independently documented buyer commitment; keep the supporting evidence privately. A verbal `would_buy` alone is not a commitment. The scorecard counts these separately and never infers orders, revenue, or conversion rates.

The report is **aggregated only**: no contact identifiers or notes appear in standard or JSON output. The interview target is a research milestone, not permission to enable checkout; the commercial launch gates in [commercial-launch-gates.md](commercial-launch-gates.md) must be independently satisfied. Do not publish the local private file, aggregate counts that identify an individual, or claim confidence in conversion rates from ten interviews.

- Update each slot's status `not_contacted` → `invited` → `accepted` →
  `interviewed` or `declined`. Store personally identifying respondent
  details only with permission, and preferably in a **private** tracker rather
  than in this public source repository.
- Log explicit outcomes separately: `would_buy`, `maybe`, `would_not_buy`,
  plus any actual **paid** commitments (only after selling is legally ready).
- Do not count hypothetical "yes" responses as sales. Sample of 10 qualitative
  interviews cannot establish a statistically reliable conversion rate.
- Before expanding the premium catalog, seek 10 interviews plus independent
  evidence of purchase intent (real preorder when legally ready, signed
  design-partner commitment, or clear willingness backed by prior purchases).
- Reject requests to move essential accessibility improvements or existing
  MIT functionality into paid bundles. Keep delivery/refund/license terms
  documented before accepting money.

**Current outcomes:** 0 invited, 0 interviewed, 0 paid commitments. The
Console Kit private prototype exists, but it is **not available for purchase** and no checkout exists.
