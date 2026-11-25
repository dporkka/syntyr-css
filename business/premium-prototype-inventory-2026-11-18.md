# Premium prototype inventory snapshot — November 18, 2026

**Evidence, not release approval. NOT FOR SALE.** These numbers describe a
verified private source preview. They do not grant any premium license, authorize
checkout/download, certify accessibility, or freeze a customer release.

Private source repository: `dporkka/syntyr-console-kit`
Exact source commit: `aa2a28c6e000f4e839c0e3a642188446311c9c92`
Version: `0.1.0-preview`

| Prototype | Application screens | Website screens | Total distinct screen types | Three-theme page variants |
| --- | ---: | ---: | ---: | ---: |
| Console Kit (included in both) | 12 | 0 | 12 | 36 |
| Syntyr Pro | 25 | 0 | 25 | 75 |
| Syntyr Studio (includes Pro) | 25 | 17 | 42 | 126 |

The 17 Studio website types consist of 15 pages in three original fictional
website kits (six B2B SaaS, five professional services, four ecommerce)
plus two separate standalone product/checkout previews. The Pro 25 include
the 12 Console Kit screens and 13 additional operations/governance/developer
screens. Theme variants are not independent functional applications.

Verification on Gertrude against the exact private commit:

- `python3 tools/build_paid.py check --product syntyr-pro`: 104 exact source output files.
- `python3 tools/build_paid.py check --product syntyr-studio`: 156 exact source output files.
- `TMPDIR=/home/dporkka/syntyr-test-tmp GOTMPDIR=/home/dporkka/syntyr-test-tmp python3 -m unittest tests.test_paid_products tests.test_package_manifest -q`: 21 passing tests.
- `python3 tools/build_paid.py verify --product syntyr-pro --zip release/syntyr-pro-0.1.0-preview.zip`: verified 178 archive files; SHA-256 `d93f20c61d6cec2988b92d5ae8abb9fcf4e8738132feb01669c7f25668cbbb04`.
- `python3 tools/build_paid.py verify --product syntyr-studio --zip release/syntyr-studio-0.1.0-preview.zip`: verified 250 archive files; SHA-256 `721df26a50bf2ddc08a2bc6f77fc853f318b97ed089cf1159ff2354f80862ced`.

Initial test runs against default `/tmp` failed with `disk quota exceeded`;
setting the two temporary directory variables above resolved the environment
failure. Archive hashes are integrity inventories, **not publisher signatures**.

The public `metadata/commercial-offers.json` and `docs/products.html` are
updated to reflect this dated inventory snapshot. Their status remains
research-only and the proposed prices remain unchanged.

## Before a sale

1. Freeze a NEW exact source commit and rebuild/verify the final distributable;
   this preview snapshot is not the final release.
2. Resolve seller/trademark, source licensing, asset rights, tax/refund/support
   disclosures, and complete dated manual accessibility reviews.
3. Run hosted payment sandbox, entitlement, authenticated private fulfillment,
   refund/revocation and recovery tests against the final package.
4. Approve an operative customer archive format with an actual commercial
   license and safe private distribution; the current `-preview.zip` must
   remain blocked.
5. Reconcile public product claims against the final customer artifact and
   confirm independent approval before enabling paid checkout.
