# Contributing to Syntyr CSS

Thank you for helping make Syntyr more useful and reliable. Syntyr is an
MIT-licensed, **CSS-first** design system. Changes should improve native HTML
and CSS without requiring a JavaScript runtime, package manager, remote assets,
or framework-specific component package.

## Start here

1. Browse [open issues](https://github.com/dporkka/syntyr-css/issues?q=is%3Aissue+is%3Aopen) and [pull requests](https://github.com/dporkka/syntyr-css/pulls). Start with [good first issues](https://github.com/dporkka/syntyr-css/labels/good%20first%20issue); small documentation, accessibility, and reproducible bug fixes are good first contributions.
2. For a new bug or feature proposal, use the [issue chooser](https://github.com/dporkka/syntyr-css/issues/new/choose). For larger changes, discuss scope and compatibility in an issue before implementation.
3. Fork the repository, create a focused branch, and open a PR against `main`. Link the relevant issue using `Fixes #123` only when the PR resolves it completely.

## Local setup

You need Git, Python 3.11+ and a modern browser. Node and browser automation
are optional maintainer tools, not consumer dependencies.

```sh
git clone https://github.com/YOUR-USERNAME/syntyr-css.git
cd syntyr-css
git remote add upstream https://github.com/dporkka/syntyr-css.git
git fetch upstream main
git switch -c fix/describe-change upstream/main
python3 scripts/build.py --check
python3 -m http.server 8000 --bind 127.0.0.1
```

Replace `YOUR-USERNAME` with your GitHub username after creating a fork.
Open [the local component gallery](http://127.0.0.1:8000/docs/) in your
browser; use a second terminal for checks below. Stop the server with Ctrl+C.

| Path | Purpose |
| --- | --- |
| `src/` | CSS source and design tokens |
| `dist/` | Generated consumer CSS; do not hand-edit |
| `examples/`, `docs/` | Real demos and canonical documentation |
| `scripts/`, `tests/` | Build, validation and regression tests |
| `integrations/` | Optional adapters outside the core runtime |

## Report a useful issue

Include the installed release or source commit, browser and operating system,
expected and actual behavior, a minimal HTML/CSS reproduction, and relevant
screenshots. Remove credentials and personal or customer data. For feature
requests, describe the user need and existing composition alternatives rather
than only a proposed API. Security reports follow [SECURITY.md](SECURITY.md).

## Before proposing changes

- Search the existing issues and pull requests to avoid duplicating work.
- Start from the current `main` branch, use a focused feature branch, and
  describe the user-facing behavior, compatibility impact, and test evidence.
- Start by composing existing semantic HTML, Syntyr classes and design tokens.
  Proposals for a new class/variant/module must name the compositions considered,
  explain why they fail, and identify the new API's ongoing test and maintenance cost.
- Keep React, Tailwind, shadcn, Figma, and AI-agent/editor adapters optional and
  independently removable. Do not introduce adapter syntax or vendor selectors
  into `src/` or require adapter packages to use the core stylesheet.
- Follow [ARCHITECTURE.md](ARCHITECTURE.md) and
  [docs/api-stability.md](docs/api-stability.md). Document changes to the
  `syn-*` class API, `--syn-*` variables, and `data-syn-*` attributes.
- Do not assume the unreleased alpha.5 source candidate's features exist
  in the published immutable alpha.4 stylesheet. Do not overwrite a tagged
  release when fixing a prerelease bug.
- Use original work or assets with documented permission and attribution.
  A visual reference does not authorize copying a third-party design system.

## Source and generated files

Edit `src/*.css` and `src/components/*.css`. The Python standard-library
build scripts produce the checked-in `dist/` assets; do not hand-edit built
stylesheets. Preserve scoped `.syn-root` behavior, opt-in semantic styling,
accessibility states, and the separation of core and optional modules.

Documentation changes must keep the curated `llms.txt` index discoverable
when relevant, then regenerate `llms-full.txt` using the repo's script.
Public documentation and examples require deliberate updates to the
Cloudflare site allowlist; never publish internal test artifacts, credentials,
business notes, or entire source directories.

## Verify a proposed change

From the repository root, use Python 3.11 or later for the full verification sequence:

```sh
python3 scripts/build.py
python3 scripts/build.py --check
python3 scripts/maintenance_policy.py
python3 scripts/design_conformance.py
python3 scripts/export_api_metadata.py --check
python3 scripts/build_agent_docs.py
python3 scripts/build_agent_docs.py --check
python3 -m unittest discover -s tests -v
python3 scripts/build_cloudflare_site.py
python3 scripts/build_cloudflare_site.py --check
python3 scripts/package_release.py
```

After committing regenerated `dist/` artifacts, verify the checked-in
distribution matches the generated files:

```sh
git status --porcelain -- dist/
```

This must produce **no output**. A successful `build.py --check` run after
`build.py` alone is insufficient: the first command may have already
rewritten files you forgot to commit.

The core Python and packaging contracts run for every PR. The Node/React/Next
adoption workflow runs its npm step on relevant CSS, integration or consumer
changes (or by manual request); documentation-only PRs do not need npm builds.
Before an alpha release, run **all** relevant consumer and browser/accessibility
checks regardless of any path-scoped PR skips. A skipped check is not a pass.
Prefer editing existing canonical guides over introducing overlapping guides,
and prefer enduring behavior tests over alpha-version-named test files. See
[architecture maintenance policy](ARCHITECTURE.md#maintenance-surface-and-test-ownership).

If you changed optional integrations, also check the relevant export scripts
and tests documented in their guides. Browser tests use optional Playwright
and browser engines **only in development or CI**; consumers do not install
these tools. See [docs/accessibility.md](docs/accessibility.md) for browser,
reflow, keyboard, focus, screen-reader and contrast checks.

For documentation-directory search changes, run `python3 tests/reference_search_browser.py`
with the optional Playwright environment and Chromium/Firefox installed.

For behavior changes, add a regression test that fails before the fix,
then verify it passes afterward. Report any unrun or unavailable browser
engines explicitly. A clean automated axe result is not a WCAG certification.

## Visual contributions and README screenshots

For visual changes, attach before/after screenshots at desktop and narrow
viewport widths. Identify the theme, viewport, browser and source revision;
use fictional data only. Check keyboard focus, reduced motion and text zoom
where relevant. Screenshots complement tests; they do not prove accessibility.

The README showcase images in `assets/readme/` are real Chromium captures
of existing examples with committed CSS, device scale factor 1 and reduced
motion. The capture definitions in `scripts/capture_readme.py` are the
authoritative list of example paths and viewport sizes.

To regenerate the complete set, use an optional developer-only virtual
environment (never install browser tooling in a consumer application):

```sh
python3 scripts/build.py --check
python3 -m venv /tmp/syntyr-readme-venv
/tmp/syntyr-readme-venv/bin/pip install playwright
/tmp/syntyr-readme-venv/bin/playwright install chromium
/tmp/syntyr-readme-venv/bin/python scripts/capture_readme.py
python3 -m unittest discover -s tests -p test_readme_showcase.py -v
```

The script opens only local examples, blocks network requests, and stages
all captures before replacing the committed PNGs. It does not run in the
consumer build or automatically change screenshots in CI. Review images
for clipping, missing assets, and accurate release labeling. Browser
version and system fonts can affect pixels; the screenshots are not
pixel-exact cross-platform baselines. Keep these separate from
`tests/visual-baselines/`; do not update test baselines just to change
marketing imagery. Do not commit browser profiles, internal screenshots
or unrelated generated files.

The public Open Graph image (`assets/og-syntyr.png`) uses the real showcase
captures. After refreshing those screenshots, optionally render its local
source at 1200 × 630 CSS pixels, scale factor 1, using the same Chromium
environment:

```sh
/tmp/syntyr-readme-venv/bin/playwright screenshot --viewport-size="1200,630" --wait-for-timeout=300 "file://$(pwd)/scripts/social-preview.html" assets/og-syntyr.png
```

Inspect the result before committing. GitHub's repository-level social preview
is configured separately from the website's Open Graph image.

## Review and release

Use the actual current-head Woodpecker quality and merge checks before
merging; a passing stale branch or a YAML file is not execution evidence.
Document unresolved accessibility, compatibility, and review concerns.
Release publication, naming clearance, and commercial licensing are separate
decisions from accepting an MIT code contribution.

**For vulnerabilities**, do not file a public issue containing exploit
details; follow [SECURITY.md](SECURITY.md) instead.
