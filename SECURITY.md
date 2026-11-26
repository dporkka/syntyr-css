# Security policy

Syntyr CSS is an experimental, MIT-licensed CSS-first library. The published
v0.3.0-alpha.4 distribution is an immutable prerelease; the repository's
alpha.5 candidate is **unreleased**. Neither is a certified security or
accessibility guarantee.

## Report a vulnerability privately

Use this repository's **Security** tab on GitHub and select **Report a
vulnerability**. GitHub private vulnerability reporting is enabled for this
repository. Do not disclose a working exploit, sensitive user data, or
credentials in a public issue or pull request.

Include a minimal reproduction, affected version or commit, relevant
browser/framework when applicable, suspected impact, and whether the report
concerns a distributed CSS asset or an optional example, development tool,
or integration. Only test systems and accounts you are authorized to use.

For non-security defects, use ordinary GitHub issues.

## Scope and handling

- The free CSS runtime requires no JavaScript, npm packages or remote fonts,
  but optional development and example dependencies require separate review.
- CSS injection, unsafe sample markup, supply-chain issues, accidental file
  exposure and malicious asset loading may still be security concerns.
- Maintain pinned and reproducible distributed assets. Do not modify an
  immutable released file in place; publish a new version for fixes.
- Security reports are triaged according to reproducibility and impact.
  There is no published response-time SLA or security-support commitment for
  the experimental prereleases.
- Coordinate public disclosure through the private report where practical,
  allowing fixes and mitigation guidance to be prepared first.

## Optional dependency advisory inventory

Run `python3 scripts/audit_non_npm_dependencies.py` from the repository root
before candidate release approval. The manual/tag Woodpecker pilot queries
OSV for the public Rust `Cargo.lock`, Go example `go.sum`, and pinned Python
`requirements-docs.txt`. Only package names and versions are submitted; no
source code, secrets, or repository credentials are sent. The script fails
on advisory matches or incomplete responses. New inventories must be added
explicitly (the Git-tracked coverage test guards against omissions).

Go checksum entries may include versions not selected in a build; RustSec
also reports maintenance notices. A match requires upstream and reachability
review, not automatic severity or a claim that CSS users are affected. The
pilot does not scan the Go compiler/standard library, installed toolchains,
CI images or secrets. Verify runner egress before treating it as a required
pull-request gate. Review new toolchain advisories separately.

Security reporting is not an alternative to the separate manual
accessibility release checks in
[docs/accessibility-alpha5-review.md](docs/accessibility-alpha5-review.md).

## Credential history review

Maintainers can run `sh scripts/audit_repository_secrets.sh` with an installed
Gitleaks binary after fetching full Git history. The manual/tag Woodpecker
pilot uses a checksum-pinned official Gitleaks release. It refuses a shallow
checkout, suppresses secret values from logs, and uses only exact historical
fingerprints for reviewed false positives (one example authorization
placeholder, its two merge-patch repetitions, and four generated registry
content digests). The scan includes merge patches without limiting ancestry
traversal to first parents. Do not broadly
exclude file paths or normalize new findings into the ignore file without
checking the underlying content. The scan covers the checked-out commit's
ancestry, not arbitrary other branches, remote services or untracked secrets.
A finding requires private review and, for genuine credentials, revocation
and rotation; deleting a file cannot invalidate an exposed credential.
