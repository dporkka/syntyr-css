# Optional real-browser adoption regression

`tests/adoption_visual_browser.py` runs **Chromium** against four built
independent consumer fixtures: Tailwind v4, static Astro, a plain HTML
shadcn semantic-token example and an official CLI-generated shadcn React/Radix
button example. It uses ephemeral local HTTP servers and
checks real DOM/computed styles, nested theme tokens, keyboard focus outlines,
missing assets and viewport overflow. It compares PNG screenshots against
checked-in baselines at `tests/visual-baselines/`.

This is **development-only** tooling, not part of Syntyr's CSS package or
its zero-JS runtime contract. It is not yet an enforced release gate.

## Commands

```sh
cd examples/tailwind-v4 && npm install && npm run build && cd ../..
cd examples/astro && npm install && npm run build && cd ../..
cd examples/shadcn-bridge && npm install && npm run build && cd ../..
cd examples/syntyr-shadcn-react && npm install && npm run build && cd ../..

python3 -m venv /tmp/syntyr-adoption-browser
/tmp/syntyr-adoption-browser/bin/pip install playwright pillow
/tmp/syntyr-adoption-browser/bin/python -m playwright install chromium
/tmp/syntyr-adoption-browser/bin/python tests/adoption_visual_browser.py
```

If a verified Chromium binary is already installed, optionally point to
it with `SYNTYR_CHROMIUM_EXECUTABLE=/absolute/path/to/chrome` when running.
Baselines in this branch were captured on Linux using the local Chromium
1255 Playwright-browser cache. Rendering differences across operating systems,
browser revisions and installed fonts can cause false positives. The current
comparison tolerates up to 2% pixels differing by more than 24 units.

For **intentional**, reviewed UI changes, regenerate baselines with
`--update-baselines`, inspect all three PNG images and commit the new
artifacts. Do not regenerate baselines simply to hide a failure.

Use this alongside accessibility/axe checks; pixel comparisons alone cannot
verify screen-reader semantics, correct focus order, or component behavior.

## Standalone CSS preset screenshot regression

A second, independent test exercises the **zero-build browser consumer path**,
with no Node/npm example projects. It loads `examples/preset-preview.html`
from localhost, switches between `dist/presets/minimal.css`, `saas.css` and
`cinematic.css`, and tests each at **390px and 1280px** in Chromium. The test
checks a single stylesheet link, theme tokens, that host elements outside
`.syn-root` remain unstyled, that SaaS recipes do not leak into minimal,
native `details` and popover interaction, keyboard focus, and horizontal
reflow. PNG baselines are checked in under `tests/visual-baselines/presets/`.

```sh
# Optional maintainer-only Python/browser tooling, not distributed with CSS.
python3 -m venv /tmp/syntyr-visual-env
/tmp/syntyr-visual-env/bin/pip install playwright pillow
/tmp/syntyr-visual-env/bin/python -m playwright install chromium
/tmp/syntyr-visual-env/bin/python tests/preset_visual_browser.py
```

Only for **reviewed intentional rendering changes**, regenerate with
`python tests/preset_visual_browser.py --update-baselines` using the same
Playwright environment, compare all six PNGs, and commit them. Screenshots
are environment-sensitive (browser/font revisions); a 2% pixel tolerance is
not a substitute for manual accessibility, zoom, WebKit and Firefox coverage.
The test is not a mandatory consumer or release dependency.

## Canonical responsive preset snapshots

The existing preset visual runner also accepts `--canonical` to exercise
three presets across the six standard viewport dimensions (18 captures).
The legacy baseline set remains separate. Generate new snapshots only for
intentional, reviewed changes:

```sh
python tests/preset_visual_browser.py --canonical --update-baselines
python tests/preset_visual_browser.py --canonical
```

Use an identical Chromium version, operating system and font configuration
for baseline generation and comparison. These opt-in snapshots are not a
cross-platform release certification.

To audit every published page at the six canonical widths and heights and
retain individual pass/fail/blocked results:

```sh
python tests/published_reflow_browser.py --browsers chromium --canonical-only --report /tmp/syntyr-responsive.json
```

A nonzero exit indicates a failure or blocked browser. The report is a local
test artifact, not part of the public site or CSS distribution.

## Dimensional query boundary tests

```sh
python tests/responsive_boundary_browser.py --browsers chromium
python tests/responsive_boundary_browser.py --browsers chromium firefox webkit
```

The maintained inventory covers dimensional media and container queries in
`src/`. Each threshold is exercised at the adjacent CSS pixels below, at,
and above its boundary using the default 16px font size. The contract test
requires newly introduced dimensional queries to be registered explicitly.

Container probes use the distributed stylesheet and constrain component
parents independently inside a 1920px viewport. Named region probes also
nest a narrow region inside a wide region. Assertions verify actual grid,
stacking, label, overlay and navigation behavior; these are not merely
screenshots or media-query string checks. The Chromium run is part of the
PR smoke configuration, and all three engines are configured for manual/tag
runs. This does not cover every docs-only CSS rule, device font preference,
or arbitrary content combination.

## Bidirectional resize and localized content stress

```sh
python tests/responsive_stress_browser.py --browsers chromium
python tests/responsive_stress_browser.py --browsers chromium firefox webkit
```

Six representative live documents are resized from 320 to 2560 CSS pixels
and back without navigation between samples. Sampling is at most 32 pixels
apart and also includes canonical widths and adjacent media-query thresholds.
This is a sampled sweep, not exhaustive testing of every possible width.

Localized component fixtures use German and Brazilian Portuguese (LTR),
Arabic and Hebrew (RTL), long labels, long actions, and unbroken record
identifiers across the six canonical viewports at 100%, 150% and 200% root
font size. Assertions check document overflow, clipped text, input/action
overlap and visual direction of adjacent statistics cards. Root font
enlargement is not equivalent to native browser zoom. Browser font shaping,
all languages and arbitrary application content are not certified by these
fixtures. The Chromium stress run is configured for PRs and the full
three-engine run for manual/tag execution.

## Publish historical responsive compatibility evidence

Generate the public static dashboard and JSON from completed local/CI
reflow reports, using the exact tested source revision and UTC test date.
Repeated input files must represent disjoint cases for that same revision.

```sh
python scripts/build_responsive_compatibility.py \
  --input /tmp/syntyr-responsive.json \
  --revision "$(git rev-parse HEAD)" --tested-on "$(date -u +%F)"
```

Only run this command with reports from the revision supplied; do not
substitute the current HEAD for an earlier tested checkout. Review the
generated HTML and JSON together before committing. Raw diagnostics are
not published. Report hashes identify the private input files; they do
not authenticate the run or imply an independent certification.

## Optional local responsive audit CLI

Run from a source checkout with developer-installed Playwright and browsers.
Start your own trusted local development server first.

```sh
python scripts/syntyr_agent.py responsive http://127.0.0.1:8000/index.html \
  --browsers chromium firefox --report /tmp/responsive.json
```

The default is six canonical viewports. Add `--stress` for the 15-case
orientation and root-text matrix. Exit 0 means all recorded cases passed;
exit 1 means at least one failed or was blocked; invalid invocation exits 2.
This is opt-in tooling, not part of the consumer CSS installation.

Use trusted local pages only. The command rejects non-loopback targets and
filters ordinary cross-origin requests, but is not a sandbox for malicious
pages or redirects. It does not replace Websyt.dev's SSRF-safe remote browser
infrastructure. Raw report paths and errors may contain private application
data; do not publish them directly.

The version-1 raw report is shared with the published reflow runner:
`schemaVersion`, `summary` (pass/fail/blocked counts), and `cases` (engine,
page, width, height, textScale, status, optional error). The local report also
includes a suite name and limitations. Consumers should recompute counts,
reject duplicate cases, and never interpret blocked or missing as success.
