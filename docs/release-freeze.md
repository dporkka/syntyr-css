# Freezing a Syntyr CSS CDN release safely

This is the **unreleased alpha.5** procedure. Published alpha.4 files are immutable. A passing unit test or automated axe-core scan is **not** authorization to publish.

## Preconditions

1. Land and freeze the approved source commit on `main`; do not edit tracked files after reviewers assess it. Resolve outstanding branches and release-specific build checks first.
2. Run the full Python contract suite, published-site generation checks and Chromium/Firefox/WebKit page and reflow matrix on that exact commit. Confirm actual Woodpecker executable results; configuration and a status posted for a different SHA do not count.
3. Complete a human review for each of these gates:
   - **contrast**: adjudicate every outstanding axe-core incomplete target, including layered gradients, real screenshots and tested states; document explicit exceptions
   - **screen_reader**: record named screen reader, browser/version, focus, forms, native dialog/popover, disclosure and scrollable-table workflows
   - **real_browser_zoom**: exercise actual browser zoom at 200% and 400%; root-font scaling is not equivalent
   - **native_forced_colors**: use actual operating-system high-contrast/forced-colors, not only browser emulation
   - **browser_support**: approve the supported minimum browsers and inspect browser-matrix results
   - **brand_clearance**: record the brand decision and legal/name-clearance evidence appropriate to intended release
4. Maintain the evidence separately from the source commit. The approval document is a **review record**, not an automated accessibility certification or a cryptographically verified signature.

## Approval record

Copy `docs/release-approval-template.json` to the intentionally untracked `release/release-approval.json`. Fill the exact release version from `VERSION` and the complete immutable SHA from `git rev-parse HEAD`. For **every** required check, change status from `pending` to `pass` only after direct assessment, and provide a named `reviewer` and a specific `evidence` reference (e.g. a controlled report or issue URL). Do not fill pass statuses just to make a release script succeed.

The script checks presence, status, version and SHA, **not** the truth of a human attestation or validity of an external link. Retain the approval JSON and referenced artifacts in restricted release records before publication. A reviewer must assess them independently. Do not commit private reports or customer details into the public MIT repository.

## Candidate check, then freeze

```sh
python3 -m unittest discover -s tests -q
python3 scripts/build.py --check
python3 scripts/build_cloudflare_site.py --check
python3 scripts/freeze_site_release.py --check
python3 scripts/freeze_site_release.py --apply
```

The default command and `--check` run a **read-only technical preflight**: verify old release hashes, deterministic CSS and the exact allowlist. They do not attest to manual approval. Only `--apply` changes the repository and fails closed if tracked source is dirty, approval is missing, the approval's SHA/version differs from HEAD, generated CSS is stale, or the release version already exists. An ordinary `python3 scripts/package_release.py` still builds a **candidate ZIP** without authorization to publish it.

The freeze command stages only the public CSS distributions declared by the build script in a temporary directory, prepares SHA-256 hashes, and atomically replaces the manifest after placing the new immutable version directory. If an operation fails before manifest publication, it removes the uncommitted version directory and leaves earlier snapshots intact. It never overwrites a frozen version.

Before authorizing any **separate npm publication**, run `python3 scripts/audit_npm_package.py` on the exact candidate source to inspect the actual packed bytes and exported CSS paths. This requires npm only in the maintainer environment, not for CSS consumers. The check does not confer release approval or publish anything.

After freezing, review the manifest diff and source hashes, commit the new immutable snapshot, verify the static-site build, deploy to staging and verify live Cloudflare paths/content hashes/headers. Only then tag and publish the release through the separate release process. **This script does not deploy, tag, enable payments or publish an npm package.**

## Signed ZIP provenance (unreleased source candidate)

After the separate release approval, package the reviewed, clean commit and
create a deterministic provenance record. The creator checks every ZIP member
against the regular, allowlisted Git blobs at that exact commit, and binds the
repository, version, commit, ZIP name, byte count and SHA-256 digest. It refuses
tracked changes, unexpected members and mismatched bytes. It does not publish
or replace prior evidence.

```sh
commit=$(git rev-parse HEAD)
version=$(cat VERSION)
archive="release/syntyr-css-$version.zip"
python3 scripts/package_release.py "$archive"
python3 scripts/release_provenance.py create "$archive" release/provenance.json --commit "$commit"
```

The generated JSON is **unsigned**. A designated release maintainer can sign
it with an existing securely managed OpenSSH signing key (OpenSSH 8.2+):

```sh
ssh-keygen -Y sign -f /secure/path/release-signing-key -n syntyr-release release/provenance.json
```

Publish the exact ZIP, `provenance.json`, and `provenance.json.sig` together
only after release authorization. Keep signing keys outside the repository and
CI checkout. Do not create or trust a key just because it accompanies an
archive. Distribute the maintainer's verified public key and signer identity
through an independently trusted channel (OpenSSH allowed-signers format:
`syntyr-release ssh-ed25519 <verified-public-key>`). A consumer who has trusted
the release commit, version, signer and public key can set `expected_commit`
and `expected_version` from that trusted source, then verify:

```sh
python3 scripts/release_provenance.py verify "syntyr-css-$expected_version.zip" provenance.json \
  --signature provenance.json.sig --allowed-signers /secure/path/trusted-signers \
  --signer syntyr-release --commit "$expected_commit" --version "$expected_version"
```

Use the verifier from a trusted checkout or independently reviewed source,
not from the unverified download. Verification fails on a wrong signer,
commit, version, manifest or archive. This is a signed maintainer attestation,
not an independently certified SLSA build, a substitute for human approval,
or evidence for the separate unpublished npm package. The published alpha.4
release has not been retroactively signed. No SSH or Python dependency is
added to CSS consumers.

## Current status

The alpha.5 manual reviews are **not signed off**. A historical November 18, 2026 source-only audit in [accessibility-alpha5-review.md](accessibility-alpha5-review.md) recorded 165 inconclusive contrast elements at commit `70ec764`. That count is **not** a measurement of the current source head; intervening commits invalidate any assumption that it remains accurate.

Before freezing, run the pinned axe and browser checks on the exact candidate SHA, record every incomplete contrast target and adjudication, and separately capture actual zoom, assistive-technology and native high-contrast evidence. Run the catalog audit with `--catalog-mode source-alpha5` (the default); the published alpha.4 catalog mode is a separate measurement and does not certify the candidate. Update the review record with the SHA and audit date, **not** a copied historical count. Until manual reviews and brand clearance have evidenced approval, freezing alpha.5 remains blocked. The [commercial sale/download gates](https://github.com/dporkka/syntyr-css/blob/main/business/commercial-launch-gates.md) are separate and remain closed.
