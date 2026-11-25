# Syntyr CSS accessibility validation

**Status:** experimental alpha; not a WCAG certification or professional audit.

## Responsive follow-up — November 15, 2026

On the source merged by PR #135 (commit 0b04607), the published-site
layout suite passed **2,964/2,964** reflow cases: 76 allowlisted HTML
pages, 13 viewport/text configurations, and Chromium, Firefox, and pinned
Playwright 1.65.2 WebKit 27.2. These cover 320–1920 CSS-pixel widths,
mobile landscape, and 150%/200% root-text enlargement. This is **not**
native browser zoom.

For separate browser-UI zoom verification, an isolated X11 virtual display
was used to send the browser's native zoom keyboard shortcuts, rather than
CSS zoom, device emulation, or pinch/visual viewport scaling. Fourteen
representative pages passed at **200% and 400%** in both Chromium
(**28/28 checks**) and Firefox (**28/28 checks**): the original 1280
CSS-pixel viewport became 640 and 320 CSS pixels respectively, with
physical X11 window dimensions unchanged. The checks found no
document-level horizontal overflow or off-viewport controls. Pages
included the homepage, documentation, playground, pricing, forms, CRM,
console, Noir landing, and visualization gallery. Screenshots and
machine-local logs are test artifacts, not proof of a complete human
visual assessment. **Safari native zoom was not verified.**

The follow-up mobile audit identified ten native disclosure summaries with
19–22 CSS-pixel heights (three FAQ examples and seven chart data
expansions). A targeted change gives these standalone controls a 44px
minimum hit area at default text size, retaining native open/close and
focus behavior. The published-site browser matrix now checks native
controls for at least 24×24 CSS-pixel target geometry at 320px and 390px
unless a larger associated label supplies the target. This is a **focused
regression check**, not a full WCAG 2.2 target-spacing or touchscreen
conformance audit.

Manual assistive technology, Safari browser zoom, real hardware touch
testing, contrast exceptions, and native OS forced-colors review remain
outstanding.

## Audited source snapshot (November 15, 2026; commit `038a24d`)

At pinned `main` commit `038a24d`, deterministic CSS/metadata/adapters/site
checks passed, **311 Python contracts** passed, the **198-case**
Chromium/Firefox/WebKit page-viewport matrix and **264-case** enlarged-text
reflow matrix passed, alongside two simulated forced-colors checks and focused
native CSS tests; an independently executed **axe-core 4.10.3** audit of 21
pages returned **0 confirmed
automated violations but 129 unresolved color-contrast nodes**. The
candidate ZIP contains 39 files and is not a published release.

See the [exact-revision findings and manual-release blockers](accessibility-alpha5-review.md).
The 129 incomplete contrast targets require review. True browser zoom, OS
high-contrast, assistive technologies and independently executed exact-head
Woodpecker validation are **not** established by this snapshot. No WCAG
conformance or alpha.5 release approval is claimed.

## Historical post-merge results (November 14, 2026)

On `main` commit `b19c331` (after PRs #14 and #22), the Python suite
passed **155 tests**. The 16-page, three-viewport gallery matrix and 64
reflow cases per engine passed in Chromium **156.0.8078.4**, Firefox
**157.0**, and WebKit **27.2** using the pinned Playwright 1.64.1
Linux developer container. Twenty-three Chromium interaction
tests and the documentation theme-editor checks also passed.

axe-core 4.10.3 reported **zero confirmed automated violations** but
**345 inconclusive color-contrast element entries on 13 of 16 pages**.
These remain open for manual review. Live Cloudflare assets sampled against
the reproducible 63-file allowlisted build matched byte-for-byte; private
repository paths returned 404. Cloudflare's exact-head build passed, but
an independent Woodpecker pipeline execution has not been verified.

See [the current per-page evidence and manual gates](accessibility-alpha5-review.md).
This is not WCAG certification or verification of real zoom, screen-reader
behavior, or native OS high-contrast mode.

## What is and is not covered

- Source contracts: native HTML, semantic labels, opt-in scoping, predictable
  focus-visible outline, reduced-motion support, and forced-color hooks.
- Real browser matrix: Chromium, Firefox, and WebKit on desktop/mobile viewport widths,
  testing navigation, table semantics, native popover, disclosure, and overflow.
- Automated accessibility: axe-core WCAG 2.0/2.1/2.2 A/AA tagged checks on the
  public showcase and example pages (the audited set changes over time). The tool may return
  **incomplete/manual-review** findings even with zero confirmed violations.
- Still needed: screen reader testing (NVDA + Firefox or Chrome, VoiceOver +
  Safari), actual browser zoom at 200% and 400%, touch target examination,
  interactive error states, font reflow and low-vision inspection.

## Reproduce the tests without installing production dependencies

Run the standard library contracts and optional Playwright checks:

```sh
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v

# Dev-only installation; choose your package/environment manager.
python3 tests/browser_test.py
python3 tests/browser_matrix.py --browsers chromium firefox webkit
python3 tests/reflow_test.py --browsers chromium firefox webkit
python3 tests/published_reflow_browser.py --browsers chromium firefox webkit
python3 tests/minimalist_browser.py --browsers chromium firefox webkit
# Opt-in: seven-theme enlarged-label, scroll keyboard, and link-target checks.
python3 tests/accessibility_regression_browser.py --browsers chromium firefox webkit
```

For a pinned axe-core 4.10.3 audit, provide the checker at test time. No
JavaScript file is shipped to application consumers:

```sh
curl -fsSL https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.3/axe.min.js -o /tmp/axe.min.js
python3 tests/axe_audit.py --axe-file /tmp/axe.min.js \
  --report /tmp/syntyr-axe-manual-review.json
```

The published-site reflow test serves the actual Cloudflare-allowlisted HTML
and hashed CSS locally, checks every page in multiple portrait and landscape
viewports, and stresses root text at 150%/200%. It permits independently
scrollable data regions but rejects page-level horizontal overflow and
out-of-viewport controls. This is **not** 200%/400% native browser zoom.

For the remaining manual zoom gate, use the browser's own zoom control (not
CSS `zoom`, a changed root font size, device pixel ratio, or pinch zoom):
open the homepage, all-documentation index, free Noir landing, visualization
gallery, pricing, and native forms. Check 200% and 400% zoom at a 1280 CSS-pixel
starting window, then mobile landscape and portrait; record each browser,
OS, zoom, viewport, navigation/control reachability and any overflow. Run with
Chrome/Firefox and Safari/WebKit on a supported host, including keyboard and
screen-reader inspection. Keep these as outstanding human review requirements
until actually performed.

The JSON now includes a `summary` that distinguishes incomplete rule results
from **inconclusive individual element targets**, with counts by page and rule.
Prioritize the highest-count pages for composited-gradient and pseudo-element
contrast inspection. These targets are unresolved, not automatically passing
or failing; record measured contrast, viewport, state, and reviewer decision
before approving a release. The enlarged-label tests change root font size,
not genuine browser zoom; human zoom and screen-reader gates remain open.

## Contrast pixel triage (developer-only; NOT a conformance result)

An optional Chromium screenshot sampler helps prioritize axe-core findings that
cannot automatically evaluate gradients and pseudo-elements. It samples the
painted background under temporarily transparent glyphs, groups results by
page/viewport/selector, and retains non-text and unsampled targets explicitly.
The helper is deliberately **not a release gate**: selected pixels do not prove
the contrast of every glyph, hover/focus state, overlay or customized theme.
Run it with pinned tooling in a disposable developer environment:

```sh
python3 -m pip install playwright==1.65.2 Pillow==12.1.1
python3 tests/axe_audit.py --axe-file /tmp/axe.min.js \
  --report /tmp/syntyr-axe.json
python3 tests/contrast_pixel_triage.py \
  --axe-report /tmp/syntyr-axe.json \
  --output /tmp/syntyr-contrast-triage.json \
  --widths 1280 390 320
```

The November 15, 2026 `9ff10ac` baseline contained 162 incomplete contrast
elements. After rebasing the targeted contrast fixes onto `7e5c14d` (a newer
main with additional unrelated changes), a fresh axe scan reported **160
incomplete elements** across 27 pages. Across three widths (480 observations),
the heuristic classified 450 as sampled above their text threshold, 27 as
non-text (9 distinct targets), and 3 as unsampled placeholders (one distinct
target). **Zero samples fell below their threshold or within a 0.5:1 margin.**
The earlier 162-target and 456-above sample counts are historical; neither
report closes any axe incompletes as certified passes. Verify actual glyph
pixels, interaction states and screen reader/zoom/OS high-contrast behavior
before making a conformance claim.
Following a further rebase onto `c726dc3` (restored native-APIs page),
the newest candidate scan found **161 incomplete elements across 28 pages**:
450 text/viewport observations sampled above threshold, 27 non-text and six
unsampled textarea observations. There were still zero sampled-below or
narrow-margin observations. All 161 inconclusives remain open for manual
adjudication; the preceding 160-element count is historical.

See [the manual release review](accessibility-alpha5-review.md) for limitations.

For reproducible WebKit on an isolated testing host with Podman or Docker, clone
the repository to a directory that the container can read and run:

```sh
podman run --rm --shm-size=1g -v "$PWD":/work:ro,Z -w /work \
  mcr.microsoft.com/playwright/python:v1.65.2-noble \
  bash -lc 'python3 -m pip install -q playwright==1.65.2 && \
    python3 tests/browser_matrix.py --browsers chromium firefox webkit && \
    python3 tests/reflow_test.py --browsers chromium firefox webkit'
```

The image supplies browser binaries and native dependencies, not the Python
Playwright package. This test-only container may download packages and should
be run against trusted code. The `:Z` mount flag is Podman/SELinux-specific;
adjust for Docker hosts. Keep the Python and browser versions aligned.

The remote URL is part of a **developer-only test**, not a browser runtime
dependency. Pin the checker release, review its MIT license, and verify its
provenance if incorporating it into build infrastructure.

## Earlier automated baseline (November 14, 2026, unreleased alpha.5)

Against post-merge `main` commit `6109b79`, an isolated Playwright v1.65.2
Linux container passed **126** page/viewport cases (14 pages × 3 widths × 3
engines) and **168** enlarged-text reflow cases (14 pages × 4 width/font
configurations × 3 engines). Browser-reported versions: Chromium
159.0.8154.6, Firefox 159.0 and WebKit 27.2. These versions describe a
specific passing test environment; they are not a promise of broader browser
support. Chromium additionally passed 17 interactive browser checks, two
simulated forced-colors checks and three documentation theme-editor viewport
checks in the developer environment.

The axe-core 4.10.3 WCAG-tagged scan found **0 confirmed automated violations**
across 14 pages, alongside **11 incomplete rule results encompassing 325
individual nodes**. Gradients, pseudo-elements and obscured backgrounds cause
most incomplete results; a missing automated verdict is **not** a passing
contrast measurement. Generate a selector-level local review list with:

```sh
python3 tests/axe_audit.py --axe-file /tmp/axe.min.js \
  --report /tmp/syntyr-axe-manual-review.json
```

A subsequent post-merge investigation of `4a623d0` confirmed that live
Cloudflare Pages serves identical CSS and selected documentation assets. A
supplemental Chromium pixel-sampling pass at 1280, 390 and 320 px found no
below-threshold contrast among **944 sampled element/viewport observations**
(19,689 background-pixel samples). The lowest was 4.65:1; a textarea's
placeholder was evaluated separately at 10.14:1. Sampling does **not**
resolve axe's 325 inconclusive color-contrast targets into certified passes.
See the detail and remaining exceptions in the review document.

See [`accessibility-alpha5-review.md`](accessibility-alpha5-review.md) for
per-page counts and the remaining manual release gates. In particular, the
browser harness modifies root font size; this is not equivalent to genuine
200%/400% browser zoom; simulated forced colors do not represent all native OS contrast modes;
and neither an axe scan nor automated keyboard actions constitute screen-reader
validation. Native HTML dialog invoker command support also varies by browser.

## Manual checklist

1. Tab from the top of every page; test visible focus, no keyboard traps and
   skip-link behavior. Open and dismiss popovers/dialogs with keyboard.
2. At 200% and 400% zoom, inspect all content at narrow widths; no clipped
   actions, invisible labels or lost table information.
3. Test one screen reader per major browser engine for headings, landmarks,
   table captions, form labels and live status; document the actual device,
   browser version and assistive technology.
4. Force-colors/high-contrast: check panel separation, focus and form controls.
5. Disable animations in system settings and ensure nothing depends on motion.
6. Validate both the default Grid/Noir palettes and any project-specific
   token overrides for text contrast and non-text essential indicators.


## Optional system palette and intrinsic layout checks

The [minimalist patterns example](../examples/minimalist-patterns.html)
uses a CSS-only `auto` palette (Studio for light, Grid for dark),
classless form controls and intrinsic layouts. Its optional browser test
checks both OS color-scheme emulations, an explicit nested Noir region,
native checkbox/radio label layout, keyboard focus and mobile wrapping.

These automated checks do **not** replace manual audits at actual 200% and
400% browser zoom, assistive-technology operation, or customized palette
contrast validation. Record browser engine and OS when testing these paths.

## Experimental native-HTML semantic coverage (unreleased branch)

The optional `syntyr.semantic.css` now also presents native `search`, `figure`, `figcaption`,
`mark`, `kbd`, `output`, `meter` and scrollable `pre` regions. These styles apply
only inside an opted-in `.syn-semantic` subtree and do not implement
application behavior.

The development-only `tests/native_semantic_browser.py` checks Chromium,
Firefox and WebKit at 320px and 900px: the `mark` foreground/background pair
has at least 4.5:1 computed contrast in seven named palettes and automatic
light/dark mode; forced-colors emulation keeps it distinguishable; the native
GET form works without JavaScript; removing `.syn-root` removes the styling.
At 320px it checks horizontal document overflow with 200% and 400% *root
font-size enlargement*, including a scrollable code block.

These tests are **not** actual browser 200%/400% zoom, manual OS high-contrast
inspection, NVDA/VoiceOver validation, or a WCAG conformance audit. The
pre-existing inconclusive axe contrast cases and manual release gates remain
open. Use the separate [native example](../examples/native-elements.html)
for representative manual checks after publishing.

## Post-merge native-element review follow-up (November 15, 2026)

The native HTML example received four confirmed actionable review findings after
PR #38 merged. The follow-up fixes make its horizontally scrollable `pre`
region keyboard-focusable with an accessible name/region role, allow long `kbd`
chords to wrap, preserve readable foreground color for `mark > code`, and
strengthen the browser regression to verify actual internal scrolling and
keyboard focus instead of merely checking `scrollWidth >= clientWidth`.

Reproducible checks on the follow-up worktree:

- New unit contracts: 11 native-element tests pass; the full stdlib suite
  passed 189 tests before final documentation/rebase.
- Developer-only Playwright smoke: Chromium, Firefox, WebKit each passed
  across seven themes, light/dark auto, 320px/900px widths, forced-colors
  emulation, 200%/400% root-font enlargement and keyboard access to the
  scrollable SQL example.
- Shared browser matrix: all three engines passed 18 pages at three viewports.
- Shared reflow matrix: all three engines completed 72 checks each (216 total).
- Pinned axe-core 4.10.3 audit: **0 confirmed automated violations**, with
  **10 incomplete rule checks** across the 18 included pages. The new
  `examples/native-elements.html` page reported 0 violations and 0
  incomplete checks. Other pages' inconclusive findings remain manual-review
  items; these results are not blanket color-contrast certification.

### Outstanding human validation (not yet performed)

1. With **VoiceOver + Safari** and **NVDA + Firefox/Chrome** (Orca + Firefox
   can be supplementary on Linux), navigate to
   [the native HTML example](../examples/native-elements.html); verify the
   "SQL query example" region is named, focusable with Tab, and responds to
   horizontal scroll keys, without trapping focus.
2. In a real browser, set **200% and 400% browser zoom**, not only the root
   font-size test harness. At a 320 CSS-pixel effective viewport, verify
   readable captions, long keyboard shortcuts, full access to the code
   example, visible focus and no clipped form action.
3. With an actual OS high-contrast/forced-colors mode, distinguish highlights,
   focus rings, and selected controls. Also examine all axe inconclusive
   contrast targets from the main release accessibility report.
4. Record device, assistive technology version, browser version, observed
   behavior, any defects, and reviewer sign-off before claiming WCAG
   conformance or closing the manual release gate.

These are QA instructions, not evidence that human assistive-technology or
browser-UI zoom testing has happened.

## Searchable component catalog coverage (November 15, 2026)

The documentation-only component catalog has been added to the normal browser,
reflow, and axe-core matrices rather than relying only on static contracts.
It contains ten rendered component examples. With JavaScript disabled, the
examples and native HTML source disclosures remain available. Enhanced search,
empty state, live result count and clipboard/keyboard fallback were checked
in both Chromium and Firefox.

Exact-branch developer-only verification:

- Chromium and Firefox: **19 pages × 3 viewports** each, including the catalog
  interactions, passed.
- Chromium and Firefox: **76 enlarged-root-font reflow cases per engine**
  passed. This is **not** genuine browser-UI zoom.
- Local axe-core: **zero confirmed automated violations** across the 19
  audited pages, with **10 incomplete rule checks** requiring manual review.
  The catalog contributed one incomplete color-contrast rule with two nodes
  in the featured pricing demo: axe cannot infer its gradient background.
- For the catalog Studio palette, a source-token-based conservative calculation
  gives approximately **13.79:1** for dark #15233a text against the strongest
  9% blue-accent overlay on white. This is theoretical CSS compositing, not
  sampled pixels or a conformance certification.
- WebKit was **not** validated on this exact branch: the Gertrude test host
  lacks libevent-2.1.so.7.

The remaining release gates are genuine browser 200%/400% zoom, screen readers,
native high-contrast inspection, and manual resolution of incomplete axe
targets. Do not present these findings as WCAG conformance certification.

Optional native recipe smoke test: run `node tests/native_recipes_browser.js` with developer-installed Playwright and its browser engines. It exercises form label state, popover escape/dismissal, modal commands where supported, reduced-motion transitions, and narrow viewport reflow. No Playwright package is shipped to consumers.
