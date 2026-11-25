"""An optional local installation planner must be safe without a Node runtime."""
import json
from pathlib import Path
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



if __name__ == "__main__":
    unittest.main()
