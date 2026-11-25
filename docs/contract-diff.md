# Compare Syntyr CSS public API contracts

This maintainer-only, offline Python standard-library tool compares two
**generated** `metadata/syntyr-contract.json` inventories. It detects possible
consumer-facing removals without introducing a CSS compiler or runtime dependency.

From a Syntyr checkout with both source revisions' generated manifests saved
locally as `/tmp/old-contract.json` and `/tmp/new-contract.json`:

```sh
python3 scripts/contract_diff.py /tmp/old-contract.json /tmp/new-contract.json
python3 scripts/contract_diff.py /tmp/old-contract.json /tmp/new-contract.json --json
python3 scripts/contract_diff.py /tmp/old-contract.json /tmp/new-contract.json --json --fail-on-breaking
```

If a checked-out Git revision contains the manifest, its committed bytes can be
copied via `git show REV:metadata/syntyr-contract.json > /tmp/old-contract.json`.
Do **not** assume every older published release carried this manifest; if absent,
do not manufacture or compare an inferred snapshot.

The report examines:
- added/removed public `syn-*` class names and `--syn-*` token names;
- added/removed themes, CSS stylesheet entrypoints, and declared attribute values;
- a surviving class/token that is no longer present in one of its previous
  stylesheet distributions.

An additive name is not automatically a compatible implementation. Likewise,
an unchanged inventory does **not** prove stable CSS behavior, styles, selector
specificity, accessibility, dynamic states, or browser support. The generator's
curated component/recipe information is not a complete CSS compatibility model.
Run existing build determinism, browser, keyboard, screen-reader, and release
checks separately.

**Exit status:** 0 for a completed comparison (even if removals are present,
unless gating is requested), 1 for possible removals with
`--fail-on-breaking`, and 2 for malformed input, unsupported schema versions,
duplicate keys, or file errors. JSON output is stable and suitable for an
external release-check workflow; the tool neither writes nor publishes assets.

Do not use the report to automatically enforce v1 compatibility before a
stable API is declared. Pre-1.0 contracts remain experimental per
[API stability](api-stability.md).
