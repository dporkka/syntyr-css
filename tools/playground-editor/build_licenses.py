"""Write licensing notices for the self-hosted CodeMirror browser bundle.

Run after `npm ci --prefix tools/playground-editor`.
The esbuild build tool itself is not shipped in the browser artifact.
"""
from pathlib import Path
import argparse
import json
import sys

TOOL_DIR = Path(__file__).resolve().parent
ROOT = TOOL_DIR.parents[1]
OUTPUT = ROOT / "docs/playground-editor.licenses.txt"


def generate() -> str:
    lock = json.loads((TOOL_DIR / "package-lock.json").read_text())
    notices = [
        "Third-party notices for docs/playground-editor.js",
        "These licenses apply only to the optional documentation editor.",
        "Syntyr's MIT CSS core does not include or depend on CodeMirror.",
        "",
    ]
    for key, info in sorted(lock["packages"].items()):
        if not key.startswith("node_modules/"):
            continue
        name = info.get("name") or key.removeprefix("node_modules/")
        if name == "esbuild" or name.startswith("@esbuild/"):
            continue  # esbuild is a development-only bundler
        folder = TOOL_DIR / key
        licenses = [path for path in folder.iterdir() if path.is_file()
                    and path.name.lower().startswith(("license", "licence"))]
        if not licenses:
            raise ValueError(f"No license file found for {name}")
        notices.extend([f"===== {name} {info.get('version', 'unknown')} =====",
                        licenses[0].read_text(encoding="utf-8").strip(), ""])
    return "\n".join(notices).rstrip("\n") + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    opts = parser.parse_args()
    body = generate()
    if opts.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != body:
            print("Stale docs/playground-editor.licenses.txt", file=sys.stderr)
            return 1
        print("OK docs/playground-editor.licenses.txt")
        return 0
    OUTPUT.write_text(body, encoding="utf-8")
    print(f"Updated {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
