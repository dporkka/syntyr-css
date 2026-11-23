"""Build reproducible modular CSS distributions using only Python's standard library.

No compiler, minifier, runtime JS, network access, or package-manager install.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src'
DIST = ROOT / 'dist'
COMPONENTS = (
    'components/layout.css', 'components/typography.css',
    'components/buttons.css', 'components/forms.css',
    'components/form-composition.css', 'components/overlays.css', 'components/data.css', 'components/patterns.css',
)

def assemble(paths):
    return '\n'.join((SOURCE / path).read_text(encoding='utf-8').strip() for path in paths) + '\n'

def assemble_embed(paths):
    '''Generate unlayered scoped CSS for CSS-in-CMS integration.

    Unlayered CMS theme declarations take precedence over all normal
    declarations in CSS cascade layers. Reuse the same source components
    but remove their outer layers for sites with an existing theme.
    '''
    parts = []
    for path in paths:
        source = (SOURCE / path).read_text(encoding='utf-8').strip()
        source = re.sub(
            r'(?m)^@layer syn\.[\w-]+(?:, syn\.[\w-]+)*;\s*\n',
            '', source,
        )
        matches = list(re.finditer(r'(?m)^@layer syn\.[\w-]+\s*\{', source))
        if len(matches) != 1 or not source.endswith('}'):
            raise ValueError(f'Expected exactly one outer CSS layer in {path}')
        match = matches[0]
        content = source[:match.start()] + source[match.end():source.rfind('}')]
        if re.search(r'@layer\b', re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)):
            raise ValueError(f'Unexpected nested layer in {path}')
        parts.append(content.strip())
    return '\n'.join(parts) + '\n'


def preset_distributions():
    """Named standalone presets, assembled from existing CSS; never runtime imports.

    A preset owns a complete cascade (tokens, base, core components, semantic
    defaults). Themes remain token-driven and are NOT theme-specific CSS forks.
    The order is canonical and follows the established cascade layer order.
    """
    core = ('tokens.css', 'base.css') + COMPONENTS
    return {
        'presets/minimal.css': core + ('semantic.css',),
        'presets/saas.css': core + ('semantic.css', 'recipes.css',
                                   'native-recipes.css', 'server.css', 'utilities.css'),
        'presets/cinematic.css': core + ('semantic.css', 'recipes.css',
                                        'geometry.css', 'symbols.css', 'effects.css',
                                        'motion.css'),
    }


def css_contract():
    """Deterministic release artifact manifest; schema v1 != stable CSS API v1."""
    preset_entries = {}
    for name, sources in preset_distributions().items():
        contents = assemble(sources).encode('utf-8')
        key = Path(name).stem
        preset_entries[key] = {
            'file': 'dist/' + name,
            'sources': list(sources),
            'sha256': hashlib.sha256(contents).hexdigest(),
            'raw_bytes': len(contents),
            'gzip_bytes': len(gzip.compress(contents, mtime=0)),
        }
    return {
        'schema_version': 1,
        'library_version': (ROOT / 'VERSION').read_text(encoding='utf-8').strip(),
        'api_stability': 'experimental-pre-1.0',
        'runtime': 'css-only',
        'presets': preset_entries,
    }



def css_contract_matches(expected: dict, stored: object) -> bool:
    """Verify stable release metadata without requiring identical zlib output.

    gzip_bytes is an informational size estimate: zlib versions can yield
    different lengths for identical source. Validate its shape/range but keep
    source inventory, raw byte count, and SHA256 byte-exact.
    """
    if not isinstance(stored, dict) or stored.keys() != expected.keys():
        return False
    if {k: v for k, v in stored.items() if k != "presets"} != {
            k: v for k, v in expected.items() if k != "presets"}:
        return False
    presets = stored.get("presets")
    if not isinstance(presets, dict) or presets.keys() != expected["presets"].keys():
        return False
    for name, reference in expected["presets"].items():
        actual = presets[name]
        if not isinstance(actual, dict) or actual.keys() != reference.keys():
            return False
        zipped = actual.get("gzip_bytes")
        if type(zipped) is not int or not (0 < zipped <= reference["raw_bytes"]):
            return False
        if {k: v for k, v in actual.items() if k != "gzip_bytes"} != {
                k: v for k, v in reference.items() if k != "gzip_bytes"}:
            return False
    return True

def distributions():
    core = ('tokens.css', 'base.css') + COMPONENTS
    primary = {
        'syntyr.core.css': core,
        'syntyr.embed.css': core,  # Unlayered scoped core for existing host themes.
        'syntyr.semantic.css': ('semantic.css',),
        'syntyr.server.css': ('server.css',),
        'syntyr.semantic-bundle.css': core + ('semantic.css',),
        'syntyr.recipes.css': ('recipes.css',),
        'syntyr.media.css': ('media.css',),
        'syntyr.native-recipes.css': ('native-recipes.css',),
        'syntyr.email.css': ('email.css',),
        'syntyr.effects.css': ('effects.css',),
        'syntyr.motion.css': ('motion.css',),
        'syntyr.geometry.css': ('geometry.css',),
        'syntyr.symbols.css': ('symbols.css',),
        'syntyr.viz.css': ('viz.css',),
        'syntyr.geo.css': ('geo.css',),
        'syntyr.data-grid.css': ('data-grid.css',),
        'syntyr.agent.css': ('agent.css',),
        'syntyr.utilities.css': ('utilities.css',),
        'syntyr.print.css': ('print.css',),
        'syntyr.css': core + ('effects.css',),
        'syntyr.all.css': core + ('semantic.css', 'recipes.css', 'native-recipes.css', 'email.css', 'geometry.css', 'symbols.css', 'effects.css', 'motion.css', 'viz.css', 'geo.css', 'data-grid.css', 'agent.css', 'utilities.css', 'print.css', 'server.css'),
        **preset_distributions(),
    }
    return primary


def component_distributions():
    """Standalone CSS files for explicit per-component imports, never runtime imports.

    A consumer must load components/tokens.css, components/base.css, then
    selected components/*.css. Component order follows COMPONENTS.
    """
    files = ("tokens.css", "base.css") + COMPONENTS
    return {"components/" + Path(name).name: (name,) for name in files}


def all_distributions():
    """Complete, publicly shipped CSS registry (bundles + atomic files)."""
    return {**distributions(), **component_distributions()}


def javascript_distributions():
    # Optional native ESM. Distributed unchanged, never imported by CSS.
    return {
        'syntyr.animate.mjs': 'animate.mjs', 'syntyr.animate.d.mts': 'animate.d.mts',
        'syntyr.copy.mjs': 'copy.mjs', 'syntyr.copy.d.mts': 'copy.d.mts',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='fail if committed dist is stale')
    args = parser.parse_args()
    failed = False
    for name, inputs in all_distributions().items():
        output = (assemble_embed(inputs) if name == 'syntyr.embed.css' else assemble(inputs)).encode('utf-8')
        path = DIST / name
        zipped = len(gzip.compress(output, mtime=0))
        if args.check:
            match = path.exists() and path.read_bytes() == output
            print(f'{"OK" if match else "STALE"} {name}: {len(output)} raw / {zipped} gzip')
            failed |= not match
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(output)
            print(f'WROTE {name}: {len(output)} raw / {zipped} gzip')
    for name, source in javascript_distributions().items():
        output = (SOURCE / source).read_bytes()
        path = DIST / name
        zipped = len(gzip.compress(output, mtime=0))
        if args.check:
            match = path.exists() and path.read_bytes() == output
            print(f'{"OK" if match else "STALE"} {name}: {len(output)} raw / {zipped} gzip')
            failed |= not match
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(output)
            print(f'WROTE {name}: {len(output)} raw / {zipped} gzip')

    contract_path = ROOT / 'metadata' / 'css-contract.v1.json'
    contract_bytes = (json.dumps(css_contract(), indent=2, sort_keys=True) + '\n').encode('utf-8')
    if args.check:
        try:
            stored_contract = json.loads(contract_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, ValueError):
            stored_contract = None
        match = css_contract_matches(css_contract(), stored_contract)
        print(f'{"OK" if match else "STALE"} metadata/css-contract.v1.json')
        failed |= not match
    else:
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_bytes(contract_bytes)
        print('WROTE metadata/css-contract.v1.json')
    return int(failed)

if __name__ == '__main__':
    sys.exit(main())
