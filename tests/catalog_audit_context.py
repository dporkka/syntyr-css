"""Keep developer-only catalog audits and follow-up screenshots on the same CSS release."""

CATALOG_PAGE = "docs/catalog.html"
CATALOG_STYLESHEETS = {
    "source-alpha5": "../dist/syntyr.all.css",
    "published-alpha4": "../site-releases/0.3.0-alpha.4/syntyr.all.css",
}


def select_catalog_context(page, mode: str) -> dict:
    """Select the release and wait for its stylesheet AND card filtering.

    Audit local file:// pages, not the hosted CDN. The catalog's JS initializes
    the published filter by default; merely navigating to its source HTML does
    not mean the candidate CSS remains active.
    """
    if mode not in CATALOG_STYLESHEETS:
        raise ValueError(f"Unknown catalog audit mode: {mode}")
    stylesheet = CATALOG_STYLESHEETS[mode]
    page.locator("#catalog-release-filter").select_option(mode)
    page.wait_for_function(
        """({mode, stylesheet}) => {
          const filter = document.getElementById('catalog-release-filter');
          const link = document.getElementById('catalog-framework-stylesheet');
          if (!filter || !link || filter.value !== mode ||
              link.getAttribute('href') !== stylesheet ||
              link.sheet?.href !== new URL(stylesheet, document.baseURI).href) return false;
          const cards = [...document.querySelectorAll('.catalog-card')];
          return cards.length > 0 && cards.every(card =>
            card.hidden === (mode === 'published-alpha4' &&
                             card.dataset.catalogAlpha4 !== 'true'));
        }""",
        arg={"mode": mode, "stylesheet": stylesheet},
        timeout=10000,
    )
    return {"mode": mode, "stylesheet": stylesheet}


def catalog_context_from_report(row: dict) -> dict | None:
    """Refuse ambiguous catalog reports rather than sampling another release."""
    if row.get("page") != CATALOG_PAGE:
        return None
    context = row.get("catalog_context")
    if not isinstance(context, dict):
        raise ValueError("Catalog report has no release context; rerun axe_audit.py with --catalog-mode")
    mode = context.get("mode")
    if not isinstance(mode, str) or mode not in CATALOG_STYLESHEETS or context.get("stylesheet") != CATALOG_STYLESHEETS[mode]:
        raise ValueError("Catalog report has an invalid release/stylesheet context; rerun the audit")
    return {"mode": mode, "stylesheet": CATALOG_STYLESHEETS[mode]}
