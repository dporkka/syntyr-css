"""The optional local browser CLI has a narrow target and stable report contract."""
import unittest
from scripts.responsive_audit import local_target, make_report

class ResponsiveCliTest(unittest.TestCase):
    def test_only_explicit_loopback_http_is_accepted(self):
        self.assertEqual(local_target("http://127.0.0.1:8000/demo?q=x"), ("http://127.0.0.1:8000", "/demo?q=x"))
        for url in ("https://example.com", "http://localhost.evil.test", "http://127.0.0.1@evil.test", "file:///etc/passwd", "http://localhost:8000/#token"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                local_target(url)

    def test_report_has_no_success_when_a_case_is_blocked(self):
        report = make_report([{"engine":"chromium","page":"/","width":320,"height":568,"textScale":1,"status":"blocked"}])
        self.assertEqual(report["schemaVersion"], 1)
        self.assertEqual(report["summary"], {"pass":0,"fail":0,"blocked":1})
