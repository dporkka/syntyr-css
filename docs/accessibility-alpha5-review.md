# SYNTYR alpha.5 — outstanding accessibility review

This report distinguishes the most recent automated findings from older
pixel-sampling evidence. It is **not** a WCAG certification.

## Fresh exact-head audit: `70ec764` (November 18, 2026)

**Newest automated source snapshot, not alpha.5 release approval.**
This source candidate includes the focused fixes to keyboard-inaccessible
documentation code blocks and a prohibited ARIA label on a nested form footer.

- Chromium with **Playwright 1.65.2** and pinned **axe-core 4.10.3**,
  checksum SHA-256
  `880970c081707360e64f34cea25ff91892f5bc95675b0776925b9709dd8a68bb`:
  **37 pages**, **zero confirmed automated violation nodes**, and
  **15 incomplete color-contrast rule results comprising 165 element targets**.
- Baseline `985fe01` had **two serious scrollable-region-focusable nodes**
  in the design-principles guide and one **aria-prohibited-attr** incomplete
  footer. The source candidate eliminated all three; the 165 remaining
  incomplete targets concern contrast, not confirmed failures.
- The reconciled source passed **1,035 Python tests (one skipped)**,
  generated-document/metadata/registry/CSS/Cloudflare and maintenance checks.
  Chromium/Firefox verified focused ArrowRight keyboard scrolling of the
  code examples at 320px/390px (also forced-colors emulation) and 1280px.
- Conservative pixel triage at **1280/390/320px** produced
  **495 observations**: **459 screenshot samples above text thresholds**,
  **9 opaque computed placeholder pairs above threshold**, and
  **27 non-text entries**, with **zero sampled below or near threshold**.
  The lowest sampled text result was approximately **5.19:1** against the
  ordinary-text 4.5:1 threshold, on the business example kicker.

**Still open:** manually adjudicate each of the 165 axe-incomplete contrast
targets in real painted, interactive states. Samples are not glyph-level
certification and may miss gradients, overlays or focus/hover appearance.
True **200%/400% browser zoom**, native OS high contrast, screen-reader
testing and representative application flows are not proven. The unpatched
high-severity `picomatch` advisory in optional Expo development tooling
remains separate and unresolved. **Do not tag or publish alpha.5** on these
automated results alone.

For reproduction, run the pinned local axe script with
`tests/axe_audit.py`, then pass its JSON report to
`tests/contrast_pixel_triage.py` at widths 1280, 390 and 320. The JSON
reports were retained outside the source tree at the audited revision.
Repeat the audit when main advances.

## Historical follow-up audit: `9f7f22b` (November 15, 2026)

This is a **newer source-only candidate audit**, not a published
release or an accessibility certification. It incorporates the enlarged-text
WebKit reflow fixes and the restored `examples/native-apis.html` audit coverage.

- Chromium headless, Playwright 1.58.0 and the pinned axe-core **4.10.3**:
  **28 pages audited, zero confirmed automated WCAG-tagged violations**,
  **14 incomplete color-contrast rule results involving 162 distinct
  element entries**. The axe payload SHA-256 was
  `880970c081707360e64f34cea25ff91892f5bc95675b0776925b9709dd8a68bb`.
- Source CSS includes targeted min-content grid sizing, text wrapping,
  and long-label reflow improvements. The original 320px / 2× WebKit
  reproducible overflow failures on six pages were resolved in focused tests.
- WebKit **26.0** was launched with user-local native libraries and
  Playwright 1.58.0 on Ubuntu 24.04; neither the operating-system packages
  nor Syntyr consumer JavaScript dependencies were changed. This is useful
  browser evidence but does **not** substitute for the pinned Playwright
  1.65.2 release-image gate, genuine browser 200%/400% zoom,
  OS-native high-contrast, or screen-reader testing.

| Page | Incomplete contrast element entries |
| --- | ---: |
| `docs/blocks.html` | 37 |
| `examples/geometry-terminal.html` | 30 |
| `docs/index.html` | 17 |
| `examples/flagship-grid.html` | 16 |
| `examples/flagship-noir.html` | 14 |
| `examples/operations-console.html` | 11 |
| `examples/pricing.html` | 7 |
| `examples/saas-workflows.html` | 7 |
| `examples/business.html` | 6 |
| `examples/console.html` | 5 |
| `examples/symbols.html` | 5 |
| `examples/terminal.html` | 4 |
| `docs/catalog.html` | 2 |
| `examples/native-apis.html` | 1 |
| Other audited pages | 0 |
| **Total** | **162** |

The audit's incomplete results may reflect gradients, pseudo-elements or
complex backgrounds; they are **unresolved** rather than passed or failed
contrast measurements. Prioritize the Blocks, geometry, documentation and
flagship hero surfaces for a real painted-background assessment. Manual
accessibility review, actual browser zoom and assistive-technology evidence,
naming clearance and authenticated distribution ownership all remain open.
**Do not freeze, tag or publish alpha.5 solely based on this evidence.**

## Follow-up pixel triage after PR #118 (November 15, 2026)

At `main` commit `9ff10ac` (which merged accessibility PR #118), pinned
axe-core 4.10.3 returned **zero confirmed violations** across 27 audited
pages, but **162 unresolved color-contrast elements** across 13 pages. A
reproducible developer-only contrast triage examined three viewport widths:
1280px, 390px, and 320px. These are screenshots with text glyph fill hidden,
**not** measured glyph-level conformance.

The initial 486 element/viewport observations included three provisional
below-threshold samples (dot-field gallery caption at 1280/390px and Grid
flagship lede at 390px), three narrow-margin samples, 450 sampled above the
relevant text threshold, 27 non-text cases, and three unsampled placeholder
cases. The follow-up branch adds localized contrast backdrops without removing
the decorative patterns. Re-sampling found **456 observations above sampled
text thresholds**, **27 non-text**, **3 unsampled**, **0 sampled-below-threshold**
and **0 narrow-margin** at the three widths. This prioritizes risk but **does not
resolve any axe inconclusive as a certified pass**.

After rebasing the candidate onto newer `main` commit `7e5c14d`, a fresh
axe-core scan reported **160** inconclusive elements across 27 pages. The
three-width repeat (480 observations) contained 450 sampled-above, 27
non-text, 3 unsampled placeholder and **zero sampled-below or narrow-margin**
entries. This is a newer snapshot than the 162-target baseline, not an
assertion that all 160 remaining elements have been manually adjudicated.

A still newer rebase onto `main` commit `c726dc3` (which restored the
native-APIs audit page) produced **161 inconclusive elements on 28 pages** at
candidate revision `912e431`, with 14 incomplete rule results and zero
confirmed violations. Across 483 element/viewport observations, 450 text
observations sampled above their thresholds, 27 involved non-text glyphs and
6 could not be sampled (the `#dispatch` and `#native-notes` textareas at three
widths each); **zero sampled below threshold or within the caution margin**.
This replaces the 160-element figure as the newest candidate triage, but
**all 161 inconclusive elements still require human review**.

The HTML sample text is not representative of every palette override or every
author-created page. The unsampled item is the `#dispatch` textarea's
placeholder; the non-text items are prompts and decorative symbols.
Manual contrast adjudication is still open for all 161 latest targets, including
composited glyph-level backgrounds and interaction states. Genuine browser
200%/400% zoom, NVDA/VoiceOver, and **native OS** high-contrast testing are
also still unverified. Browser forced-colors *emulation* and root-font scaling
are only regression proxies. Do not treat the follow-up as WCAG 2.2 AA
certification or approval to publish alpha.5.

Run the opt-in methodology documented in [accessibility.md](accessibility.md),
retaining its JSON report, source commit and browser versions with review notes.

## Verified source snapshot: `038a24d` (November 15, 2026)

This **point-in-time source audit** includes PR #68 (the native CSS
flow/high-contrast corrections) and the Blocks/Assets gallery changes through
`038a24dd626c3299a10abd0de8ff6890adc7ea3d`. It is not a verdict on commits
merged afterward, the published alpha.4 assets, or the future alpha.5 release.

- Reproducible CSS, API metadata, generated LLM reference and optional
  ecosystem adapters: **PASS** with `--check`. Full Python stdlib suite:
  **311 passed**. A public-only Cloudflare site build included **114 allowlisted
  files**; the 39-file alpha.5 candidate ZIP packaged successfully **without
  publishing, freezing, or tagging a release**.
- The developer-only Linux Playwright **1.65.2** matrix covered
  **22 pages × 3 viewport widths × 3 engines = 198 passing browser cases**
  in Chromium, Firefox and WebKit, including gallery-specific keyboard/popover
  assertions. The accompanying **88 enlarged-root-font reflow cases per engine
  (264 total)**, **two Chromium forced-colors-emulation tests**, and focused
  seven-theme native CSS tests in all three engines also passed. This stress
  testing is not actual browser zoom or OS-native high contrast. Tests changed
  no consumer runtime dependencies.
- A separate pinned **axe-core 4.10.3** audit of **21 pages** found
  **zero confirmed automated WCAG-tagged violations**, with **11 incomplete
  color-contrast rule results containing 129 unresolved nodes**. SHA-256 of
  the repository audit harness (`tests/axe_audit.py` at audited commit
  `038a24d`): `3f94a5672d13c39b511131386bc70abba43b81cba37a672f62b382c8908ddd58`.
  SHA-256 of the separately downloaded axe-core 4.10.3 JavaScript payload
  used by that harness: `880970c081707360e64f34cea25ff91892f5bc95675b0776925b9709dd8a68bb`.
  Incompletes are not passing contrast measurements or proven defects.
- GitHub showed Cloudflare Pages, build, deploy, and build-status checks
  successful for the audited commit. **A real exact-head Woodpecker pipeline
  is still unverified.** PR #68's CodeRabbit check was cancelled after the PR
  closed; this was not an independently completed CodeRabbit approval.

| Page | Unresolved axe color-contrast nodes |
| --- | ---: |
| `docs/blocks.html` | 38 |
| `examples/geometry-terminal.html` | 30 |
| `docs/index.html` | 14 |
| `examples/operations-console.html` | 11 |
| `examples/pricing.html` | 7 |
| `examples/saas-workflows.html` | 7 |
| `examples/business.html` | 6 |
| `examples/console.html` | 5 |
| `examples/symbols.html` | 5 |
| `examples/terminal.html` | 4 |
| `docs/catalog.html` | 2 |
| Remaining 10 audited pages | 0 |
| **Total** | **129** |

**Manual prioritization:** inspect the Blocks hero and featured content,
each shaped geometry surface, the documentation hero and the operations
console first. These four pages account for **93/129** unresolved targets.
Record the effective painted background including gradients and pseudo-elements,
foreground color, theme, viewport, interaction state, a screenshot and measured
contrast; do not automatically dismiss an axe incomplete because a CSS token pair
is accessible in isolation.

**Release gates that this evidence does not close:** true 200% and 400% browser
zoom, NVDA/VoiceOver screen-reader operation, native OS high-contrast mode,
manual review of the 129 inconclusive nodes, and trademark/name clearance.
Root-font reflow stress and forced-colors *emulation* are useful but are not
substitutes. Do **not** tag/freeze/publish alpha.5 from these results alone.

## Historical post-merge snapshot: `b19c331` (November 14, 2026, Brasília)

This was the latest **executed** audit snapshot at that time, after the merges of
[PR #14](https://github.com/dporkka/syntyr-css/pull/14) and
[PR #22](https://github.com/dporkka/syntyr-css/pull/22).
The published alpha.4 CSS remains immutable; alpha.5 is not yet published.

- Deterministic build: **PASS**; Python contracts: **155 passed**.
- Pinned Playwright 1.64.1 Linux container: **23 Chromium interaction
  checks**, **16 public pages × 3 viewports × 3 browser engines** (144 cases),
  **64 reflow cases × 3 browser engines** (192 cases), and docs-only theme
  editor checks: **PASS**. These are automated tests, not actual browser zoom
  or assistive-technology operation.
- axe-core 4.10.3: **0 confirmed violations** across 16 pages; **345
  unresolved `color-contrast` target entries on 13 pages**. These have
  **not** been adjudicated as passes and do not establish WCAG compliance.
- Cloudflare Pages public deployment: current CSS, docs, new demo, and
  immutable release asset matched locally generated bytes for this exact
  main commit in sampled SHA-256 comparisons; private tests/business/.env
  paths returned HTTP 404. **63 allowlisted public assets** built locally.
- GitHub/Cloudflare build and deploy checks succeeded on `b19c331`; an
  independently executed Woodpecker pipeline on this exact commit was **not
  verified**.

| Page | Inconclusive color-contrast targets |
| --- | ---: |
| `index.html` | 42 |
| `docs/index.html` | 122 |
| `examples/console.html` | 33 |
| `examples/resources.html` | 45 |
| `examples/pricing.html` | 8 |
| `docs/console-kit.html` | 14 |
| `examples/saas.html` | 0 |
| `examples/business.html` | 6 |
| `examples/terminal.html` | 4 |
| `examples/geometry-terminal.html` | 26 |
| `examples/operations-console.html` | 11 |
| `examples/themes.html` | 21 |
| `examples/vertigo-admin.html` | 0 |
| `examples/saas-workflows.html` | 7 |
| `examples/minimalist-patterns.html` | 6 |
| `examples/design-states.html` | 0 |
| **Total** | **345** |

These are axe-core *incomplete* element entries rather than proven defects.
Regenerate the exact selector-level evidence with:

```sh
python3 tests/axe_audit.py --axe-file /tmp/axe.min.js \
  --report /tmp/syntyr-axe-manual-review.json
```

The earlier pixel-sampling results below were collected against `4a623d0`,
**not** `b19c331`. They cannot be transferred to the additional 20 findings
or used to close the current 345 targets. Prioritize gradient/pseudo-element
cases, the previously narrow 4.65:1 margin, keyboard and contrast states,
and text-overflow cases in horizontally scrollable tables.

### Manual-only release requirements still open

Real 200% and 400% browser zoom; actual screen-reader navigation with named
assistive technologies and browser versions; native OS high-contrast/forced
colors; keyboard workflows in a representative integrated application; and
review/adjudication of the 345 inconclusive contrast targets. Do not describe
these automated results as a certification.

## Historical comparison: `4a623d0` baseline

The November 14 (Brasília) baseline `4a623d0`, incorporating
[PR #21](https://github.com/dporkka/syntyr-css/pull/21), was independently
tested before subsequent PRs merged. Its historical color-contrast counts and
pixel samples are retained below; they should not be confused with the
newer post-merge report.

## Automated axe-core findings

The fourteen-page post-merge audit with axe-core 4.10.3 and WCAG A/AA tags returned **zero confirmed violations** and **eleven inconclusive `color-contrast` rule results involving 325 individual targets**. Incomplete is not equivalent to passing.

| Page | Inconclusive elements |
| --- | ---: |
| `index.html` | 42 |
| `docs/index.html` | 115 |
| `examples/console.html` | 33 |
| `examples/resources.html` | 45 |
| `examples/pricing.html` | 8 |
| `docs/console-kit.html` | 14 |
| `examples/saas.html` | 0 |
| `examples/business.html` | 6 |
| `examples/terminal.html` | 4 |
| `examples/geometry-terminal.html` | 26 |
| `examples/operations-console.html` | 11 |
| `examples/themes.html` | 21 |
| `examples/vertigo-admin.html` | 0 |
| `examples/saas-workflows.html` | 0 |
| **Total** | **325** |

The 325 targets comprise 282 unresolved backgrounds involving gradients, 34
involving pseudo-elements, four too-short text cases, four non-text-only cases,
and one partially obscured element. They are **not** 325 proven defects.
Generate a reproducible node-by-node triage report (selectors, HTML snippets,
rule and failure summaries) in a local file using the developer-only audit:

```sh
python3 tests/axe_audit.py --axe-file /tmp/axe.min.js \
  --report /tmp/syntyr-axe-manual-review.json
```

The automated checker cannot establish the effective paint underneath these foregrounds where gradients and pseudo-elements overlap text. Contrast-token unit tests are useful but do not certify composited backgrounds.

## Supplemental browser-pixel contrast triage — merged `4a623d0`

The axe report's **325 incomplete targets** were also investigated with a
one-off Chromium screenshot-sampling pass on the merged source. This does not
alter the number of axe findings or convert an incomplete axe result to a pass.

| Viewport | Elements with pixel samples | Not directly sampled | Background-pixel samples | Lowest measured contrast |
| --- | ---: | ---: | ---: | ---: |
| 1280 px | 324 | 1 | 5,970 | 4.65:1 |
| 390 px | 310 | 15 | 6,480 | 5.09:1 |
| 320 px | 310 | 15 | 7,239 | 4.95:1 |
| **Total element/viewport observations** | **944** | **31** | **19,689** | — |

**No below-threshold result was found at the sampled positions** using 4.5:1
for ordinary text and 3:1 for large/bold text. The closest result was the
Studio header badge at 1280 px (4.65:1 against a gradient); it should receive
priority in visual review because its margin above 4.5:1 is narrow.

Method: Chromium **156.0.8078.4** at device scale factor 1, Playwright
**1.65.2**, a 1280/390/320 px page viewport, `getComputedStyle().color`
for text foreground, text-node `Range.getClientRects()` for location, and
full-page screenshots with glyph fill temporarily transparent to reveal
underlying gradients. Five horizontal by three vertical points per text
fragment were sampled and compared using the WCAG sRGB luminance/contrast
formula. These are **sampled background pixels**, not a guarantee about
every pixel beneath every glyph. Fixed viewport and static states do not
establish behavior across zoom, hover, focus or user-customized themes.

The sole 1280 px unsampled target was `#dispatch`, a textarea without
ordinary text nodes; its computed placeholder color `rgb(173,191,202)`
against background `rgb(8,15,25)` measures **10.14:1**, and its input
text color measures **17.93:1**. At 320/390 px, the 14 additional unsampled
targets were horizontally off-screen cells/statuses inside the deliberately
scrollable `examples/resources.html` table. These cells were sampled at
1280 px, but their mobile scrolled state still warrants manual inspection.

**Interpretation:** this triage found no obvious color-contrast regression in
the sampled cases; it **does not** close the 325 manual-review targets or
certify WCAG AA. Background sampling can miss local gradient extrema,
overlapping pseudo-elements, text-shadow effects, embedded graphics, and
interactive states. The actual screen reader, real zoom, high-contrast mode,
and representative-product checks below remain open.

## Manual verification protocol

For each flagged element, record selector, theme, browser, viewport/zoom setting, sampled foreground and effective background, measured contrast and screenshot. Test the lowest-contrast part of each gradient. Apply WCAG thresholds of at least 4.5:1 for regular text and 3:1 for large text and applicable essential UI graphics. Check hover, focus, disabled, selected and nested-theme contexts.

Earlier automated browser evidence covered **126 viewport cases** across Chromium/Firefox/WebKit and **168 enlarged-text reflow cases** on a historical commit. These figures are not the latest branch coverage. The Chromium forced-colors primary-link screenshot and focus tests passed for all seven palettes in that snapshot. None of these checks substitute for native Windows High Contrast or other OS-level modes, real browser zoom, or a screen reader.

## Remaining release checklist

- [ ] Measure or adjudicate each of the **165 axe-incomplete contrast elements** in the latest 37-page candidate audit above (70ec764). Earlier 161-, 162-, 345- and 325-entry figures are historical snapshots, not the current review queue.
- [ ] Test keyboard-only navigation, native dialog/popover focus, table regions, disclosure and form semantics in a representative real app.
- [ ] Perform real assistive-technology testing with NVDA, JAWS, VoiceOver or Orca and record evidence.
- [ ] Test true 200% and 400% browser zoom on supported browsers; verify navigation, reflow and target visibility.
- [ ] Check actual OS forced-colors/high-contrast and reduced-motion settings.
- [x] Record browser versions used for automated testing (not a permanent
  support guarantee). The **current** 16-page matrix and 64-case/engine
  reflow run used Linux `mcr.microsoft.com/playwright/python:v1.64.1-noble`
  with Playwright Python 1.64.1: Chromium **156.0.8078.4**, Firefox
  **157.0**, and WebKit **27.2**. Versions were read directly using
  `browser.version` from the same pinned image.
- [x] Preserve the **historical** 14-page baseline's separate browser
  versions: Chromium 159.0.8154.6, Firefox 159.0, WebKit 27.2 in the
  Playwright 1.65.2 image. These do not describe the newer 1.64.1 run.
- [ ] Establish browser support versions and unresolved exceptions before a stable release.

A passing axe-core run alone is **not** sufficient to claim WCAG conformance.
