"""Prepare a static website for a hosting provider; never publish implicitly.

Standard-library-only. Nulang Cloud is explicitly experimental and produces an
offline bundle until the Cloud platform exposes a qualified static-site API.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import ipaddress
import os
import json
import re
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Protocol
from urllib.parse import urlsplit
from zipfile import ZIP_STORED, ZipFile, ZipInfo


class DeploymentError(ValueError):
    """Unsafe input or unsupported deployment operation."""


_ALLOWED_DOTFILES = frozenset({".nojekyll", ".syntyr-site-manifest.json"})
_FORBIDDEN_BASENAMES = frozenset({
    ".git", ".env", ".npmrc", ".pypirc", ".ssh", ".aws", ".npm",
    "id_rsa", "id_ed25519", "credentials", "credentials.json",
    "secrets.json", "secrets.yml", "secrets.yaml", "credentials.yaml",
    "credentials.yml", ".htpasswd", ".ds_store",
})
# These are repository/source directories, not reviewed static build outputs.
# Assets in an intentional release build should live in public/ or assets/.
_PRIVATE_SOURCE_DIRS = frozenset({
    "business", "tests", "test", "src", "node_modules", "scripts",
    "tools", "experiments", "benchmarks", "private", "internal", "secrets",
    "site-releases", ".github", ".woodpecker", ".venv", "venv",
})


def _safe_hostname(hostname: str | None) -> bool:
    if not hostname or "%" in hostname:
        # Scoped IPv6 addresses may contain characters unsafe in HTML attrs.
        return False
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    # No URI punctuation or HTML meta-attribute delimiters in a DNS hostname.
    # Internationalized hostnames can be supplied in ASCII/Punycode form.
    if len(hostname) > 253 or not re.fullmatch(r"[a-zA-Z0-9.-]+", hostname):
        return False
    labels = hostname.removesuffix(".").split(".")
    return all(label and len(label) <= 63 and label[0].isalnum() and label[-1].isalnum()
               for label in labels)


def validate_site_url(value: str) -> str:
    """Accept only an HTTPS origin, never paths, credentials or query data."""
    # urlsplit strips some leading C0 controls before parsing, which can
    # silently introduce invalid bytes into generated XML/HTML metadata.
    if any(ord(char) < 0x20 or ord(char) == 0x7f for char in value):
        raise DeploymentError("site URL contains ASCII control characters")
    try:
        parsed = urlsplit(value)
        valid = (
            parsed.scheme == "https" and _safe_hostname(parsed.hostname)
            and not parsed.username and not parsed.password
            and parsed.path in ("", "/") and not parsed.query and not parsed.fragment
            and parsed.port in (None, 443)
            and "?" not in value and "#" not in value
            and not any(char.isspace() for char in value)
        )
    except ValueError:
        valid = False
    if not valid:
        raise DeploymentError("site URL must be a bare HTTPS origin (no path, query or credentials)")
    return value.rstrip("/")


def _validate_output(site_dir: Path, output: Path) -> Path:
    if output.is_symlink():
        raise DeploymentError(f"output already exists: {output}")
    destination = output.resolve(strict=False)
    if destination.exists() or destination.is_symlink():
        raise DeploymentError(f"output already exists: {destination}")
    if destination == site_dir or destination.is_relative_to(site_dir):
        raise DeploymentError("output must be outside the source website directory")
    if not destination.parent.is_dir():
        raise DeploymentError(f"output parent directory does not exist: {destination.parent}")
    return destination


def _site_paths(directory: Path):
    """Yield source entries in sorted order and propagate every scan error."""
    with os.scandir(directory) as entries:
        children = sorted(entries, key=lambda entry: entry.name)
    for entry in children:
        path = Path(entry.path)
        yield path
        if entry.is_dir(follow_symlinks=False):
            yield from _site_paths(path)


@dataclass(frozen=True)
class StaticSite:
    source: Path
    files: tuple[tuple[str, bytes], ...]

    @classmethod
    def load(cls, directory: Path) -> "StaticSite":
        if directory.is_symlink() or not directory.is_dir():
            raise DeploymentError(f"not a real static site directory: {directory}")
        directory = directory.resolve()
        assets: list[tuple[str, bytes]] = []
        for path in _site_paths(directory):
            relative = path.relative_to(directory)
            if path.is_symlink():
                raise DeploymentError(f"site includes symlink: {relative}")
            if relative.parts[0].lower() in _PRIVATE_SOURCE_DIRS:
                raise DeploymentError(f"disallowed private source directory in site: {relative}")
            for part in relative.parts:
                folded = part.lower()
                if (folded in _FORBIDDEN_BASENAMES or folded.startswith(".env")
                        or folded.endswith((".pem", ".key", ".p12", ".pfx"))
                        or (part.startswith(".") and part not in _ALLOWED_DOTFILES
                            and part != ".well-known")):
                    raise DeploymentError(f"disallowed file or directory in site: {relative}")
            if path.is_dir():
                continue
            if not path.is_file():
                raise DeploymentError(f"not a regular site file: {relative}")
            if any(char in relative.as_posix() for char in ("\\", "\n", "\r")):
                raise DeploymentError(f"unsafe filename: {relative}")
            assets.append((relative.as_posix(), path.read_bytes()))
        if not any(name == "index.html" for name, _ in assets):
            raise DeploymentError("site root must contain index.html")
        return cls(directory, tuple(assets))


class StaticSiteProvider(Protocol):
    def prepare(self, site: StaticSite, output: Path, site_url: str) -> dict[str, str]:
        ...


class CloudflareDirectoryProvider:
    """Stage identical bytes for Cloudflare Pages / Workers Static Assets."""

    def prepare(self, site: StaticSite, output: Path, site_url: str) -> dict[str, str]:
        origin = validate_site_url(site_url)
        destination = _validate_output(site.source, output)
        destination.mkdir()
        try:
            for name, payload in site.files:
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
        except Exception:
            shutil.rmtree(destination)
            raise
        return {"provider": "cloudflare", "status": "prepared_only",
                "origin": origin, "output": str(destination)}


def _write_zip(zipped: ZipFile, name: str, content: bytes) -> None:
    info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_STORED
    info.external_attr = 0o100644 << 16
    zipped.writestr(info, content)


class NulangCloudBundleProvider:
    """Experimental offline bundle. NOT a deploy API or production integration."""

    def prepare(self, site: StaticSite, output: Path, site_url: str) -> dict[str, str]:
        origin = validate_site_url(site_url)
        destination = _validate_output(site.source, output)
        if any(name in {"_headers", "_redirects"} for name, _ in site.files):
            raise DeploymentError(
                "Cloudflare _headers/_redirects cannot be preserved in a Nulang Cloud bundle; "
                "export a portable build and configure security headers on the host"
            )
        manifest = {
            "schema": "syntyr.static-site.bundle/v1",
            "provider": "nulang-cloud",
            "status": "prepared_only",
            "origin": origin,
            "files": [
                {"path": name, "bytes": len(data),
                 "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in site.files
            ],
        }
        # Build privately in the destination filesystem. An exclusive hard link
        # publishes only a complete archive and never replaces a competing file.
        temporary_path = None
        cleanup_warning = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w+b", prefix=".syntyr-", suffix=".tmp",
                dir=destination.parent, delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                with ZipFile(temporary, "w") as zipped:
                    for name, payload in site.files:
                        _write_zip(zipped, f"site/{name}", payload)
                    _write_zip(zipped, "syntyr-deploy.json",
                               (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
                temporary.flush()
                os.fsync(temporary.fileno())
            os.link(temporary_path, destination)  # Fails atomically if present.
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError as exc:
                    # The exclusive hard link may have already committed a
                    # complete ZIP. Do not turn a successful publish-to-path
                    # into a reported failure or mask an earlier ZIP error.
                    cleanup_warning = f"temporary bundle cleanup failed for {temporary_path}: {exc}"
                    print(f"Warning: {cleanup_warning}", file=sys.stderr)
        receipt = {"provider": "nulang-cloud", "status": "prepared_only",
                   "origin": origin, "output": str(destination)}
        if cleanup_warning:
            receipt["cleanup_warning"] = cleanup_warning
        return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", required=True, type=Path, help="Reviewed static build output, not repo root")
    parser.add_argument("--site-url", required=True, help="Public HTTPS origin of the resulting website")
    parser.add_argument("--output", required=True, type=Path, help="New staging directory or ZIP path")
    parser.add_argument("--provider", choices=("cloudflare", "nulang-cloud"), required=True)
    parser.add_argument("--experimental-nulang-cloud", action="store_true")
    parser.add_argument("--publish", action="store_true", help="Reserved for a future live integration")
    args = parser.parse_args(argv)
    try:
        # No HTTP upload or credential handling until a real, tested Cloud API exists.
        if args.publish:
            raise DeploymentError("live publish is not supported by this preparation-only CLI")
        if args.provider == "nulang-cloud" and not args.experimental_nulang_cloud:
            raise DeploymentError("Nulang Cloud is experimental; pass --experimental-nulang-cloud to prepare an offline bundle")
        provider: StaticSiteProvider = (
            CloudflareDirectoryProvider() if args.provider == "cloudflare"
            else NulangCloudBundleProvider()
        )
        receipt = provider.prepare(StaticSite.load(args.site_dir), args.output, args.site_url)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    except (DeploymentError, OSError) as exc:
        print(f"Deployment preparation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
