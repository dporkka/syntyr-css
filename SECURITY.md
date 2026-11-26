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

## Public repository confidentiality

This repository is public independently of the Cloudflare publishing allowlist.
Tracked business plans, specifications and pilot templates must be suitable for
public disclosure. Store confidential strategy, credentials, customer records
and identifying research notes in an access-controlled private workspace, never
in tracked source. In particular, keep real pilot data under the ignored
`business/private/` path or outside the checkout. An ignored path does not erase
files from existing Git history.

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
