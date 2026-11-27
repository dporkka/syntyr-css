#!/usr/bin/env python3
"""Offline, optional agent onboarding and pinned-release HTML checks for Syntyr.

Run from a Syntyr source checkout. No consumer runtime or Python dependency is
installed; the output can be copied to applications using any HTML renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_mcp.catalog import CANDIDATE, MAX_HTML_CHARS, PUBLISHED, RELEASES, SyntyrCatalog  # noqa: E402
from agent_mcp.html_inspector import inspect_markup, plan_variants, plan_source_patches  # noqa: E402
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
    def safe_target(rel: Path) -> Path:
        target = project / rel
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent != project):
            raise ValueError(f'Refusing symlinked output path: {target}')
        if any(parent.exists() and not parent.is_dir() for parent in target.parents):
            raise ValueError(f'Refusing non-directory output ancestor: {target}')
        if target.exists() and not target.is_file():
            raise ValueError(f'Refusing non-file output path: {target}')
        return target

    conflicts = []
    for rel, content in planned.items():
        target = safe_target(rel)
        if target.exists() and target.read_bytes() != content:
            conflicts.append(str(rel))
    if conflicts:
        return 1, {'error': 'Existing files differ; no files were changed', 'conflicts': sorted(conflicts)}
    written = []
    for rel, content in planned.items():
        target = safe_target(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target = safe_target(rel)
        if target.exists():
            if target.read_bytes() != content:
                raise ValueError(f'File changed during installation: {rel}')
            continue
        # Exclusive creation prevents a concurrent file or symlink from being overwritten.
        with target.open('xb') as stream:
            stream.write(content)
        written.append(rel.as_posix())
    return 0, {'status': config['release_status'], 'release': config['release'],
               'created': written, 'unchanged': len(planned) - len(written),
               'next_step': 'Load versioned CSS into your app; the Skill describes framework-specific markup and limits.'}


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
    planned, expected = _planned_files(project, release, 'generic', catalog)
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
    # Compare against bytes generated by the trusted source checkout, not a
    # checksum supplied by the installed project. Preserve existing v1 configs.
    agent_artifacts = []
    for name, relative, original in [
            ('agent-skill', skill, expected['agent_skill']),
            ('api-reference', config['api_reference'], expected['api_reference'])]:
        target = project / relative
        expected_hash = _hash(planned[Path(original)])
        if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != project):
            integrity = 'symlink'
        elif not target.is_file():
            integrity = 'missing'
        elif _hash(target.read_bytes()) != expected_hash:
            integrity = 'modified'
        else:
            integrity = 'verified'
        agent_artifacts.append({'name': name, 'path': relative, 'sha256': expected_hash, 'integrity': integrity})
        if integrity != 'verified':
            diagnostics.append({'code': integrity+'-'+name, 'file': relative,
                                'severity': 'error',
                                'message': f'{name}: {integrity}; compare with the trusted source checkout'})
    return (1 if diagnostics else 0), {
        'schema_version': 1, 'status': 'degraded' if diagnostics else 'healthy',
        'release': release, 'release_status': expected['release_status'],
        'stylesheets': list(DEFAULT_SHEETS), 'assets': assets,
        'agent_skill': skill, 'api_reference': config['api_reference'],
        'agent_artifacts': agent_artifacts,
        'themes': catalog.get_theme_tokens(release=release)['themes'],
        'css_usage_verified': False, 'diagnostics': diagnostics,
        'limitations': 'Read-only inventory verifies pinned files, not CSS inclusion, application behavior, or accessibility.',
    }


def check(args: argparse.Namespace, catalog: SyntyrCatalog) -> tuple[int, dict]:
    project = _safe_project(Path(args.project))
    status, inventory = info(args, catalog)
    if status == 2:
        raise ValueError('Missing syntyr.agent.json; run init first')
    release = inventory['release']
    diagnostics = list(inventory['diagnostics'])
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


def _read_inspector_html(file: str) -> str:
    # Preserve CRLF and exact UTF-8 bytes so the digest agrees with standalone Go.
    with Path(file).open(encoding="utf-8", newline="") as source:
        return source.read(MAX_HTML_CHARS + 1)


def inspect_html(args: argparse.Namespace, catalog: SyntyrCatalog) -> tuple[int, dict]:
    return 0, inspect_markup(_read_inspector_html(args.file), args.release, args.selector)


def _read_plan_request(file: str) -> dict:
    with Path(file).open(encoding="utf-8") as source:
        raw = source.read(16385)
    if len(raw) > 16384:
        raise ValueError("Plan request exceeds 16,384 characters")
    request = json.loads(raw)
    if not isinstance(request, dict) or set(request) != {"document_sha256", "operations"}:
        raise ValueError("Expected document_sha256 and operations in plan request")
    return request


def plan_html(args: argparse.Namespace, catalog: SyntyrCatalog) -> tuple[int, dict]:
    request = _read_plan_request(args.request)
    planner = plan_source_patches if args.source_patches else plan_variants
    return 0, planner(_read_inspector_html(args.file), args.release,
                      request["document_sha256"], request["operations"])


def apply_html(args: argparse.Namespace, catalog: SyntyrCatalog) -> tuple[int, dict]:
    """Materialize a freshly verified, approved candidate without overwriting anything."""
    source = Path(args.file).absolute()
    output = Path(args.output).absolute()
    if source.suffix.lower() != ".html" or output.suffix.lower() != ".html":
        raise ValueError("Source and output must be .html files")
    if any(p.is_symlink() for path in (source, output) for p in (path, *path.parents)):
        raise ValueError("Symlink paths are not supported")
    if not stat.S_ISREG(source.stat().st_mode) or not output.parent.is_dir():
        raise ValueError("Expected a regular HTML source and existing output directory")
    if output.exists():
        raise ValueError("Refusing to overwrite an existing output")
    request = _read_plan_request(args.request)
    html = _read_inspector_html(str(source))
    plan = plan_source_patches(html, args.release, request["document_sha256"], request["operations"])
    if not plan["combined_dom_verified"] or not plan["validation"]["valid"]:
        raise ValueError("Candidate failed combined proof or static validation")
    if args.approve_result_sha256 != plan["result_sha256"]:
        raise ValueError("Approval digest mismatch; review a fresh source-patch preview")
    data = html.encode("utf-8")
    candidate = data
    for patch in reversed(plan["patches"]):
        start, end = patch["start_byte"], patch["end_byte"]
        if data[start:end] != patch["expected"].encode("ascii"):
            raise ValueError("Patch precondition mismatch")
        candidate = candidate[:start] + patch["replacement"].encode("ascii") + candidate[end:]
    if _hash(candidate) != args.approve_result_sha256:
        raise ValueError("Candidate digest mismatch")
    # Exclusive publication via a hard link in the same directory. The output
    # never appears partially written and an existing path is never replaced.
    # Assumes a trusted local directory; this is not a hostile-filesystem sandbox.
    temporary = None
    published = False
    cleanup_warning = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".syntyr-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(candidate)
            handle.flush()
            os.fsync(handle.fileno())
        if source.is_symlink() or _read_inspector_html(str(source)).encode("utf-8") != data:
            raise ValueError("Source changed during planning")
        os.link(temporary, output)
        published = True
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as exc:
                if not published:
                    raise
                cleanup_warning = f"Candidate created; could not remove staging file {temporary}: {exc}"
    payload = {"status": "created", "output": str(output), "source_unchanged": True,
               "document_sha256": plan["document_sha256"], "result_sha256": plan["result_sha256"],
               "combined_dom_verified": True, "validation": plan["validation"]}
    if cleanup_warning is not None:
        payload["cleanup_warning"] = cleanup_warning
    return 0, payload


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
    markup = sub.add_parser('inspect-html', help='Inspect literal candidate HTML using the optional configured Go inspector')
    markup.add_argument('--release', required=True, choices=[CANDIDATE])
    markup.add_argument('--selector', default='')
    markup.add_argument('--json', action='store_true')
    markup.add_argument('file')
    plan = sub.add_parser('plan-html', help='Preview bounded variant replacements without writing source')
    plan.add_argument('--release', required=True, choices=[CANDIDATE])
    plan.add_argument('--request', required=True, help='Local JSON plan request')
    plan.add_argument('--source-patches', action='store_true', help='Preview exact source edits and static validation')
    plan.add_argument('--json', action='store_true')
    plan.add_argument('file')
    apply = sub.add_parser('apply-html', help='Create a new approved HTML candidate; never overwrite source')
    apply.add_argument('--release', required=True, choices=[CANDIDATE])
    apply.add_argument('--request', required=True)
    apply.add_argument('--approve-result-sha256', required=True)
    apply.add_argument('--output', required=True)
    apply.add_argument('--json', action='store_true')
    apply.add_argument('file')
    args = parser.parse_args(argv)
    try:
        catalog = SyntyrCatalog()
        handlers = {'init': initialize, 'check': check, 'info': info, 'inspect-html': inspect_html, 'plan-html': plan_html, 'apply-html': apply_html}
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
