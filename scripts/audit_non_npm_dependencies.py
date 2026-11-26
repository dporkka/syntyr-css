"""Query OSV for Syntyr's public non-npm dependency inventories.

Checks registry crates, every Go checksum entry (a conservative inventory,
not a reachability claim), and pinned docs-maintainer Python dependencies.
Only package coordinates are transmitted; no source, credentials or Git data.
Requires network access to the OSV querybatch API, not registry installs.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tomllib
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OSV_ENDPOINT = "https://api.osv.dev/v1/querybatch"
# Public, optional dependency inputs; no user-controlled paths or private packages.
INVENTORIES = {
    "examples/rust-axum/Cargo.lock": "crates.io",
    "examples/server-components-templ/go.sum": "Go",
    "requirements-docs.txt": "PyPI",
}
PIN = re.compile(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)")
ADVISORY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")


def package_inventory(root: Path) -> dict[tuple[str, str, str], set[str]]:
    packages: dict[tuple[str, str, str], set[str]] = {}
    for relative, ecosystem in INVENTORIES.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or unsafe inventory: {relative}")
        contents = path.read_text(encoding="utf-8")
        entries = set()
        if ecosystem == "crates.io":
            for entry in tomllib.loads(contents)["package"]:
                source = entry.get("source")
                if source is None:
                    continue  # Local example crate, not a registry dependency.
                if source != "registry+https://github.com/rust-lang/crates.io-index":
                    raise ValueError(f"Unsupported Cargo dependency source: {entry['name']}")
                entries.add((entry["name"], entry["version"]))
        elif ecosystem == "Go":
            for line in contents.splitlines():
                if not line.strip():
                    continue
                name, version, checksum = line.split()
                if not checksum.startswith("h1:") or not version.startswith("v"):
                    raise ValueError(f"Invalid Go checksum line in {relative}")
                entries.add((name, version.removesuffix("/go.mod")))
        else:
            for line in contents.splitlines():
                value = line.split("#", 1)[0].strip()
                if not value:
                    continue
                match = PIN.fullmatch(value)
                if not match:
                    raise ValueError(f"Expected an exact Python pin in {relative}")
                entries.add(match.groups())
        if not entries:
            raise ValueError(f"Empty dependency inventory: {relative}")
        for name, version in entries:
            packages.setdefault((ecosystem, name, version), set()).add(relative)
    return packages


def query_batch(queries: list[dict]) -> dict:
    request = Request(OSV_ENDPOINT, data=json.dumps({"queries": queries}).encode(),
                      headers={"Content-Type": "application/json", "Accept": "application/json"},
                      method="POST")
    with urlopen(request, timeout=45) as response:
        return json.load(response)


def advisories(packages: dict, request=query_batch) -> dict:
    findings = {}
    keys = sorted(packages)
    if not keys:
        raise ValueError("No package coordinates; refusing an empty audit")
    # OSV guarantees result ordering. Keep the package mapping on pagination.
    for offset in range(0, len(keys), 100):
        pending = [(key, {"package": {"ecosystem": key[0], "name": key[1]}, "version": key[2]})
                   for key in keys[offset:offset + 100]]
        seen_tokens = set()
        pages = 0
        while pending:
            pages += 1
            if pages > 100:
                raise ValueError("OSV pagination exceeded the safety limit")
            response = request([query for _, query in pending])
            results = response.get("results") if isinstance(response, dict) else None
            if not isinstance(results, list) or len(results) != len(pending):
                raise ValueError("OSV response is incomplete or malformed")
            following = []
            for (key, query), result in zip(pending, results):
                if not isinstance(result, dict) or not result.keys() <= {"vulns", "next_page_token"}:
                    raise ValueError("Unexpected OSV per-package response")
                vulns = result.get("vulns", [])
                if not isinstance(vulns, list):
                    raise ValueError("Malformed OSV advisory list")
                for vuln in vulns:
                    identifier = vuln.get("id") if isinstance(vuln, dict) else None
                    if not isinstance(identifier, str) or not ADVISORY_ID.fullmatch(identifier):
                        raise ValueError("OSV advisory lacks a valid ID")
                    findings.setdefault(key, set()).add(identifier)
                token = result.get("next_page_token", "")
                if not isinstance(token, str):
                    raise ValueError("Invalid OSV pagination token")
                if token:
                    if (key, token) in seen_tokens:
                        raise ValueError("Repeated OSV pagination token")
                    seen_tokens.add((key, token))
                    following.append((key, {**query, "page_token": token}))
            pending = following
    return findings


def main() -> int:
    try:
        packages = package_inventory(ROOT)
        print(f"Auditing {len(packages)} public package versions across {len(INVENTORIES)} inventories", flush=True)
        findings = advisories(packages)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"INCOMPLETE non-npm audit: {error}", file=sys.stderr)
        return 2
    for key, identifiers in sorted(findings.items()):
        print(f"REVIEW {key[0]} {key[1]} {key[2]}: {', '.join(sorted(identifiers))} ({', '.join(sorted(packages[key]))})")
    if findings:
        print(f"Found advisory matches on {len(findings)} package versions. Review scope and reachability.")
        return 1
    print("PASS: no OSV advisory matches in these exact public package inventories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
