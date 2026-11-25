"""Build an explicit public-only SYNTYR site for Cloudflare Workers Static Assets.

Pure stdlib, no Node dependencies, no browser JavaScript, no repo-root publishing.
"""
from __future__ import annotations

import argparse
from html import unescape as unescape_html
import hashlib
import json
import posixpath
import re
from urllib.parse import urlsplit
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile

if __package__:
    from .build import all_distributions, javascript_distributions
    from .build_shadcn_registry import generate as universal_registry_files
    from .build_playground_catalog import generate as playground_catalog, generate_inspection as playground_inspection
    from .build_blocks import build as blocks_gallery
    from .build_section_composer import build as section_catalog
    from .build_catalog_release import build_release_matrix, render_release_matrix, verify_catalog_annotations
    from .static_deploy import validate_site_url
else:
    from build import all_distributions, javascript_distributions
    from build_shadcn_registry import generate as universal_registry_files
    from build_playground_catalog import generate as playground_catalog, generate_inspection as playground_inspection
    from build_blocks import build as blocks_gallery
    from build_section_composer import build as section_catalog
    from build_catalog_release import build_release_matrix, render_release_matrix, verify_catalog_annotations
    from static_deploy import validate_site_url

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".cloudflare-public"
MARKER = ".syntyr-site-manifest.json"
SITE_URL = "https://syntyr-css.pages.dev"
# These pages are illustrative applications or an error response, not search
# landing pages. Their HTML remains publicly available and linkable.
NOINDEX_HTML = frozenset({
    "404.html", "examples/crm.html", "examples/saas.html", "examples/pricing.html", "examples/preset-preview.html",
    "examples/saas-admin-starter/index.html", "examples/saas-admin-starter/pipeline.html",
    "examples/saas-admin-starter/customers.html", "examples/saas-admin-starter/billing.html",
    "examples/resource-workspace.html", "examples/form-state-contracts.html", "examples/geo.html",
    "examples/permission-matrix.html",
    "examples/query-review.html",
    "examples/command-launcher.html",
    "examples/settings-billing.html",
    "examples/app-onboarding.html", "examples/app-team.html", "examples/app-notifications.html",
    "examples/app-integrations.html", "examples/app-security.html",
    "examples/design-benchmarks/marketing.html", "examples/design-benchmarks/crm.html",
    "examples/design-benchmarks/documentation.html",
    "examples/site-starters/saas-marketing/index.html",
    "examples/site-starters/saas-marketing/pricing/index.html",
    "examples/site-starters/saas-marketing/about/index.html",
    "examples/industry-sites/index.html",
    "examples/industry-sites/field-service/index.html",
    "examples/industry-sites/field-service/services.html",
    "examples/industry-sites/professional-practice/index.html",
    "examples/industry-sites/professional-practice/services.html",
    "examples/industry-sites/saas-developer/index.html",
    "examples/industry-sites/saas-developer/pricing.html",
    "examples/industry-sites/saas-developer/docs.html",
    "docs/htmx-playground.html",  # Interactive app demo, not an SEO landing page.
})
CANONICAL_LINK = re.compile(r'<link\s+rel="canonical"[^>]*>', re.IGNORECASE)
ROBOTS_META = re.compile(r'<meta\s+name="robots"[^>]*>', re.IGNORECASE)


def canonical_path(name: str, *, portable: bool = False) -> str:
    """Match Cloudflare Pages' 200-status clean URLs (not .html redirect URLs)."""
    if name == "index.html":
        return "/"
    if name.endswith("/index.html"):
        return "/" + name.removesuffix("index.html")
    return "/" + (name if portable else name.removesuffix(".html"))


def add_seo_metadata(files: dict[str, bytes], site_url: str = SITE_URL, *, portable: bool = False) -> None:
    """Build-time-only SEO: preserve readable sources and avoid browser JS."""
    for name, data in tuple(files.items()):
        if not name.endswith(".html"):
            continue
        html = data.decode("utf-8")
        if site_url != SITE_URL:
            # Replace only first-party machine-readable metadata. Preserve
            # ordinary content, public source links and external destinations.
            html = re.sub(
                r'<(?:meta|link)\b[^>]*>',
                lambda match: match.group().replace(SITE_URL, site_url),
                html, flags=re.IGNORECASE,
            )
            html = re.sub(
                r'<script\b[^>]*\btype="application/ld\+json"[^>]*>.*?</script>',
                lambda match: match.group().replace(SITE_URL, site_url),
                html, flags=re.IGNORECASE | re.DOTALL,
            )
        if name in NOINDEX_HTML:
            if not ROBOTS_META.search(html):
                html = html.replace("</head>", '  <meta name="robots" content="noindex,follow">\n</head>', 1)
            # Excluded pages should not claim canonical index URLs.
            html = CANONICAL_LINK.sub("", html)
        else:
            url = site_url + canonical_path(name, portable=portable)
            tag = f'<link rel="canonical" href="{url}">'
            if CANONICAL_LINK.search(html):
                html = CANONICAL_LINK.sub(tag, html, count=1)
            else:
                html = html.replace("</head>", f"  {tag}\n</head>", 1)
            # Existing OG URLs may use Cloudflare clean paths. Portable sites
            # require a directly servable .html URL, even with the default origin.
            if portable:
                def replace_existing_og_url(tag):
                    raw = tag.group()
                    if not re.search(r"""\bproperty\s*=\s*(["'])og:url\1""", raw, flags=re.I):
                        return raw
                    content = re.search(r"""\bcontent\s*=\s*(["']).*?\1""", raw, flags=re.I | re.S)
                    if content is None:
                        return raw[:-1] + f' content="{url}">'
                    return raw[:content.start()] + f'content="{url}"' + raw[content.end():]

                html = re.sub(r"""<meta\b(?:[^>"']|"[^"]*"|'[^']*')*>""",
                              replace_existing_og_url, html, flags=re.I)
            # Author pages can include Open Graph data already; don't duplicate it.
            if 'property="og:url"' not in html:
                html = html.replace("</head>", f'  <meta property="og:url" content="{url}">\n</head>', 1)
            if 'property="og:title"' not in html:
                title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
                if title:
                    from html import escape
                    html = html.replace("</head>",
                                        f'  <meta property="og:title" content="{escape(unescape_html(title.group(1)), quote=True)}">\n</head>', 1)
            if 'property="og:description"' not in html:
                description = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.IGNORECASE)
                if description:
                    html = html.replace("</head>",
                                        f'  <meta property="og:description" content="{description.group(1)}">\n</head>', 1)
            schema = None
            if name == "index.html":
                schema = {
                    "@context": "https://schema.org",
                    "@type": "SoftwareSourceCode",
                    "name": "Syntyr CSS",
                    "description": "MIT-licensed CSS-first interface system for SaaS dashboards and semantic HTML.",
                    "url": url,
                    "codeRepository": "https://github.com/dporkka/syntyr-css",
                    "license": "https://opensource.org/licenses/MIT",
                    "programmingLanguage": "CSS",
                }
            elif name.startswith("docs/"):
                title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
                label = unescape_html(title.group(1)).removesuffix(" — Syntyr CSS docs") if title else "Documentation"
                items = [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": site_url + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Documentation", "item": site_url + "/docs/"},
                ]
                if name not in {"docs/index.html"}:
                    items.append({"@type": "ListItem", "position": 3, "name": label, "item": url})
                schema = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}
            if schema and 'type="application/ld+json"' not in html:
                # Escape markup sentinels even though data originates in checked-in source.
                json_text = json.dumps(schema, ensure_ascii=True, separators=(",", ":")).replace("<", r"\u003c")
                html = html.replace("</head>", f'  <script type="application/ld+json">{json_text}</script>\n</head>', 1)
        files[name] = html.encode("utf-8")



# Enforced CSP blocks third-party/inline scripts. Some published docs use
# inline presentation styles, so style-src retains unsafe-inline until those
# styles are migrated and validated across the browser matrix. Keep the
# sandboxed playground's about:srcdoc preview working with frame-src 'self'.
# These headers protect the static docs; they are NOT application security
# middleware and do not follow the distributed CSS into consumer applications.
HEADERS = """/*
  Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self' https://github.com/dporkka/syntyr-css/issues; upgrade-insecure-requests
  Strict-Transport-Security: max-age=31536000
  Permissions-Policy: camera=(), microphone=(), geolocation=(), usb=()
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin

/
  Cache-Control: public, max-age=0, must-revalidate

/*.html
  Cache-Control: public, max-age=0, must-revalidate

/docs/*
  Cache-Control: public, max-age=0, must-revalidate

/docs/*.md
  X-Robots-Tag: noindex
  Content-Type: text/markdown; charset=utf-8

/README.md
  X-Robots-Tag: noindex
  Content-Type: text/markdown; charset=utf-8

/DESIGN.md
  X-Robots-Tag: noindex
  Content-Type: text/markdown; charset=utf-8

/ARCHITECTURE.md
  X-Robots-Tag: noindex
  Content-Type: text/markdown; charset=utf-8

/agents/syntyr/SKILL.md
  X-Robots-Tag: noindex
  Content-Type: text/markdown; charset=utf-8

/llms.txt
  X-Robots-Tag: noindex

/llms-full.txt
  X-Robots-Tag: noindex

/examples/*
  Cache-Control: public, max-age=0, must-revalidate

/blog/*
  Cache-Control: public, max-age=0, must-revalidate

/tools/*
  Cache-Control: public, max-age=0, must-revalidate

/blog/rss.xml
  Content-Type: application/rss+xml; charset=utf-8

/dist/*
  Cache-Control: public, max-age=0, must-revalidate
  Access-Control-Allow-Origin: *

/registry/*
  Cache-Control: public, max-age=0, must-revalidate
  Access-Control-Allow-Origin: *

/v/*
  Cache-Control: public, max-age=31536000, immutable
  Access-Control-Allow-Origin: *

/metadata/component-gallery.v1.json
  Access-Control-Allow-Origin: *

/metadata/section-composer.v1.json
  Access-Control-Allow-Origin: *

/_assets/css/*
  Cache-Control: public, max-age=31536000, immutable
"""


LINK_TAG = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
REL_ATTR = re.compile(r"""\brel\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)
HREF_ATTR = re.compile(r"""\bhref\s*=\s*(['"])(.*?)\1""", re.IGNORECASE)


def immutable_site_css(files: dict[str, bytes]) -> None:
    """Rewrite only shipped HTML stylesheet references to content-hashed copies.

    Original /dist and /v assets remain intact for consumers. The site HTML
    references an immutable hashed copy of each linked local stylesheet.
    Other source links, external URLs, JS, and Markdown examples are unchanged.
    """
    derived: dict[str, bytes] = {}
    for filename, payload in tuple(files.items()):
        if not filename.endswith(".html"):
            continue
        def replace_link(match: re.Match) -> str:
            tag = match.group(0)
            rel = REL_ATTR.search(tag)
            href = HREF_ATTR.search(tag)
            if not rel or not href or "stylesheet" not in rel.group(2).lower().split():
                return tag
            parsed = urlsplit(href.group(2))
            if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
                return tag
            # The HTML may be at the site root or in an examples/docs folder.
            path = posixpath.normpath(
                posixpath.join(posixpath.dirname(filename), parsed.path.lstrip("/"))
                if not parsed.path.startswith("/")
                else parsed.path.lstrip("/"))
            if path not in files or not path.endswith(".css"):
                return tag
            css = files[path]
            if re.search(rb"@import\b|url\s*\(", css, re.IGNORECASE):
                raise ValueError(f"Cannot relocate CSS with imports/relative URLs: {path}")
            dest = f"_assets/css/{hashlib.sha256(css).hexdigest()}.css"
            existing = derived.get(dest)
            if existing is not None and existing != css:
                raise ValueError(f"Hash collision: {dest}")
            derived[dest] = css
            return tag[:href.start(2)] + "/" + dest + tag[href.end(2):]

        html = payload.decode("utf-8")
        rewritten = LINK_TAG.sub(replace_link, html)
        files[filename] = rewritten.encode("utf-8")
    files.update(derived)


PUBLIC_DOCS = (
    "ai-quickstart.md", "agent-integration.md", "design-principles.md", "app-screens.md",
    "media-entertainment.md",
    "accessibility.md", "accessibility-alpha5-review.md", "api-stability.md", "cloudflare-hosting.md", "nulang-cloud-hosting.md",
    "release-freeze.md", "launch-status.md", "component-authoring.md", "components.md", "data-tables.md", "data-grid.md",
    "console-kit.html", "component-recipes.md", "email-components.md", "design-research-linear-resend.md", "design-reference-matrix.md", "premium-compositions.md", "visual-composition.md",
    "console-kit.html", "component-recipes.md", "design-research-linear-resend.md", "premium-compositions.md", "visual-composition.md",
    "faq.md", "compare.md", "compare-tailwind.md", "compare-bootstrap.md", "compare-shadcn.md",
    "compare-daisyui.md", "compare-pico.md", "compare-native-css.md",
    "distribution.md", "native-patterns.md", "native-workflows.md", "semantic-components.md", "composition-adoption.md", "from-pico.md", "package-managers.md", "docs.css", "reference-search.js", "guides.html", "how-to.html", "how-to.css", "how-to.js", "starter-wizard.html", "starter-wizard.mjs", "catalog.html", "catalog.css", "catalog.js",
    "blocks.html", "blocks.css", "blocks.js", "blocks-assets.css", "blocks-guide.md", "headless-interactions.md", "framework-integrations.md", "htmx-components.md", "htmx-playground.html", "mobile-frameworks.md",
    "geometry-terminal.md", "native-browser-apis.md", "interaction-recipes.md", "dropdowns.md", "radix-integration.md", "visual-intensity.md", "performance-and-polish.md",
    "performance-validation.md", "progressive-enhancement.md", "progressive-loading.md", "live-performance-audit.md",
    "index.html", "design-resources.html", "animation.md", "clipboard.md", "lit-integration.md", "playground.html", "playground.css", "playground.js", "playground-catalog.js", "playground-design-inspection.js", "playground-snippet.js", "playground-editor.js", "playground-editor.licenses.txt", "page-builder-guide.md", "page-builder.html",  "page-builder.css", "page-builder.js", "page-builder-model.mjs", "site-builder-model.mjs", "page-builder-zip.mjs", "page-builder-starters.mjs", "page-builder-site-kits.mjs", "page-builder-section-picker.mjs",
    "form-builder.html", "form-builder.css", "form-builder.js", "form-builder-model.mjs",
    "editor-integration.md", "recipes.md", "saas-cli-business.md", "products.html", "pro.html", "studio.html", "integration-services.html",
    "cms-integration.md", "site-generator-decision.md", "static-site-generators.md", "site-builders.md", "tailwind-research.md", "tailwind-alternative.html",
    "wordpress.md", "shopify.md", "wix.md", "webflow.md", "framer.md", "squarespace.md", "ghost.md", "hubspot.md", "drupal.md", "joomla.md", "carrd.md", "duda.md", "tilda.md",
    "theme-customization.md", "theme-editor.html", "theme-editor.js", "symbols.md", "ascii-effects.md",
    "vertigo-integration.md", "rust-saas-integration.md", "viz.md", "geo.md",
)


def source_files(site_url: str = SITE_URL, *, include_cloudflare_headers: bool = True) -> dict[str, bytes]:
    site_url = validate_site_url(site_url)
    if __package__:
        from .build_interaction_catalog import load_catalog, render_catalog
    else:
        from build_interaction_catalog import load_catalog, render_catalog
    if (ROOT / "docs/interaction-recipes.md").read_text(encoding="utf-8") != render_catalog(load_catalog()):
        raise ValueError("Stale interaction recipe catalog: run scripts/build_interaction_catalog.py")
    # Both galleries are generated from reviewed, MIT-owned source fragments.
    if (ROOT / "docs/blocks.html").read_text(encoding="utf-8") != blocks_gallery():
        raise ValueError("Stale blocks gallery: run scripts/build_blocks.py")
    if (ROOT / "metadata/section-composer.v1.json").read_bytes() != section_catalog():
        raise ValueError("Stale section composer library: run scripts/build_section_composer.py")
    # Published-release copy targets must be backed by the frozen CSS snapshot.
    release_matrix = build_release_matrix()
    if ((ROOT / "metadata/catalog-release-compatibility.v1.json").read_text(encoding="utf-8")
            != render_release_matrix(release_matrix)
            or not verify_catalog_annotations(release_matrix)):
        raise ValueError("Stale release coverage: run scripts/build_catalog_release.py")
    # Fail closed if either gallery changes without updating the playground.
    if (ROOT / "docs/playground-catalog.js").read_text(encoding="utf-8") != playground_catalog():
        raise ValueError("Stale playground examples: run scripts/build_playground_catalog.py")
    if (ROOT / "docs/playground-design-inspection.js").read_text(encoding="utf-8") != playground_inspection():
        raise ValueError("Stale playground inspection: run scripts/build_playground_catalog.py")
    files: dict[str, bytes] = {}
    paths = [
        ROOT / "index.html",
        ROOT / "assets/syntyr-mark.svg",
        ROOT / "assets/og-syntyr.png",
        ROOT / "assets/readme/operations-console.png",
        ROOT / "assets/readme/flagship-studio.png",
        ROOT / "assets/readme/flagship-noir.png",
        ROOT / "assets/gallery-horizon.svg",
        ROOT / "assets/gallery-architecture.svg",
        ROOT / "assets/gallery-signal.svg",
        ROOT / "assets/gallery-botanical.svg",

        ROOT / "404.html",
        ROOT / "LICENSE",
        ROOT / "README.md",
        ROOT / "DESIGN.md",
        ROOT / "ARCHITECTURE.md",
        ROOT / "llms.txt",
        ROOT / "llms-full.txt",
        ROOT / "metadata/components.json",
        ROOT / "metadata/component-gallery.v1.json",
        ROOT / "metadata/interaction-recipes.json",
        ROOT / "metadata/catalog-release-compatibility.v1.json",
        ROOT / "metadata/section-composer.v1.json",
        # Public, generated, dependency-free mobile design tokens and copy-owned source.
        ROOT / "metadata/mobile/syntyr.tokens.json",
        ROOT / "integrations/react-native/tokens.ts",
        ROOT / "integrations/react-native/styles.ts",
        ROOT / "examples/react-native/App.tsx",
        ROOT / "metadata/commercial-offers.json",
        ROOT / "agents/syntyr/SKILL.md",
        ROOT / "terminal/palettes.json",
        *(
            ROOT / "metadata" / name
            for name in (
                "syntyr-api.json", "syntyr-contract.json", "css-contract.v1.json",
                "syntyr.html-custom-data.json",
                "syntyr.css-custom-data.json", "syntyr.code-snippets",
            )
        ),
        ROOT / "integrations/vertigo/admin.css",
        ROOT / "integrations/radix/states.css",
        ROOT / "integrations/headless/interactions.css",
        ROOT / "integrations/htmx/syntyr.htmx.css",
        ROOT / "examples/ansi_cli.py",
        ROOT / "examples/animation-demo.mjs",
        ROOT / "examples/copy-demo.mjs",
        ROOT / "examples/resizable-workspace.mjs",
    ]
    # Explicit per-file allowlist: new repo files are private until reviewed.

    public_examples = (
        "business.html", "form-state-contracts.html",
        "media-entertainment.html", "email.html", "common-ui.html", "platform-embed.html", "console.html", "form-composition.html", "geometry-terminal.html", "intensity-geometry.html", "landing.html", "semantic-starter.html",
        "minimalist-patterns.html", "design-states.html", "native-elements.html", "semantic-compositions.html", "native-interactions.html", "native-recipes.html", "resource-outline.html", "query-review.html", "command-launcher.html", "command-launcher.mjs", "native-choice-filter-list.html", "composition-adoption.html", "native-apis.html", "dropdowns.html", "performance-first.html",
        "operations-console.css", "operations-console.html", "pricing.html", "workflow-steps.html", "settings-billing.html", "settings-billing.css",
        "app-screens.css", "app-onboarding.html", "app-team.html", "app-notifications.html",
        "app-integrations.html", "app-security.html",
        "flagship.css", "flagship-studio.html", "flagship-noir.html", "flagship-grid.html",
        "rust-axum/README.md", "resources.html", "data-tables.html", "saas.html", "preset-preview.html", "saas-workflows.html",
        "saas-admin-starter/index.html", "saas-admin-starter/pipeline.html",
        "saas-admin-starter/customers.html", "saas-admin-starter/billing.html",
        "saas-admin-starter/styles.css", "saas-admin-starter/README.md", "enterprise-compositions.html", "permission-matrix.html", "permission-matrix.css", "crm.html", "resource-workspace.html", "native-workflows.html", "file-lifecycle.html", "resizable-workspace.html", "operation-revisions.html", "saas-workflows.css", "workflow-operations.html", "workflow-operations.css", "premium-compositions.html",
        "terminal.html", "themes.html", "vertigo-admin.html", "vertigo-resource-workflow.html", "vertigo-resource-workflow.css", "symbols.html", "ascii.html", "ascii-heroes.html",
        "viz.html", "geo.html", "data-grid.html", "animation.html", "copy.html",
        "design-benchmarks/marketing.html", "design-benchmarks/crm.html",
        "design-benchmarks/documentation.html", "design-benchmarks/benchmark.css",
        "site-starters/saas-marketing/index.html", "site-starters/saas-marketing/pricing/index.html",
        "site-starters/saas-marketing/about/index.html", "site-starters/saas-marketing/assets/site.css",
        # Reviewed MIT site starters only; do not scan arbitrary template directories.
        "industry-sites/index.html", "industry-sites/site.css",
        "industry-sites/field-service/index.html", "industry-sites/field-service/services.html",
        "industry-sites/professional-practice/index.html", "industry-sites/professional-practice/services.html",
        "industry-sites/saas-developer/index.html", "industry-sites/saas-developer/pricing.html",
        "industry-sites/saas-developer/docs.html",
    )
    # Import the canonical distribution registry rather than maintaining
    # a second list that can silently omit new CSS entrypoints.
    public_css = tuple(all_distributions())
    # Independent SEO landing pages, no server-side URL scanning or npm dependencies.
    public_tools = (
        "index.html", "color-contrast-checker.html", "css-theme-generator.html",
        "css-clamp-generator.html", "responsive-design-tester.html",
        "site.css", "logic.mjs", "site.mjs",
        "ascii-playground.html", "ascii-playground.css", "ascii-playground.mjs", "ascii-logic.mjs",
    )
    paths.extend(ROOT / "tools" / name for name in public_tools)
    # Self-hosted, exact-version HTMX; docs-only, excluded from npm and core bundles.
    paths.extend(ROOT / "docs/vendor" / name for name in
                 ("htmx-2.0.11.min.js", "htmx-LICENSE.txt"))
    paths.extend(ROOT / "docs" / name for name in PUBLIC_DOCS)
    paths.extend(ROOT / "docs" / (name.removesuffix(".md") + ".html")
                 for name in PUBLIC_DOCS if name.endswith(".md"))
    paths.append(ROOT / "docs/reference.html")
    # Only approved raster captures from the privately authored Console Kit.
    # Never publish premium HTML, CSS, build output, or other private assets.
    public_preview_images = (
        "studio-overview.webp",
        "grid-resources.webp",
        "noir-billing.webp",
        "studio-editor.webp",
        "studio-settings.webp",
        "grid-detail.webp",
        "noir-team.webp",
        "grid-sign-in.webp",
        # Product-specific static marketing screenshots from private, original source.
        # Screenshots are public; never distribute the premium HTML/CSS prototypes.
        "pro-work-orders-studio.webp",
        "studio-saas-home.webp",
    )
    paths.extend(ROOT / "docs/previews" / name for name in public_preview_images)
    paths.extend(ROOT / "examples" / name for name in public_examples)
    # Public editorial HTML, styling and RSS. Other blog sources stay private.
    paths.extend(ROOT / "blog" / name for name in (
        "index.html", "blog.css", "rss.xml", "css-first-design-systems.html",
        "accessible-native-html.html", "landing-page-ui-blocks.html",
    ))
    paths.extend(ROOT / "dist" / name for name in public_css)
    paths.extend(ROOT / "dist" / name for name in javascript_distributions())
    # Only known generated MIT universal-item JSON; never scan private products.
    registry_expected = universal_registry_files()
    paths.extend(ROOT / "registry" / name for name in registry_expected)
    for path in paths:
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"Not a regular repo file: {path}")
        data = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("registry/"):
            expected = registry_expected.get(relative.removeprefix("registry/"))
            if data != expected:
                raise ValueError(f"Out-of-date generated registry item: {relative}")
        files[relative] = data

    releases = ROOT / "site-releases"
    manifest = json.loads((releases / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Invalid release manifest")
    for version, assets in manifest.items():
        if not version or "/" in version or version in {".", ".."} or not isinstance(assets, dict):
            raise ValueError(f"Invalid release version: {version!r}")
        for filename, expected_hash in assets.items():
            relative = PurePosixPath(filename)
            if (relative.is_absolute() or ".." in relative.parts
                    or not filename.startswith("syntyr") or relative.suffix != ".css"
                    or len(relative.parts) != 1):
                raise ValueError(f"Invalid release filename: {filename!r}")
            path = releases / version / filename
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Missing immutable release asset: {path}")
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != expected_hash:
                raise ValueError(f"Modified immutable release asset: {path}")
            files[f"v/{version}/{filename}"] = data

    # Keep the sitemap confined to HTML that is useful as a search result.
    # Cloudflare Pages redirects *.html -> clean paths, so only list final 200 URLs.
    from xml.sax.saxutils import escape as escape_xml
    add_seo_metadata(files, site_url, portable=not include_cloudflare_headers)
    indexable = sorted(
        site_url + canonical_path(name, portable=not include_cloudflare_headers)
        for name in files if name.endswith(".html") and name not in NOINDEX_HTML
    )
    files["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                            + "".join(f"  <url><loc>{escape_xml(url)}</loc></url>\n"
                                      for url in indexable)
                            + "</urlset>\n").encode("utf-8")
    files["robots.txt"] = (f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n").encode("utf-8")
    immutable_site_css(files)
    if include_cloudflare_headers:
        # Only the live demo API invokes Pages Functions. Keep static traffic free.
        files["_routes.json"] = (json.dumps({"version": 1, "include":
                                        ["/api/htmx-demo/*"], "exclude": []},
                                        separators=(",", ":")) + "\n").encode("utf-8")
        files["_headers"] = HEADERS.encode("utf-8")
    return files


def build(out: Path, check: bool, *, site_url: str = SITE_URL,
          include_cloudflare_headers: bool = True) -> int:
    out = out.resolve()
    if out == ROOT or out in ROOT.parents:
        raise ValueError("Refusing to publish into the source root or its parents")
    files = source_files(site_url, include_cloudflare_headers=include_cloudflare_headers)
    index = {path: hashlib.sha256(data).hexdigest() for path, data in sorted(files.items())}
    files[MARKER] = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if check:
        existing = {p.relative_to(out).as_posix(): p.read_bytes()
                    for p in out.rglob("*") if p.is_file()} if out.is_dir() else {}
        if existing != files:
            print("STALE Cloudflare publish directory", file=sys.stderr)
            return 1
        print(f"OK Cloudflare publish directory: {len(files)} allowlisted files")
        return 0
    if out.exists():
        if out.is_symlink() or not (out / MARKER).is_file():
            raise ValueError(f"Refusing to overwrite a non-SYNTYR output directory: {out}")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for relative, data in files.items():
        destination = out / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    print(f"BUILT Cloudflare static site: {len(files)} files at {out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--site-url", default=SITE_URL, help="Canonical HTTPS origin for SEO metadata")
    parser.add_argument("--portable", action="store_true", help="Omit Cloudflare-specific _headers for other static hosts")
    args = parser.parse_args()
    return build(args.output, args.check, site_url=args.site_url,
                 include_cloudflare_headers=not args.portable)


if __name__ == "__main__":
    sys.exit(main())
