#!/usr/bin/env python3
"""Export a standalone, copy-owned Expo SaaS starter from canonical sources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from export_site_starter import publish_new_directory

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/expo-native-smoke"
APP_NAME = "syntyr-native-starter"
ADAPTER_FILES = ("tokens.ts", "styles.ts", "recipes.tsx")
SCREEN_FILES = ("App.tsx", "OperationsScreen.tsx")


def export_native_starter(destination: Path) -> Path:
    destination = destination.expanduser()
    destination = destination.parent.resolve() / destination.name
    if destination.is_symlink() or destination.exists():
        raise FileExistsError(f"Destination exists; refusing to overwrite: {destination}")
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"Create the output parent directory first: {destination.parent}")

    with tempfile.TemporaryDirectory(prefix=".syntyr-native-", dir=destination.parent) as work:
        staged = Path(work) / "starter"
        source = staged / "src"
        source.mkdir(parents=True)
        for name in ("index.ts", "tsconfig.json", "App.test.tsx", "OperationsScreen.test.tsx"):
            shutil.copyfile(FIXTURE / name, staged / name)
        for name in ADAPTER_FILES:
            shutil.copyfile(ROOT / "integrations/react-native" / name, source / name)
        for name in SCREEN_FILES:
            text = (ROOT / "examples/react-native" / name).read_text(encoding="utf-8")
            prefix = "../../integrations/react-native/"
            if prefix not in text:
                raise ValueError(f"Canonical {name} imports changed; update the starter contract")
            (source / name).write_text(text.replace(prefix, "./"), encoding="utf-8")

        package = json.loads((FIXTURE / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((FIXTURE / "package-lock.json").read_text(encoding="utf-8"))
        root_lock = lock["packages"][""]
        for key in ("name", "version", "dependencies", "devDependencies"):
            if package.get(key) != root_lock.get(key):
                raise ValueError(f"Fixture lock mismatch: {key}")
        package["name"] = lock["name"] = root_lock["name"] = APP_NAME

        # Keep the verified dependency graph, but remove repository-only sync
        # and measurement scripts. The exported src/ is consumer-owned.
        scripts = {}
        for name in ("start", "android", "ios", "typecheck", "test", "export:android", "export:ios"):
            command = package["scripts"][name]
            if not command.startswith("npm run sync && "):
                raise ValueError(f"Fixture script changed: {name}")
            scripts[name] = command.removeprefix("npm run sync && ")
        package["scripts"] = scripts
        app = json.loads((FIXTURE / "app.json").read_text(encoding="utf-8"))
        app["expo"]["name"] = "Syntyr Native Starter"
        app["expo"]["slug"] = APP_NAME
        for name, data in (("package.json", package), ("package-lock.json", lock), ("app.json", app)):
            (staged / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (staged / ".gitignore").write_text("node_modules/\ndist/\n.expo/\ncoverage/\n*.log\n", encoding="utf-8")
        shutil.copyfile(ROOT / "LICENSE", staged / "LICENSE")
        shutil.copyfile(FIXTURE / "starter-README.md", staged / "README.md")
        publish_new_directory(staged, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory; never overwrites an existing path")
    args = parser.parse_args()
    try:
        result = export_native_starter(args.output)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Export failed: {exc}\n")
    print(f"Exported standalone Expo starter to {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
