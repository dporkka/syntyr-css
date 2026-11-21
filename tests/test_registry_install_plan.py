"""An optional local installation planner must be safe without a Node runtime."""
from contextlib import contextmanager
import json
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

    def test_failed_write_removes_partial_new_file(self):
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
                    raise OSError("simulated disk failure")
            def injected_open(path, *args, **kwargs):
                stream = original_open(path, *args, **kwargs)
                if path == target and args and args[0] == "xb":
                    return FailWritingStream(stream)
                return stream
            with patch.object(Path, "open", injected_open):
                with self.assertRaises(OSError):
                    apply_install(plan, project)
            self.assertFalse(target.exists(), "failed creation must not leave a partial asset")



    def test_mid_install_failure_rolls_back_only_new_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            first_plan = plan_install("settings-form", project)
            license_entry = next(item for item in first_plan["files"] if item["path"] == "syntyr/LICENSE")
            license_target = project / license_entry["path"]
            license_target.parent.mkdir(parents=True)
            license_target.write_text(license_entry["_content"], encoding="utf-8")

            plan = plan_install("settings-form", project)
            self.assertEqual(
                [item["status"] for item in plan["files"]],
                ["create", "identical", "create"],
            )
            failing_target = project / "syntyr/blocks/settings-form.html"
            original_open = Path.open

            def fail_on_last_asset(path, *args, **kwargs):
                if path == failing_target and args and args[0] == "xb":
                    raise OSError("simulated later asset failure")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", fail_on_last_asset):
                with self.assertRaisesRegex(OSError, "simulated later asset failure"):
                    apply_install(plan, project)

            self.assertFalse(
                (project / "syntyr/css/syntyr.core.css").exists(),
                "a failed multi-asset install must remove earlier new files",
            )
            self.assertFalse(failing_target.exists())
            self.assertEqual(
                license_target.read_text(encoding="utf-8"),
                license_entry["_content"],
                "previously identical customer files must remain untouched",
            )

            apply_install(plan_install("settings-form", project), project)
            self.assertTrue(failing_target.is_file())
            self.assertTrue(all(item["status"] == "identical" for item in
                                plan_install("settings-form", project)["files"]))



    def test_rollback_preserves_identical_replacement_during_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = plan_install("settings-form", project)
            first = project / plan["files"][0]["path"]
            moved = first.with_suffix(".moved")
            failing = project / plan["files"][-1]["path"]
            content = plan["files"][0]["_content"].encode("utf-8")
            original_open = Path.open

            @contextmanager
            def swap_during_write(path):
                with original_open(path, "xb") as stream:
                    write = stream.write

                    def write_then_replace(data):
                        size = write(data)
                        path.rename(moved)
                        path.write_bytes(data)
                        return size

                    with patch.object(stream, "write", write_then_replace):
                        yield stream

            def injected_open(path, mode="r", *args, **kwargs):
                if mode == "xb":
                    if path == first:
                        return swap_during_write(path)
                    if path == failing:
                        raise OSError("simulated later asset failure")
                return original_open(path, mode, *args, **kwargs)

            with patch.object(Path, "open", injected_open):
                with self.assertRaisesRegex(OSError, "simulated later asset failure"):
                    apply_install(plan, project)

            self.assertEqual(moved.read_bytes(), content)
            self.assertEqual(first.read_bytes(), content)
            self.assertFalse((project / "syntyr/LICENSE").exists())

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
