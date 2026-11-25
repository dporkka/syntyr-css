#!/usr/bin/env python3
"""Opt-in actual package and framework verification.

No Node/npm dependency is introduced into Syntyr's core Python test suite.
Run with --install after a clean checkout; see docs/jsx-tsx-integration.md.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(folder, *args):
    print("$", " ".join(args), "[", folder, "]", flush=True)
    subprocess.run(args, cwd=ROOT / folder, check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true",
                        help="npm install for each local optional consumer")
    options = parser.parse_args()
    if not shutil.which("node") or not shutil.which("npm"):
        parser.error("Node.js and npm are required for this opt-in integration test")

    # The local file: React package must be built before its dependents install.
    tasks = [
        ("packages/react", "test"),
        ("examples/react-vite", "build"),
        ("examples/preact-jsx", "build"),
        ("examples/solid-tsx", "build"),
        ("examples/next-app-router", "build"),
        ("examples/node-express", "test"),
    ]
    for folder, task in tasks:
        if options.install:
            run(folder, "npm", "install", "--no-audit", "--no-fund")
        run(folder, "npm", "run", task)
    print("All Syntyr JSX/TSX, Node, React and Next adoption checks passed.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
