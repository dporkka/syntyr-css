"""Opt-in, stdlib-only planner for the local Syntyr copy-owned registry.

No network, package manager, script execution or mutations in plan mode.
Only the checked-in prerelease registry matching VERSION is supported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

if __package__:
    from .build_shadcn_registry import ROOT, OUTPUT, DEFAULT_REGISTRY_URL
else:
    from build_shadcn_registry import ROOT, OUTPUT, DEFAULT_REGISTRY_URL


class RegistryError(ValueError):
    """Invalid registry data, unsafe target, or existing-file conflict."""


def _safe_destination(project: Path, target: str) -> Path:
    if not isinstance(target, str) or not target.startswith("~/syntyr/"):
        raise RegistryError("Registry target outside ~/syntyr/")
    relative = target[2:]
    parts = Path(relative).parts
    if not parts or any(part in {".", ".."} for part in parts):
        raise RegistryError("Invalid registry target")
    if not re.fullmatch(r"syntyr/(css|blocks)/[a-z0-9_.-]+|syntyr/LICENSE", relative):
        raise RegistryError("Unknown registry destination: " + relative)
    if project.is_symlink():
        raise RegistryError("Project directory must not be a symlink")
    destination = project / relative
    for parent in (project, *destination.parents):
        if parent == project.parent:
            break
        if parent.is_symlink():
            raise RegistryError("Symlinked installation path: " + str(parent))
        if parent.exists() and not parent.is_dir():
            raise RegistryError("Non-directory installation ancestor: " + str(parent))
    if destination.is_symlink():
        raise RegistryError("Symlinked installation target: " + relative)
    return destination


def plan_install(name: str, project: Path, registry_root: Path = OUTPUT) -> dict:
    """Resolve explicit CSS dependencies, validate hashes and preview all writes."""
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise RegistryError("Invalid item name")
    project = Path(project).absolute()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    registry_root = Path(registry_root)
    collected: dict[str, str] = {}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_name: str) -> None:
        if item_name in visited:
            return
        if item_name in visiting:
            raise RegistryError("Cyclic registry dependency")
        visiting.add(item_name)
        file = registry_root / "r" / (item_name + ".json")
        try:
            obj = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RegistryError("Missing or unreadable registry item: " + item_name) from error
        if obj.get("name") != item_name or obj.get("type") != "registry:item":
            raise RegistryError("Unexpected registry item identity")
        meta = obj.get("meta", {})
        if meta.get("syntyrVersion") != version or meta.get("runtimeJavaScript") is not False:
            raise RegistryError("Incompatible item version or runtime")
        if obj.get("dependencies") != []:
            raise RegistryError("Runtime dependencies are not supported")
        for dep in obj.get("registryDependencies", []):
            prefix = DEFAULT_REGISTRY_URL + "/"
            if not isinstance(dep, str) or not dep.startswith(prefix) or not dep.endswith(".json"):
                raise RegistryError("Untrusted registry dependency URL")
            child = dep[len(prefix):-5]
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", child):
                raise RegistryError("Invalid dependency item name")
            visit(child)
        hashes = meta.get("fileDigests")
        if not isinstance(hashes, dict):
            raise RegistryError("Missing content digests")
        files = obj.get("files")
        if not isinstance(files, list) or not files:
            raise RegistryError("Missing item files")
        for entry in files:
            if not isinstance(entry, dict) or entry.get("type") != "registry:file":
                raise RegistryError("Unexpected file entry")
            target, content = entry.get("target"), entry.get("content")
            if not isinstance(content, str):
                raise RegistryError("Missing file content")
            dest = _safe_destination(project, target)
            relative = dest.relative_to(project).as_posix()
            expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if hashes.get(target) != expected_hash:
                raise RegistryError("File digest mismatch: " + relative)
            old = collected.get(relative)
            if old is not None and old != content:
                raise RegistryError("Conflicting registry assets: " + relative)
            collected[relative] = content
        visiting.remove(item_name)
        visited.add(item_name)

    visit(name)
    files = []
    for relative, content in collected.items():
        target = _safe_destination(project, "~/" + relative)
        status = "create"
        if target.exists():
            if not target.is_file():
                raise RegistryError("Non-file registry destination: " + relative)
            status = "identical" if target.read_bytes() == content.encode("utf-8") else "conflict"
        files.append({"path": relative, "status": status,
                      "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                      "bytes": len(content.encode("utf-8")), "_content": content})
    return {"item": name, "version": version, "project": str(project), "files": files}


def apply_install(plan: dict, project: Path) -> None:
    """Explicit opt-in copy; never replaces or follows an existing target."""
    project = Path(project).absolute()
    if plan.get("project") != str(project):
        raise RegistryError("Installation target does not match the reviewed plan")
    for entry in plan["files"]:
        target = _safe_destination(project, "~/" + entry["path"])
        if entry["status"] == "conflict" or (target.exists() and
              (not target.is_file() or target.read_bytes() != entry["_content"].encode("utf-8"))):
            raise RegistryError("Would overwrite existing file: " + entry["path"])
    # A multi-file install can fail after earlier assets were copied (e.g. disk
    # full or a concurrent directory change). Keep the install retryable by
    # rolling back only assets this invocation created and that remain unchanged.
    created_files: list[tuple[Path, bytes, int, int]] = []
    try:
        for entry in plan["files"]:
            target = _safe_destination(project, "~/" + entry["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            _safe_destination(project, "~/" + entry["path"])
            content = entry["_content"].encode("utf-8")
            if target.exists():
                # Another process can modify a once-identical target after preflight.
                if not target.is_file() or target.read_bytes() != content:
                    raise RegistryError("Changed during installation: " + entry["path"])
                continue
            created = False
            try:
                with target.open("xb") as stream:
                    created = True
                    stream.write(content)
                    metadata = target.stat(follow_symlinks=False)
                created_files.append((target, content, metadata.st_dev, metadata.st_ino))
            except FileExistsError as error:
                raise RegistryError("Concurrent installation conflict: " + entry["path"]) from error
            except BaseException:
                # Exclusive create succeeded: discard our partial file on write/close
                # failure. Never remove files that existed before this attempt.
                if created:
                    target.unlink(missing_ok=True)
                raise
    except BaseException:
        for target, content, device, inode in reversed(created_files):
            try:
                metadata = target.stat(follow_symlinks=False)
                if (metadata.st_dev == device and metadata.st_ino == inode
                        and target.is_file() and target.read_bytes() == content):
                    target.unlink()
            except OSError:
                # Do not mask the original failure or delete a changed target.
                pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan, install, or verify a local Syntyr registry item")
    parser.add_argument("item", help="Name from registry/registry.json")
    parser.add_argument("--project", type=Path, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true",
                        help="Opt in to creating missing assets; never overwrites")
    action.add_argument("--verify", action="store_true",
                        help="Exit nonzero if any expected installed file is missing or modified")
    parser.add_argument("--json", action="store_true",
                        help="Output machine-readable paths, digests, and statuses (never source)")
    args = parser.parse_args()
    try:
        plan = plan_install(args.item, args.project)
        if args.apply:
            apply_install(plan, args.project)
            plan = plan_install(args.item, args.project)
        verified = all(entry["status"] == "identical" for entry in plan["files"])
        if args.json:
            print(json.dumps({
                "item": plan["item"], "version": plan["version"],
                "project": plan["project"],
                "verified": verified,
                "canApply": all(entry["status"] != "conflict" for entry in plan["files"]),
                "applied": args.apply,
                "files": [
                    {key: entry[key] for key in ("path", "status", "sha256", "bytes")}
                    for entry in plan["files"]
                ],
            }, indent=2))
        else:
            for entry in plan["files"]:
                print(f"{entry['status']:9} {entry['path']} ({entry['bytes']} bytes, sha256:{entry['sha256'][:12]})")
            print(f"Syntyr {plan['version']} / {len(plan['files'])} files")
            if args.apply:
                print("Installed; existing identical files untouched")
            elif args.verify:
                print("Verified" if verified else "Verification failed: missing or modified assets")
            else:
                print("Dry run only. Pass --apply to copy missing files.")
        return 0 if not args.verify or verified else 1
    except (RegistryError, OSError) as error:
        parser.exit(2, f"Registry installation rejected: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
