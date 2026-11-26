"""Fresh generator CI orchestration: fail closed, no consumer dependencies."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import build_generator_parity as gate
from scripts.render_cms_starter import render_document
from scripts.verify_cms_parity import CONTENT

ROOT = Path(__file__).resolve().parents[1]


def fixture(output, mount, *, drift=False):
    css = output / "css"
    css.mkdir(parents=True)
    for name in ("syntyr.core.css", "syntyr.recipes.css"):
        shutil.copyfile(ROOT / "dist" / name, css / name)
    markup = render_document(json.loads(CONTENT.read_text())).replace('href="/', f'href="{mount}')
    if drift:
        markup = markup.replace("Built for long-lived websites", "Drifted content")
    (output / "index.html").write_text(markup)


class GeneratorParityCI(unittest.TestCase):
    def mock_builds(self, *, drift=False, fail=False):
        def npm_or_css(command, *, cwd, check):
            self.assertTrue(check)
            if command[0] != "npm":
                self.assertIn("scripts/build.py", command)
                return
            if cwd.name == "eleventy":
                output = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("--output=")))
                fixture(output, "/syntyr-eleventy/")
            elif cwd.name == "astro-keystatic":
                output = Path(command[-1])
                self.assertTrue(output.is_relative_to(cwd))
                if fail:
                    raise subprocess.CalledProcessError(1, command)
                fixture(output, "/syntyr-astro-keystatic/", drift=drift)
            else:
                self.fail(f"Unexpected generator: {cwd}")
        return patch("scripts.build_generator_parity.subprocess.run", side_effect=npm_or_css)

    def test_fresh_build_contains_independent_verified_fixtures(self):
        with TemporaryDirectory() as tmp, self.mock_builds(), patch(
            "scripts.build_generator_parity.build_hugo",
            side_effect=lambda output, **kwargs: fixture(output, "/syntyr-hugo/"),
        ) as hugo:
            target = Path(tmp) / "parity"
            gate.build_fixtures(target, hugo="/verified/hugo")
            self.assertEqual({path.name for path in target.iterdir()},
                             {"reference", "syntyr-hugo", "syntyr-eleventy", "syntyr-astro-keystatic"})
            hugo.assert_called_once()
            self.assertEqual(hugo.call_args.kwargs["hugo"], "/verified/hugo")

    def test_drift_or_build_failure_does_not_publish_partial_output(self):
        for drift, fail in ((True, False), (False, True)):
            with self.subTest(drift=drift, fail=fail), TemporaryDirectory() as tmp, self.mock_builds(
                    drift=drift, fail=fail), patch(
                "scripts.build_generator_parity.build_hugo",
                side_effect=lambda output, **kwargs: fixture(output, "/syntyr-hugo/"),
            ):
                target = Path(tmp) / "parity"
                with self.assertRaises(AssertionError if drift else subprocess.CalledProcessError):
                    gate.build_fixtures(target)
                self.assertFalse(target.exists())
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_invalid_canonical_input_rejected_before_any_generator_runs(self):
        with TemporaryDirectory() as tmp, patch("scripts.build_generator_parity.subprocess.run") as run:
            root = Path(tmp)
            content = root / "home.json"
            original = CONTENT.read_text()
            content.write_text('{"title":"shadowed",' + original.lstrip()[1:])
            target = root / "parity"
            with patch("scripts.build_generator_parity.CONTENT", content), self.assertRaisesRegex(ValueError, "Duplicate"):
                gate.build_fixtures(target)
            run.assert_not_called()
            self.assertEqual(list(root.iterdir()), [content])

    def test_existing_output_or_symlink_rejected_before_any_generator_runs(self):
        with TemporaryDirectory() as tmp, patch("scripts.build_generator_parity.subprocess.run") as run:
            root = Path(tmp)
            existing = root / "keep"
            existing.mkdir()
            (existing / "content.txt").write_text("preserve")
            alias = root / "alias"
            alias.symlink_to(existing, target_is_directory=True)
            for target in (existing, alias):
                with self.assertRaises(FileExistsError):
                    gate.build_fixtures(target)
            self.assertEqual((existing / "content.txt").read_text(), "preserve")
            run.assert_not_called()

    def test_woodpecker_uses_pinned_independent_build_and_browser_stages(self):
        config = (ROOT / ".woodpecker/static-generators.yaml").read_text()
        for expected in (
            "event: manual", "event: tag", "event: [pull_request, push]", "branch: main",
            "examples/eleventy/**", "examples/astro-keystatic/**",
            "npm ci --prefix examples/eleventy", "npm ci --prefix examples/astro-keystatic",
            "sha256sum -c -", "set -eu", "previews/generator-parity",
            "depends_on:", "- fresh-locked-generator-builds",
            "node examples/lit/generator-parity-browser.mjs previews/generator-parity chromium firefox webkit",
        ):
            self.assertIn(expected, config)
        self.assertLess(config.index("sha256sum -c -"), config.index('"$tools_dir/hugo" version'))
        self.assertNotIn("pip install", config)
        self.assertNotIn("npm install --prefix", config)
        self.assertIn("node:24-bookworm-slim@sha256:", config)
        self.assertIn("mcr.microsoft.com/playwright:v1.65.0-noble@sha256:", config)

    def test_eleventy_lock_is_exact_and_not_a_core_dependency(self):
        example = ROOT / "examples/eleventy"
        package = json.loads((example / "package.json").read_text())
        lock = json.loads((example / "package-lock.json").read_text())
        version = package["devDependencies"]["@11ty/eleventy"]
        self.assertEqual(version, lock["packages"][""]["devDependencies"]["@11ty/eleventy"])
        self.assertEqual(version, lock["packages"]["node_modules/@11ty/eleventy"]["version"])
        core = json.loads((ROOT / "package.json").read_text())
        self.assertNotIn("@11ty/eleventy", core.get("dependencies", {}))
        self.assertNotIn("@11ty/eleventy", core.get("devDependencies", {}))


if __name__ == "__main__":
    unittest.main()
