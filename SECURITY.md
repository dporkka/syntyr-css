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

Security reporting is not an alternative to the separate manual
accessibility release checks in
[docs/accessibility-alpha5-review.md](docs/accessibility-alpha5-review.md).

## Credential history review

Maintainers can run `sh scripts/audit_repository_secrets.sh` with an installed
Gitleaks binary after fetching full Git history. The manual/tag Woodpecker
pilot uses a checksum-pinned official Gitleaks release. It refuses a shallow
checkout, suppresses secret values from logs, and uses only exact historical
fingerprints for reviewed false positives (one example authorization
placeholder and four generated registry content digests). Do not broadly
exclude file paths or normalize new findings into the ignore file without
checking the underlying content. The scan covers the checked-out commit's
ancestry, not arbitrary other branches, remote services or untracked secrets.
A finding requires private review and, for genuine credentials, revocation
and rotation; deleting a file cannot invalidate an exposed credential.
