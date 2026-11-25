"""Opt-in local automated WCAG-tagged audit, using a developer-supplied axe-core JS.

The audit script is never loaded by the site or library. Install Playwright in
a temporary test environment and supply a local axe-core script, e.g.:

  curl -fsSL https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.3/axe.min.js -o /tmp/axe.min.js
  python3 tests/axe_audit.py --axe-file /tmp/axe.min.js

Automated checks do not replace screen reader, keyboard or zoom verification.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import os
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "docs/index.html", "docs/catalog.html", "docs/blocks.html", "docs/guides.html", "docs/design-principles.html", "examples/console.html",
          "examples/resources.html", "examples/pricing.html", "docs/console-kit.html",
         "examples/saas.html", "examples/settings-billing.html",
         "examples/app-onboarding.html", "examples/app-team.html", "examples/app-notifications.html",
         "examples/app-integrations.html", "examples/app-security.html", "examples/business.html", "examples/terminal.html",
         "examples/geometry-terminal.html",
         "examples/operations-console.html", "examples/themes.html",
         "examples/vertigo-admin.html", "examples/vertigo-resource-workflow.html", "examples/saas-workflows.html", "examples/data-tables.html", "examples/resource-workspace.html", "examples/native-workflows.html", "examples/crm.html", "examples/minimalist-patterns.html",
         "examples/design-states.html", "examples/symbols.html", "examples/native-elements.html",
         "examples/flagship-studio.html", "examples/flagship-noir.html", "examples/flagship-grid.html",
         "examples/semantic-starter.html", "examples/native-apis.html", "examples/dropdowns.html", "examples/workflow-steps.html", "examples/enterprise-compositions.html", "examples/premium-compositions.html", "examples/operation-revisions.html",
)

def normalize_findings(page_path: str, result: dict) -> dict:
    """Keep actionable axe targets for manual review without shipping a browser tool."""
    findings = {"page": page_path, "violations": [], "incomplete": []}
    for category in ("violations", "incomplete"):
        for rule in result.get(category, []):
            for node in rule.get("nodes", []):
                findings[category].append({
                    "page": page_path,
                    "rule": rule["id"],
                    "impact": rule.get("impact"),
                    "help": rule.get("help"),
                    "selector": node.get("target", []),
                    "html": node.get("html"),
                    "failure_summary": node.get("failureSummary"),
                })
    return findings


def summarize_findings(pages: list[dict]) -> dict:
    """Count affected elements, not merely axe rule instances.

    An axe incomplete rule can contain dozens of targets, none of which
    should be silently counted as a verified pass or a proven violation.
    """
    incomplete = [node for page in pages for node in page['incomplete']]
    return {
        'pages': len(pages),
        'confirmed_violation_nodes': sum(len(page['violations']) for page in pages),
        'incomplete_nodes': len(incomplete),
        'incomplete_rules': dict(sorted(Counter(node['rule'] for node in incomplete).items())),
        'incomplete_by_page': {
            page['page']: len(page['incomplete'])
            for page in pages if page['incomplete']
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--axe-file", type=Path, required=True)
    parser.add_argument("--report", type=Path, help="write actionable JSON findings for manual review")
    args = parser.parse_args()
    if not args.axe_file.is_file():
        parser.error(f"Missing local axe-core script: {args.axe_file}")
    exe = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
           or shutil.which("chromium") or shutil.which("chromium-browser"))
    kwargs = {"headless": True}
    if exe:
        kwargs.update(executable_path=exe, args=["--no-sandbox"])
    from playwright.sync_api import sync_playwright  # developer-only dependency
    violations = 0
    manual_review = 0
    findings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**kwargs)
        for path in PAGES:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto((ROOT / path).as_uri())
            page.add_script_tag(path=str(args.axe_file.resolve()))
            result = page.evaluate("""async () => axe.run(document, {
                runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa'] }
            })""")
            findings.append(normalize_findings(path, result))
            count = len(result["violations"])
            incomplete = len(result["incomplete"])
            violations += count
            manual_review += incomplete
            print(f"{path}: {count} automated violations, {incomplete} incomplete checks")
            for item in result["violations"]:
                print(f"  {item['impact']} {item['id']}: " +
                      ", ".join(str(n["target"]) for n in item["nodes"][:4]))
            page.close()
        browser.close()
    summary = summarize_findings(findings)
    if args.report:
        args.report.write_text(json.dumps({"schema_version": 1, "summary": summary, "pages": findings}, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE manual review targets: {args.report}")
    print(f"TOTAL: {violations} confirmed violation rules, "
          f"{summary['confirmed_violation_nodes']} confirmed violation nodes, "
          f"{manual_review} incomplete rule results, "
          f"{summary['incomplete_nodes']} inconclusive element targets requiring review")
    return int(bool(violations))


if __name__ == "__main__":
    sys.exit(main())
