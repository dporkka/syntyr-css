"""Optional real shadcn CLI compatibility smoke, never a required Syntyr build step.

Requires Node and access to the selected CLI package (or an existing npm cache):
  python3 tests/shadcn_registry_cli_smoke.py --package shadcn@4.23.0
No packages or files are written into the repository or a consumer project.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import os
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_shadcn_registry import generate  # noqa: E402


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", default="shadcn@4.23.0")
    parser.add_argument("--cli-bin", type=str, help="Already installed shadcn CLI; avoid npx/npm fetch")
    args = parser.parse_args()
    # Preserve PATH lookup for bare names; paths containing a directory are
    # anchored before the child process switches to an isolated consumer cwd.
    cli_bin = (os.path.abspath(args.cli_bin) if args.cli_bin and os.path.dirname(args.cli_bin)
               else args.cli_bin)
    with tempfile.TemporaryDirectory(prefix="syntyr-shadcn-") as temp:
        temp = Path(temp)
        server_root = temp / "static"
        server = ThreadingHTTPServer(("127.0.0.1", 0),
                   partial(QuietHandler, directory=str(server_root)))
        port = server.server_address[1]
        base_url = f"http://127.0.0.1:{port}/registry/r"
        for name, content in generate(base_url).items():
            file = server_root / "registry" / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for block, modules in (("faq", ("core",)),
                                   ("hero-product", ("core", "recipes")),
                                   ("resource-workspace", ("core", "recipes"))):
                consumer = temp / block
                consumer.mkdir()
                command = ([cli_bin, "add", f"{base_url}/{block}.json", "--yes"]
                           if cli_bin else
                           ["npx", "--yes", args.package, "add", f"{base_url}/{block}.json", "--yes"])
                result = subprocess.run(
                    command,
                    cwd=consumer, capture_output=True, text=True, timeout=120)
                if result.returncode:
                    raise RuntimeError(f"shadcn failed for {block}:\n{result.stdout}\n{result.stderr}")
                html = consumer / "syntyr/blocks" / (block + ".html")
                if html.read_bytes() != (ROOT / "blocks/snippets" / (block + ".html")).read_bytes():
                    raise AssertionError(f"Installed HTML mismatch: {block}")
                for module in modules:
                    css_name = {"core": "syntyr.core.css",
                                "recipes": "syntyr.recipes.css"}[module]
                    installed = consumer / "syntyr/css" / css_name
                    if installed.read_bytes() != (ROOT / "dist" / css_name).read_bytes():
                        raise AssertionError(f"Installed CSS mismatch: {css_name}")
                if (consumer / "syntyr/LICENSE").read_bytes() != (ROOT / "LICENSE").read_bytes():
                    raise AssertionError("Installed MIT license notice is missing or changed")
                if (consumer / "package.json").exists() or (consumer / "node_modules").exists():
                    raise AssertionError("Universal registry unexpectedly created a runtime package")
                print(f"PASS {block}: HTML and {len(modules)} exact CSS modules, zero runtime packages")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
