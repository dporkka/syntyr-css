## Change and verification

- User-facing need and behavior:
- Test evidence (include exact revision; flag checks not run):
- Public `syn-*` / `--syn-*` / `data-syn-*` compatibility impact:

## Low-entropy review

- [ ] Tried existing semantic HTML, native states, core classes, tokens and composition first.
- [ ] If adding a class, variant, token or abstraction: documented why existing composition or application-local CSS is insufficient, the reusable need, and ongoing test/maintenance cost. Otherwise: **not applicable**.
- [ ] Kept opt-in recipes/effects and adapters out of the core dependency graph.
- [ ] React, Tailwind, shadcn, Figma, and agent/editor tooling remain optional and independently removable; no adapter-specific CSS leaks into `src/`.
- [ ] Updated relevant regression tests and documentation, or explained why not needed.

Run `python3 scripts/maintenance_policy.py` and the focused/full suites described in `CONTRIBUTING.md`. Browser accessibility evidence is distinct from unit checks.
