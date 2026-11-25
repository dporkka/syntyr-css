"""Build an opt-in, dependency-free shadcn universal-item registry for MIT assets.

Each item is copy-owned HTML or CSS with explicit targets. This generator does
not publish a registry, install packages, use npm, or modify consumer projects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "registry"
BASE = "https://ui.shadcn.com/schema/"
DEFAULT_REGISTRY_URL = "https://syntyr-css.pages.dev/registry/r"
CSS_MODULES = {
    "core": "syntyr.core.css",
    "recipes": "syntyr.recipes.css",
    "geometry": "syntyr.geometry.css",
    "symbols": "syntyr.symbols.css",
    "viz": "syntyr.viz.css",
    "geo": "syntyr.geo.css",
    "motion": "syntyr.motion.css",
    "effects": "syntyr.effects.css",
    "utilities": "syntyr.utilities.css",
}


def serialize(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def generate(registry_url: str = DEFAULT_REGISTRY_URL) -> dict[str, bytes]:
    # shadcn treats "./core.json" as a filesystem path, not an HTTP sibling.
    # The default uses explicit URLs published together by the same site build.
    if not registry_url.startswith(("https://", "http://127.0.0.1:", "http://localhost:")):
        raise ValueError("Registry URL must be HTTPS or local test HTTP")
    registry_url = registry_url.rstrip("/")
    manifest = json.loads((ROOT / "blocks/manifest.json").read_text(encoding="utf-8"))
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if manifest.get("version") != 1 or not version:
        raise ValueError("Unsupported blocks manifest or missing Syntyr version")
    items = []
    payloads = {}
    for module, cssfile in CSS_MODULES.items():
        path = f"dist/{cssfile}"
        items.append({
            "name": module, "type": "registry:item",
            "title": f"Syntyr {module} CSS",
            "description": f"MIT Syntyr {module} stylesheet. No runtime JavaScript.",
            "dependencies": [], "registryDependencies": [],
            "files": [{"path": path, "type": "registry:file", "target": f"~/syntyr/css/{cssfile}"}],
        })
    seen = set(CSS_MODULES)
    for block in manifest["blocks"]:
        ident = block["id"]
        if not isinstance(ident, str) or not ident.replace("-", "").isalnum() or ident in seen:
            raise ValueError(f"Duplicate or invalid block id: {ident!r}")
        seen.add(ident)
        modules = block["modules"]
        if not modules or not set(modules).issubset(CSS_MODULES):
            raise ValueError(f"Unsupported CSS dependency: {ident}")
        snippet_path = f"blocks/snippets/{ident}.html"
        snippet = (ROOT / snippet_path).read_text(encoding="utf-8")
        # Bundle first-party gallery illustrations alongside copy-owned markup:
        # ../assets/ continues to resolve after local installation. Only the
        # explicitly named original gallery SVGs may become registry assets.
        illustration_names = sorted(set(re.findall(
            r'(?:src|href)="\.\./assets/(gallery-[a-z0-9-]+\.svg)"', snippet
        )))
        block_files = [{"path": snippet_path, "type": "registry:file",
                        "target": f"~/syntyr/blocks/{ident}.html"}]
        block_files.extend(
            {"path": f"assets/{name}", "type": "registry:file",
             "target": f"~/syntyr/assets/{name}"}
            for name in illustration_names
        )
        items.append({
            "name": ident, "type": "registry:item",
            "title": block["title"], "description": block["description"],
            "dependencies": [],
            "registryDependencies": [f"{registry_url}/{module}.json" for module in modules],
            "files": block_files,
        })
    for item in items:
        # Copy-owned MIT files must retain the license notice when installed.
        item["files"].append({"path": "LICENSE", "type": "registry:file",
                              "target": "~/syntyr/LICENSE"})
        files = []
        for file in item["files"]:
            source = ROOT / file["path"]
            if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(ROOT):
                raise ValueError(f"Missing, unsafe or non-file registry source: {source}")
            files.append({**file, "content": source.read_text(encoding="utf-8")})
        payload = {
            "$schema": BASE + "registry-item.json",
            **item,
            "files": files,
            "meta": {"syntyrVersion": version, "source": "MIT source candidate",
                     "runtimeJavaScript": False,
                     "fileDigests": {f["target"]: hashlib.sha256(f["content"].encode("utf-8")).hexdigest() for f in files}},
            "docs": ("Experimental source-candidate asset. Review exact version, "
                     "HTML routes, keyboard behavior and integration before production use."),
        }
        payloads[f"r/{item['name']}.json"] = serialize(payload)
    index = {"$schema": BASE + "registry.json",
             "name": "syntyr", "homepage": "https://github.com/dporkka/syntyr-css",
             "items": items}
    return {"registry.json": serialize(index), **payloads}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--base-url", default=DEFAULT_REGISTRY_URL,
                        help="Registry item URL prefix (local smoke mirrors only)")
    args = parser.parse_args()
    expected = generate(args.base_url)
    actual = {p.relative_to(OUTPUT).as_posix(): p.read_bytes()
              for p in OUTPUT.rglob("*.json")} if OUTPUT.exists() else {}
    if args.check:
        mismatches = sorted(set(actual) ^ set(expected) |
                            {name for name in expected if actual.get(name) != expected[name]})
        for name in mismatches:
            print("STALE", name)
        if not mismatches:
            print(f"OK registry: {len(expected) - 1} universal items")
        return bool(mismatches)
    for name, payload in expected.items():
        dest = OUTPUT / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
    for stale in sorted(set(actual) - set(expected)):
        (OUTPUT / stale).unlink()
    print(f"WROTE registry: {len(expected) - 1} universal items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
