"""Regression contracts for the public site's browser and build security boundaries."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SecurityHardeningTests(unittest.TestCase):
    def test_cloudflare_site_enforces_minimum_security_policy(self):
        from scripts.build_cloudflare_site import source_files
        headers = source_files()["_headers"].decode("utf-8")
        # A global /* rule must precede cache-specific per-path rules.
        rule, _, _ = headers.partition("\n\n")
        self.assertEqual(rule.splitlines()[0], "/*")
        fields = {}
        for line in rule.splitlines()[1:]:
            name, sep, value = line.strip().partition(":")
            self.assertTrue(sep, line)
            self.assertNotIn(name.lower(), fields, "Duplicate global header")
            fields[name.lower()] = value.strip()

        csp = fields["content-security-policy"]
        directives = {}
        for directive in csp.split(";"):
            tokens = directive.split()
            if not tokens:
                continue
            self.assertNotIn(tokens[0], directives)
            directives[tokens[0]] = tokens[1:]

        for directive, sources in {
            "default-src": ["'none'"],
            "base-uri": ["'none'"],
            "object-src": ["'none'"],
            "frame-ancestors": ["'none'"],
            "script-src": ["'self'"],
            "connect-src": ["'self'"],
            "form-action": ["'self'", "https://github.com/dporkka/syntyr-css/issues"],
            # The documentation playground uses an about:srcdoc iframe.
            "frame-src": ["'self'"],
            "style-src": ["'self'", "'unsafe-inline'"],
        }.items():
            self.assertEqual(directives[directive], sources, directive)
        self.assertNotIn("'unsafe-inline'", directives["script-src"])
        self.assertNotIn("'unsafe-eval'", directives["script-src"])
        self.assertEqual(fields["x-frame-options"], "DENY")
        self.assertEqual(fields["x-content-type-options"], "nosniff")
        self.assertTrue(fields["strict-transport-security"].startswith("max-age=31536000"))
        policy = fields["permissions-policy"]
        for feature in ("camera=()", "microphone=()", "geolocation=()", "usb=()"):
            self.assertIn(feature, policy)
        self.assertIn("Referrer-Policy: strict-origin-when-cross-origin", headers)
        self.assertIn("Access-Control-Allow-Origin: *", headers,
                      "The public CSS CDN must remain cross-origin consumable")

    def test_external_htmx_example_has_subresource_integrity(self):
        html = (ROOT / "examples/htmx.html").read_text(encoding="utf-8")
        tag = re.search(r'<script\s+[^>]*src="https://unpkg\.com/htmx\.org@2\.0\.8/dist/htmx\.min\.js"[^>]*>', html)
        self.assertIsNotNone(tag)
        self.assertIn('integrity="sha384-/TgkGk7p307TH7EXJDuUlgG3Ce1UVolAOFopFekQkkXihi5u/6OCvVKyz1W+idaz"', tag.group())
        self.assertIn('crossorigin="anonymous"', tag.group())

    def test_playground_srcdoc_allows_only_the_host_origin_for_styles(self):
        html = (ROOT / "docs/playground.html").read_text(encoding="utf-8")
        js = (ROOT / "docs/playground.js").read_text(encoding="utf-8")
        self.assertIn('sandbox="allow-same-origin"', html)
        self.assertNotIn('sandbox="allow-same-origin allow-scripts"', html)
        self.assertIn('const localStyleOrigin = /^https?:$/.test(location.protocol) ? location.origin : "\'self\'";', js)
        self.assertIn("style-src 'self' 'unsafe-inline' ${localStyleOrigin}", js)
        self.assertIn("default-src 'none'", js)
        self.assertIn("form-action 'none'", js)
        self.assertNotIn("allow-scripts", html)

    def test_playground_preview_loads_only_local_host_images_and_data_urls(self):
        js = (ROOT / "docs/playground.js").read_text(encoding="utf-8")
        self.assertIn("img-src data: ${localStyleOrigin}", js,
                      "Site-hosted responsive image examples must load in the sandbox preview")
        self.assertIn("form-action 'none'", js,
                      "Allowing same-origin images must not enable form submission")
        self.assertNotIn("script-src 'unsafe-inline'", js,
                         "The srcdoc preview must not run arbitrary JavaScript")

    def test_ci_images_are_pinned_and_optional_locks_audited(self):
        for name in ("quality", "pr-merge", "browser", "security"):
            config = (ROOT / ".woodpecker" / f"{name}.yaml").read_text(encoding="utf-8")
            images = re.findall(r"(?m)^\s+image:\s+(\S+)\s*$", config)
            self.assertTrue(images, f"No CI images in {name}")
            for ref in images:
                self.assertRegex(ref, r"@sha256:[0-9a-f]{64}$")
        audit = (ROOT / ".woodpecker/security.yaml").read_text(encoding="utf-8")
        self.assertIn("npm audit", audit)
        self.assertIn("examples/lit", audit)
        self.assertIn("benchmarks/frameworks", audit)
        for name in ("examples/lit/package-lock.json", "benchmarks/frameworks/package-lock.json"):
            self.assertTrue((ROOT / name).is_file())


if __name__ == "__main__":
    unittest.main()
