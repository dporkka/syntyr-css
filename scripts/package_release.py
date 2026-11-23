"""Create a deterministic, minimal SYNTYR CSS release without third-party tools.

Only allowlisted public MIT artifacts are packaged; business drafts and development
files are deliberately omitted. This script refuses to bundle stale compiled CSS.
"""
import argparse
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

if __package__:
    from .build import all_distributions, javascript_distributions
else:
    from build import all_distributions, javascript_distributions

ROOT = Path(__file__).resolve().parents[1]
# One source of truth: scripts/build.py defines public CSS entrypoints.
FILES = (
    "LICENSE",
    "README.md",
    "DESIGN.md",
    "ARCHITECTURE.md",
    "docs/distribution.md",
    "docs/api-stability.md",
    "docs/animation.md",
    "docs/clipboard.md",
    "docs/ai-quickstart.md",
    "docs/agent-integration.md",
    "docs/components.md",
    "docs/recipes.md",
    "docs/component-recipes.md",
    "docs/component-recipes.html",  # Offline integration guide for packaged form-state example.
    "docs/email-components.md",
    "examples/email.html",
    "examples/saas.html",  # Offline-openable, no external assets or scripts.
    "examples/form-state-contracts.html",  # Native server-supplied form states.
    "examples/preset-preview.html",
    "examples/resource-outline.html",  # Script-free native navigation demo.
    "examples/command-launcher.html",
    "examples/command-launcher.mjs",  # Optional copy-owned navigation adapter.
    "examples/query-review.html",  # Native server-rendered filter/review composition.
    "examples/resizable-workspace.html",
    "examples/resizable-workspace.mjs",
    "examples/animation.html",
    "examples/animation-demo.mjs",  # One local CSS file per named preset.
    "examples/copy.html",
    "examples/copy-demo.mjs",
    "docs/native-patterns.md",
    "docs/radix-integration.md",
    "docs/framework-integrations.md",
    "docs/htmx-components.md",
    "integrations/htmx/syntyr.htmx.css",
    "docs/site-builders.md",
    "examples/platform-embed.html",
    "integrations/wordpress/syntyr-enqueue.php",
    "integrations/shopify/sections/syntyr-feature.liquid",
    "docs/headless-interactions.md",
    "integrations/headless/interactions.css",
    "docs/native-browser-apis.md",
    "docs/dropdowns.md",
    "docs/theme-customization.md",
    "docs/visual-intensity.md",
    "docs/accessibility.md",
    "docs/viz.md",
    "docs/geo.md",
    "examples/geo.html",
    "llms.txt",
    "llms-full.txt",
    "llms-components.txt",
    "llms-frameworks.txt",
    "metadata/components.json",
    "metadata/component-gallery.v1.json",
    "metadata/css-contract.v1.json",
    "agents/syntyr/SKILL.md",
    "docs/editor-integration.md",
    "metadata/syntyr-api.json",
    "metadata/syntyr.html-custom-data.json",
    "metadata/syntyr.css-custom-data.json",
    "metadata/syntyr.code-snippets",

) + tuple(f"dist/{name}" for name in all_distributions()) + tuple(
    f"dist/{name}" for name in javascript_distributions()
) + (
    "terminal/palettes.json",
    "integrations/dropdown/menu.mjs",
)


def package(output: Path) -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version or "/" in version or "\\" in version:
        raise ValueError("Invalid VERSION")
    subprocess.run([sys.executable, str(ROOT / "scripts/build.py"), "--check"],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_agent_docs.py"), "--check"],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/sync_design_md.py"), "--check"],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/export_api_metadata.py"), "--check"],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_component_gallery.py"), "--check"],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in FILES:
            source = ROOT / relative
            contents = source.read_bytes()
            info = ZipInfo(f"syntyr-css-{version}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o100644 << 16)
            archive.writestr(info, contents, compress_type=ZIP_DEFLATED, compresslevel=9)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", help="output ZIP path")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    target = args.output or ROOT / "release" / f"syntyr-css-{version}.zip"
    package(target)
    print(f"Packaged {len(FILES)} files in {target}")
