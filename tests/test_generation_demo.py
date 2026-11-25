"""Portable demo packages reproduce the real, validated generation pipeline."""
import io
import json
import shutil
import unittest
from zipfile import ZipFile

from scripts.build_generation_demo import build_demo, DEMOS


@unittest.skipUnless(shutil.which("node"), "Optional Node authoring tool")
class GenerationDemoTests(unittest.TestCase):
    def test_each_demo_is_a_deterministic_portable_package(self):
        for name in DEMOS:
            with self.subTest(name=name):
                data = build_demo(name)
                self.assertEqual(data, build_demo(name))
                with ZipFile(io.BytesIO(data)) as z:
                    self.assertIsNone(z.testzip())
                    self.assertTrue({"index.html", "syntyr.all.css", "LICENSE", "README.txt",
                                     "request.json", "project.json", "validation.json"} <= set(z.namelist()))
                    report = json.loads(z.read("validation.json"))
                    self.assertEqual(report["status"], "generated")
                    self.assertEqual(report["validation"]["diagnostics"], [])
                    self.assertTrue(report["preflight"]["valid"])
                    self.assertNotIn("output", report)
                    html = z.read("index.html").decode()
                    self.assertNotIn("<script", html)
                    self.assertIn('href="syntyr.all.css"', html)
                    self.assertIn("not a working application", z.read("README.txt").decode())
                    for name_in_zip in z.namelist():
                        self.assertFalse(name_in_zip.startswith("/") or ".." in name_in_zip.split("/"))

    def test_unknown_demo_rejected(self):
        with self.assertRaises(ValueError):
            build_demo("../escape")
