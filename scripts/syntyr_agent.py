#!/usr/bin/env python3
"""Offline, optional agent onboarding and pinned-release HTML checks for Syntyr.

Run from a Syntyr source checkout. No consumer runtime or Python dependency is
installed; the output can be copied to applications using any HTML renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_mcp.catalog import PUBLISHED, RELEASES, SyntyrCatalog  # noqa: E402
from scripts.syntyr_check import validate_html  # noqa: E402

DEFAULT_SHEETS = ('syntyr.core.css', 'syntyr.recipes.css')
AGENT_PATHS = {
    'auto': '.agents/skills/syntyr',
    'codex': '.agents/skills/syntyr',
    'claude': '.claude/skills/syntyr',
    'cursor': '.cursor/skills/syntyr',
    'generic': '.agents/skills/syntyr',
}
SKIP_DIRS = {'.git', '.next', '.nuxt', '.svelte-kit', 'node_modules', 'dist', 'build', 'vendor', '.venv', '.agents', '.claude', '.cursor'}


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_project(root: Path) -> Path:
    project = root.expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f'Project directory does not exist: {root}')
    return project


def _agent_reference(catalog: SyntyrCatalog, release: str) -> bytes:
    info = catalog._catalog(release)  # derived from immutable published/source CSS
    classes = sorted(set().union(*(info['files'][name]['classes'] for name in DEFAULT_SHEETS)))
    components = catalog.search_components(release=release)['components']
    components = [c for c in components if set(c['stylesheets']).issubset(DEFAULT_SHEETS)]
    themes = catalog.get_theme_tokens(release=release)['themes']
    return (json.dumps({
        'schema_version': 1, 'release': release,
        'status': 'published' if release == PUBLISHED else 'unreleased_candidate',
        'stylesheets': list(DEFAULT_SHEETS), 'themes': themes,
        'classes': classes, 'components': components,
        'note': 'Curated components; CSS classes listed are validated against the selected release.',
    }, sort_keys=True, indent=2) + '\n').encode()


def _planned_files(project: Path, release: str, agent: str, catalog: SyntyrCatalog) -> tuple[dict[Path, bytes], dict]:
    if release not in RELEASES:
        raise ValueError(f'Unsupported release: {release}. Choose: {", ".join(RELEASES)}')
    source_dir = catalog._directory(release)
    assets_dir = Path('vendor') / 'syntyr' / release
    skill_dir = Path(AGENT_PATHS[agent])
    planned = {}
    checksums = {}
    for name in DEFAULT_SHEETS:
        content = (source_dir / name).read_bytes()
        planned[assets_dir / name] = content
        checksums[name] = _hash(content)
    planned[skill_dir / 'SKILL.md'] = (ROOT / 'agents/syntyr/SKILL.md').read_bytes()
    planned[skill_dir / 'references/api.json'] = _agent_reference(catalog, release)
    config = {
        'schema_version': 1,
        'release': release,
        'release_status': 'published' if release == PUBLISHED else 'unreleased_candidate',
        'assets_dir': assets_dir.as_posix(),
        'stylesheets': list(DEFAULT_SHEETS),
        'sha256': checksums,
        'agent_skill': (skill_dir / 'SKILL.md').as_posix(),
        'api_reference': (skill_dir / 'references/api.json').as_posix(),
    }
    planned[Path('syntyr.agent.json')] = (json.dumps(config, indent=2, sort_keys=True) + '\n').encode()
    return planned, config


def initialize(args: argparse.Namespace, catalog: SyntyrCatalog) -> tuple[int, dict]:
    project = _safe_project(Path(args.project))
    planned, config = _planned_files(project, args.release, args.agent, catalog)
    # Abort before any writes: never clobber consumer-owned changes or follow output symlinks.
    for rel in planned:
        target = project / rel
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent != project):
            raise ValueError(f'Refusing symlinked output path: {target}')
    conflicts = sorted(str(rel) for rel, content in planned.items()
                       if (project / rel).exists() and (project / rel).read_bytes() != content)
    if conflicts:
        return 1, {'error': 'Existing files differ; no files were changed', 'conflicts': conflicts}
    written = []
    for rel, content in planned.items():
        target = project / rel
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        written.append(rel.as_posix())
    return 0, {'status': config['release_status'], 'release': config['release'],
               'created': written, 'unchanged': len(planned) - len(written),
               'next_step': 'Load versioned CSS into your app; the Skill describes framework-specific markup and limits.'}


def _check_asset_integrity(project: Path, config: dict, diagnostics: list[dict]) -> None:
    for sheet in config['stylesheets']:
        asset = project / config['assets_dir'] / sheet
        if not asset.is_file():
            diagnostics.append({'file': str(asset), 'code': 'missing-asset',
                                'severity': 'error', 'message': f'Missing configured {sheet}'})
        elif _hash(asset.read_bytes()) != config['sha256'][sheet]:
            diagnostics.append({'file': str(asset), 'code': 'modified-asset',
                                'severity': 'error', 'message': f'{sheet} differs from pinned CSS asset'})


def _html_files(project: Path) -> list[Path]:
    files = []
    for p in project.rglob('*.html'):
        if not any(part in SKIP_DIRS for part in p.relative_to(project).parts[:-1]):
            files.append(p)
    return sorted(files)


def _valid_agent_paths(skill: str, reference: str, *, path_cls=Path) -> bool:
    """Match the installer POSIX metadata independent of host OS separators."""
    if not isinstance(skill, str) or not isinstance(reference, str):
        return False
    allowed = {(path_cls(path) / 'SKILL.md').as_posix() for path in AGENT_PATHS.values()}
    return (skill in allowed
            and reference == (path_cls(skill).parent / 'references/api.json').as_posix())


def info(args: argparse.Namespace, catalog: SyntyrCatalog) -> tuple[int, dict]:
    """Report only verified installation facts; never guess at host CSS imports."""
    project = _safe_project(Path(args.project))
    config_file = project / 'syntyr.agent.json'
    if config_file.is_symlink():
        raise ValueError('Refusing symlinked Syntyr configuration')
    if not config_file.is_file():
        return 2, {
            'schema_version': 1, 'status': 'unconfigured', 'css_usage_verified': False,
            'diagnostics': [], 'next_step': 'Run syntyr-agent init in this project to pin a release.'
        }
    config = json.loads(config_file.read_text(encoding='utf-8'))
    if not isinstance(config, dict):
        raise ValueError('Syntyr configuration must be an object')
    release = config.get('release')
    if release not in RELEASES:
        raise ValueError('Unsupported configured Syntyr release')
    _planned, expected = _planned_files(project, release, 'generic', catalog)
    skill = config.get('agent_skill')
    if (config.get('schema_version') != 1
            or config.get('stylesheets') != list(DEFAULT_SHEETS)
            or config.get('assets_dir') != expected['assets_dir']
            or config.get('sha256') != expected['sha256']
            or not _valid_agent_paths(skill, config.get('api_reference'))):
        raise ValueError('Invalid or inconsistent syntyr.agent.json; rerun init with a clean config')

    diagnostics = []
    assets = []
    for name in DEFAULT_SHEETS:
        relative = Path(config['assets_dir']) / name
        asset = project / relative
        if asset.is_symlink() or any(p.is_symlink() for p in asset.parents if p != project):
            integrity, code = 'unsafe', 'symlink-asset'
        elif not asset.is_file():
            integrity, code = 'missing', 'missing-asset'
        elif _hash(asset.read_bytes()) != config['sha256'][name]:
            integrity, code = 'modified', 'modified-asset'
        else:
            integrity, code = 'verified', None
        assets.append({
            'name': name, 'path': relative.as_posix(),
            'sha256': config['sha256'][name], 'integrity': integrity,
        })
        if code:
            diagnostics.append({'code': code, 'file': relative.as_posix(),
                                'severity': 'error', 'message': f'{name}: {integrity}'})
    for name, relative in [('agent-skill', skill), ('api-reference', config['api_reference'])]:
        target = project / relative
        if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != project):
            diagnostics.append({'code': 'symlink-'+name, 'file': relative, 'severity': 'error'})
        elif not target.is_file():
            diagnostics.append({'code': 'missing-'+name, 'file': relative, 'severity': 'error'})
    return (1 if diagnostics else 0), {
        'schema_version': 1, 'status': 'degraded' if diagnostics else 'healthy',
        'release': release, 'release_status': expected['release_status'],
        'stylesheets': list(DEFAULT_SHEETS), 'assets': assets,
        'agent_skill': skill, 'api_reference': config['api_reference'],
        'themes': catalog.get_theme_tokens(release=release)['themes'],
        'css_usage_verified': False, 'diagnostics': diagnostics,
        'limitations': 'Read-only inventory verifies pinned files, not CSS inclusion, application behavior, or accessibility.',
    }


def check(args: argparse.Namespace, catalog: SyntyrCatalog) -> tuple[int, dict]:
    project = _safe_project(Path(args.project))
    config_file = project / 'syntyr.agent.json'
    if not config_file.is_file():
        raise ValueError('Missing syntyr.agent.json; run init first')
    config = json.loads(config_file.read_text())
    release = config.get('release')
    if release not in RELEASES:
        raise ValueError('Unsupported configured Syntyr release')
    expected, _ = _planned_files(project, release, 'generic', catalog)
    # Validate metadata against the pinned source, not a user-supplied version or URL.
    if (config.get('stylesheets') != list(DEFAULT_SHEETS)
            or config.get('assets_dir') != f'vendor/syntyr/{release}'
            or config.get('sha256') != json.loads(expected[Path('syntyr.agent.json')])['sha256']):
        raise ValueError('Invalid or inconsistent syntyr.agent.json; rerun init with a clean config')
    diagnostics = []
    _check_asset_integrity(project, config, diagnostics)
    files = [Path(p).expanduser().resolve() for p in args.files] if args.files else _html_files(project)
    unchecked = []
    checked = []
    for path in files:
        if not path.is_file():
            diagnostics.append({'file': str(path), 'code': 'missing-input', 'severity': 'error', 'message': 'File does not exist'})
        elif path.suffix.lower() != '.html':
            unchecked.append(str(path))
        else:
            content = path.read_text(encoding='utf-8')
            # CLI accepts complete HTML files; MCP's 20-kilobyte input cap is tool-specific.
            result = validate_html(content, catalog._validation_contract(release), stylesheets=set(DEFAULT_SHEETS))
            diagnostics.extend({'file': str(path), **d} for d in result)
            checked.append(str(path))
    code = 1 if diagnostics else 2 if unchecked or not checked else 0
    return code, {'release': release, 'status': 'errors' if code == 1 else 'incomplete' if code == 2 else 'passed',
                  'checked_files': checked, 'unchecked_files': unchecked,
                  'diagnostics': diagnostics,
                  'limitations': 'Static literal HTML and pinned file integrity only. CSS inclusion, browser behavior, JSX/TSX/Vue/Svelte, and WCAG require separate verification.'}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, prog='syntyr-agent')
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Safely install an offline, versioned consumer Agent Skill and CSS')
    init.add_argument('--project', default='.')
    init.add_argument('--release', default=PUBLISHED, choices=RELEASES)
    init.add_argument('--agent', default='auto', choices=AGENT_PATHS)
    init.add_argument('--json', action='store_true')
    verify = sub.add_parser('check', help='Check pinned CSS files and literal HTML against their exact release')
    verify.add_argument('--project', default='.')
    verify.add_argument('--json', action='store_true')
    verify.add_argument('files', nargs='*')
    inspect = sub.add_parser('info', help='Read-only project inventory for agents and developers')
    inspect.add_argument('--project', default='.')
    inspect.add_argument('--json', action='store_true')
    responsive = sub.add_parser('responsive', help='Optional local rendered-page audit (Playwright required)')
    responsive.add_argument('url')
    responsive.add_argument('--browsers', nargs='+', choices=('chromium', 'firefox', 'webkit'), default=['chromium'])
    responsive.add_argument('--stress', action='store_true')
    responsive.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'responsive':
        from scripts.responsive_audit import main as audit_main
        flags = [args.url, '--browsers', *args.browsers]
        if args.stress:
            flags.append('--stress')
        if args.report:
            flags.extend(['--report', str(args.report)])
        return audit_main(flags)
    try:
        catalog = SyntyrCatalog()
        handlers = {'init': initialize, 'check': check, 'info': info}
        code, payload = handlers[args.command](args, catalog)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        code, payload = 1, {'error': str(exc)}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
