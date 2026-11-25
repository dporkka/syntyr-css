#!/usr/bin/env python3
"""Build reproducible, offline demo ZIPs from the actual generation pipeline."""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_ui import generate
from agent_mcp.catalog import CANDIDATE

DEMOS = {
    "saas": {"title": "SaaS landing page", "theme": "studio",
             "requirements": ["product-intro", "features", "pricing", "faq", "call-to-action"]},
    "crm": {"title": "CRM dashboard", "theme": "noir",
            "requirements": ["pipeline", "metrics", "inventory-search", "account-management"]},
    "native": {"title": "Native controls", "theme": "corporate",
               "requirements": ["product-intro"], "interactions": [
                   {"contract": "combobox", "recipe": "native-select", "relationship": "fallback"},
                   {"contract": "sortable-table", "recipe": "native-table", "relationship": "fallback"},
                   {"contract": "disclosure", "recipe": "native-modal-dialog", "relationship": "example"},
               ]},
}


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def build_demo(name: str) -> bytes:
    if name not in DEMOS:
        raise ValueError("Unknown demo")
    request = {"release": CANDIDATE, **DEMOS[name]}
    result = generate(request)
    if result["status"] != "generated":
        raise RuntimeError("Demo generation blocked: " + result["stage"])
    output = result["output"]
    if output["stylesheets"] != ["syntyr.all.css"]:
        raise RuntimeError("Demo stylesheet packaging needs review")
    entries = {
        "index.html": output["html"].encode(),
        "syntyr.all.css": (ROOT / "dist/syntyr.all.css").read_bytes(),
        "LICENSE": (ROOT / "LICENSE").read_bytes(),
        "request.json": json_bytes(request),
        "project.json": json_bytes(output["project"]),
        "validation.json": json_bytes({k: v for k, v in result.items() if k != "output"}),
        "README.txt": (
            "Syntyr source candidate " + CANDIDATE + "\n"
            "Open index.html locally; keep CSS and assets alongside it.\n"
            "This is a presentation scaffold, not a working application.\n"
            "Sample copy, routes, forms and data need review before deployment.\n"
            "See validation.json for coverage, limitations and host obligations.\n"
            "Regenerate from the matching source checkout: "
            "python3 scripts/generate_ui.py < request.json\n"
            "Import project.json in the matching visual builder to edit.\n"
        ).encode(),
    }
    for name in output["assets"]:
        if not isinstance(name, str) or not re.fullmatch(r"(?:gallery-[a-z0-9-]+|syntyr-mark)\.svg", name):
            raise RuntimeError("Unexpected demo asset")
        entries["assets/" + name] = (ROOT / "assets" / name).read_bytes()
    buf = BytesIO()
    with ZipFile(buf, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path, content in sorted(entries.items()):
            info = ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compresslevel=9)
    return buf.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("demo", choices=sorted(DEMOS))
    parser.add_argument("output", type=Path, help="New ZIP file; existing files are not overwritten")
    args = parser.parse_args(argv)
    try:
        data = build_demo(args.demo)
        with args.output.open("xb") as stream:
            stream.write(data)
    except (ValueError, OSError, RuntimeError) as exc:
        print("Demo error: " + str(exc), file=sys.stderr)
        return 1
    print(f"Created {args.output} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
