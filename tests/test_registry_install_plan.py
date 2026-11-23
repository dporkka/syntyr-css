"""An optional local installation planner must be safe without a Node runtime."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.registry_install import plan_install, apply_install, RegistryError

ROOT = Path(__file__).resolve().parents[1]


class RegistryInstallPlanTests(unittest.TestCase):
    def test_dependencies_are_resolved_and_install_is_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = plan_install("settings-form", project)
            self.assertEqual(plan["version"], (ROOT / "VERSION").read_text().strip())
            self.assertEqual([file["path"] for file in plan["files"]], [
                "syntyr/css/syntyr.core.css", "syntyr/LICENSE",
                "syntyr/blocks/settings-form.html"
            ])
            self.assertTrue(all(file["status"] == "create" for file in plan["files"]))
            self.assertFalse((project / "syntyr").exists(), "planning must not write files")
            apply_install(plan, project)
            self.assertIn("syn-root", (project / "syntyr/blocks/settings-form.html").read_text())
            rerun = plan_install("settings-form", project)
            self.assertTrue(all(file["status"] == "identical" for file in rerun["files"]))

    def test_existing_modified_target_fails_closed_without_overwriting_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            target = project / "syntyr/css/syntyr.core.css"
            target.parent.mkdir(parents=True)
            target.write_text("custom application css", encoding="utf-8")
            plan = plan_install("settings-form", project)
            self.assertEqual(plan["files"][0]["status"], "conflict")
            with self.assertRaises(RegistryError):
                apply_install(plan, project)
            self.assertEqual(target.read_text(), "custom application css")
            self.assertFalse((project / "syntyr/blocks").exists())

    def test_symlinked_targets_and_dependency_spoofing_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            outside = Path(tmp) / "outside"
            project.mkdir()
            outside.mkdir()
            (project / "syntyr").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(RegistryError):
                plan_install("settings-form", project)
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp)
            (fake / "r").mkdir()
            candidate = json.loads((ROOT / "registry/r/settings-form.json").read_text())
            candidate["registryDependencies"] = ["https://evil.invalid/core.json"]
            (fake / "r/settings-form.json").write_text(json.dumps(candidate))
            with self.assertRaises(RegistryError):
                plan_install("settings-form", Path(tmp) / "project", registry_root=fake)

    def test_installer_verifies_digest_and_version_before_installation(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp)
            (fake / "r").mkdir()
            candidate = json.loads((ROOT / "registry/r/core.json").read_text())
            self.assertIn("fileDigests", candidate["meta"])
            candidate["files"][0]["content"] += "\n/* corrupted */"
            (fake / "r/core.json").write_text(json.dumps(candidate))
            with self.assertRaises(RegistryError):
                plan_install("core", fake / "project", registry_root=fake)
            candidate = json.loads((ROOT / "registry/r/core.json").read_text())
            candidate["meta"]["syntyrVersion"] = "0.0.0"
            (fake / "r/core.json").write_text(json.dumps(candidate))
            with self.assertRaises(RegistryError):
                plan_install("core", fake / "project", registry_root=fake)


    def test_preflight_rejects_nondirectory_ancestor_without_writing_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "syntyr").mkdir()
            (project / "syntyr/blocks").write_text("not a directory")
            with self.assertRaises(RegistryError):
                plan_install("settings-form", project)
            self.assertFalse((project / "syntyr/css").exists())

    def test_apply_rechecks_identical_file_after_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            apply_install(plan_install("core", project), project)
            plan = plan_install("core", project)
            target = project / "syntyr/css/syntyr.core.css"
            original_mkdir = Path.mkdir
            mutated = [False]
            def mutate_before_skip(path, *args, **kwargs):
                if path == target.parent and not mutated[0]:
                    target.write_text("changed after preflight")
                    mutated[0] = True
                return original_mkdir(path, *args, **kwargs)
            with patch.object(Path, "mkdir", mutate_before_skip):
                with self.assertRaises(RegistryError):
                    apply_install(plan, project)
            self.assertTrue(mutated[0])
            self.assertEqual(target.read_text(), "changed after preflight")

    def test_failed_stage_write_never_publishes_partial_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = plan_install("core", project)
            target = project / plan["files"][0]["path"]
            original_open = Path.open

            class FailWritingStream:
                def __init__(self, stream):
                    self.stream = stream
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    return self.stream.__exit__(*args)
                def write(self, data):
                    self.stream.write(data[:3])
                    raise OSError("simulated staged disk failure")

            def injected_open(path, *args, **kwargs):
                stream = original_open(path, *args, **kwargs)
                if (path.name == "0000" and path.parent.name.startswith(".syntyr-stage-")
                        and args and args[0] == "xb"):
                    return FailWritingStream(stream)
                return stream

            with patch.object(Path, "open", injected_open):
                with self.assertRaisesRegex(OSError, "staged disk failure"):
                    apply_install(plan, project)
            self.assertFalse(target.exists(), "partial staged bytes must never publish")
            self.assertFalse(list(project.glob(".syntyr-stage-*")))

    def test_stage_failure_preserves_existing_customer_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = plan_install("settings-form", project)
            license_entry = next(x for x in plan["files"] if x["path"] == "syntyr/LICENSE")
            license_target = project / license_entry["path"]
            license_target.parent.mkdir(parents=True)
            license_target.write_text(license_entry["_content"])
            plan = plan_install("settings-form", project)
            original_open = Path.open

            def fail_second_stage(path, *args, **kwargs):
                if (path.name == "0001" and path.parent.name.startswith(".syntyr-stage-")
                        and args and args[0] == "xb"):
                    raise OSError("simulated stage error")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", fail_second_stage):
                with self.assertRaisesRegex(OSError, "simulated stage error"):
                    apply_install(plan, project)
            self.assertEqual(license_target.read_text(), license_entry["_content"])
            self.assertFalse((project / "syntyr/css/syntyr.core.css").exists())
            self.assertFalse(list(project.glob(".syntyr-stage-*")))

    def test_late_publish_failure_keeps_complete_assets_for_safe_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = plan_install("settings-form", project)
            license_entry = next(x for x in plan["files"] if x["path"] == "syntyr/LICENSE")
            license_target = project / license_entry["path"]
            license_target.parent.mkdir(parents=True)
            license_target.write_text(license_entry["_content"])
            plan = plan_install("settings-form", project)
            first = project / "syntyr/css/syntyr.core.css"
            last = project / "syntyr/blocks/settings-form.html"
            original_link = os.link

            def fail_last_link(source, target, **kwargs):
                if target == last:
                    raise OSError("simulated publish failure")
                return original_link(source, target, **kwargs)

            with patch("scripts.registry_install.os.link", fail_last_link):
                with self.assertRaisesRegex(OSError, "simulated publish failure"):
                    apply_install(plan, project)

            self.assertTrue(first.is_file(), "complete earlier asset must not be deleted")
            self.assertEqual(first.read_text(), plan["files"][0]["_content"])
            self.assertFalse(last.exists())
            self.assertEqual(license_target.read_text(), license_entry["_content"])
            self.assertFalse(list(project.glob(".syntyr-stage-*")))

            apply_install(plan_install("settings-form", project), project)
            self.assertTrue(all(item["status"] == "identical" for item in
                                plan_install("settings-form", project)["files"]))

    def test_concurrent_destination_creation_never_overwrites_customer_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = plan_install("core", project)
            target = project / "syntyr/css/syntyr.core.css"
            original_link = os.link

            def competing_link(source, destination, **kwargs):
                if destination == target:
                    target.write_bytes(b"customer replacement")
                return original_link(source, destination, **kwargs)

            with patch("scripts.registry_install.os.link", competing_link):
                with self.assertRaisesRegex(RegistryError, "Concurrent installation conflict"):
                    apply_install(plan, project)
            self.assertEqual(target.read_bytes(), b"customer replacement")
            self.assertFalse(list(project.glob(".syntyr-stage-*")))

    def test_cross_filesystem_publish_explains_failure_and_keeps_complete_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = plan_install("settings-form", project)
            first, *_, last = plan["files"]
            original_link = os.link

            def reject_cross_filesystem_link(source, destination, **kwargs):
                if destination == project / last["path"]:
                    raise OSError(errno.EXDEV, os.strerror(errno.EXDEV))
                return original_link(source, destination, **kwargs)

            with patch("scripts.registry_install.os.link", reject_cross_filesystem_link):
                with self.assertRaisesRegex(RegistryError, "share the project staging filesystem") as raised:
                    apply_install(plan, project)

            self.assertIn(last["path"], str(raised.exception))
            self.assertEqual((project / first["path"]).read_bytes(), first["_content"].encode("utf-8"))
            self.assertFalse((project / last["path"]).exists())
            self.assertFalse(list(project.glob(".syntyr-stage-*")))

    def test_committed_install_file_is_never_deleted_on_late_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = plan_install("settings-form", project)
            first = project / "syntyr/css/syntyr.core.css"
            blocked_dir = project / "syntyr/blocks"
            original_mkdir = Path.mkdir

            def fail_late(path, *args, **kwargs):
                if path == blocked_dir:
                    raise OSError("simulated late filesystem failure")
                return original_mkdir(path, *args, **kwargs)

            with patch.object(Path, "mkdir", fail_late):
                with self.assertRaisesRegex(OSError, "simulated late filesystem failure"):
                    apply_install(plan, project)

            self.assertTrue(first.is_file(),
                            "already published assets must never be unlinked after later failure")
            self.assertEqual(first.read_text(), plan["files"][0]["_content"])
            self.assertFalse((blocked_dir / "settings-form.html").exists())
            apply_install(plan_install("settings-form", project), project)
            self.assertTrue(all(item["status"] == "identical" for item in
                                plan_install("settings-form", project)["files"]))

    def test_cli_json_verify_reports_installation_integrity_without_source_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            command = [
                sys.executable, str(ROOT / "scripts/registry_install.py"),
                "settings-form", "--project", str(project),
            ]

            def invoke(*args):
                result = subprocess.run(
                    [*command, *args], capture_output=True, text=True, check=False,
                )
                return result, json.loads(result.stdout)

            missing, report = invoke("--verify", "--json")
            self.assertEqual(missing.returncode, 1, missing.stderr)
            self.assertFalse(report["verified"])
            self.assertTrue(report["canApply"])
            self.assertEqual(
                [item["status"] for item in report["files"]],
                ["create", "create", "create"],
            )
            self.assertNotIn("_content", missing.stdout)
            self.assertNotIn("syn-root", missing.stdout)
            self.assertFalse((project / "syntyr").exists())

            applied, report = invoke("--apply", "--json")
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertTrue(report["verified"])
            self.assertTrue(report["applied"])
            checked, report = invoke("--verify", "--json")
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertTrue(report["verified"])
            self.assertFalse(report["applied"])

            modified = project / "syntyr/blocks/settings-form.html"
            modified.write_text("customer customized HTML", encoding="utf-8")
            drifted, report = invoke("--verify", "--json")
            self.assertEqual(drifted.returncode, 1, drifted.stderr)
            self.assertEqual(
                next(item["status"] for item in report["files"]
                     if item["path"] == "syntyr/blocks/settings-form.html"),
                "conflict",
            )
            self.assertEqual(modified.read_text(encoding="utf-8"),
                             "customer customized HTML")


if __name__ == "__main__":
    unittest.main()
