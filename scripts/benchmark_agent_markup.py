"""Reproducible static inspection of independently generated CSS framework HTML.

No model calls or output generation are hidden in this evaluator. Report only
measured submitted artifacts; do not infer WCAG compliance or agent token cost.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

# Imported as a package by tests and as a script by the local benchmark CLI.
try:
    from scripts.syntyr_check import validate_html
except ModuleNotFoundError:
    from syntyr_check import validate_html

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / 'benchmarks/agent-output/tasks.json'
CONTRACT = ROOT / 'metadata/syntyr-contract.json'
FRAMEWORKS = ('syntyr', 'tailwind', 'daisyui')
SAFE_ID = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
FORM_INPUTS = {'input', 'select', 'textarea'}
UNLABELED_TYPES = {'hidden', 'submit', 'reset', 'button', 'image'}


def validate_manifest(manifest: dict) -> None:
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1:
        raise ValueError('Expected agent task schema_version 1')
    if manifest.get('frameworks') != list(FRAMEWORKS):
        raise ValueError('Frameworks must be syntyr, tailwind, daisyui in that order')
    cases = manifest.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 50:
        raise ValueError('Expected between 1 and 50 tasks')
    ids = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get('id'), str) or not SAFE_ID.fullmatch(case['id']):
            raise ValueError('Task ids must be safe lowercase slugs')
        ids.append(case['id'])
        for field in ('required_tags', 'required_text'):
            if not isinstance(case.get(field), list) or not case[field] or any(
                    not isinstance(item, str) or not item.strip() for item in case[field]):
                raise ValueError(f'Task {case["id"]!r} requires nonempty {field}')
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate task id')


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding='utf-8'))
    validate_manifest(manifest)
    return manifest


def _finding(code: str, message: str) -> dict:
    return {'code': code, 'message': message}


class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text = []
        self.classes = []
        self.class_bytes = 0
        self.ids = []
        self.label_targets = set()
        self.fields = []
        self.links = []
        self.css_links = []
        self.forms = []
        self.buttons = []
        self.images = []
        self.tables = 0
        self.captions = 0
        self.headers = 0
        self.label_depth = 0
        self.html_has_lang = False
        self.script_count = 0
        self.inline_handlers = 0

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.tags.append(tag)
        if tag == 'html':
            self.html_has_lang = bool((data.get('lang') or '').strip())
        if tag == 'label':
            self.label_depth += 1
            if data.get('for'):
                self.label_targets.add(data['for'])
        if data.get('id'):
            self.ids.append(data['id'])
        if data.get('class'):
            self.classes.extend(data['class'].split())
            self.class_bytes += len(data['class'].encode('utf-8'))
        self.inline_handlers += sum(key.startswith('on') for key in data)
        if tag in FORM_INPUTS:
            self.fields.append((tag, data, self.label_depth > 0))
        if tag == 'link' and 'stylesheet' in (data.get('rel') or '').split():
            self.css_links.append(data.get('href') or '')
        if tag == 'a':
            self.links.append(data.get('href'))
        if tag == 'form':
            self.forms.append(data)
        if tag == 'button':
            self.buttons.append(data)
        if tag == 'img':
            self.images.append(data)
        if tag == 'table':
            self.tables += 1
        if tag == 'caption':
            self.captions += 1
        if tag == 'th':
            self.headers += 1
        if tag == 'script':
            self.script_count += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == 'label':
            self.label_depth = max(0, self.label_depth - 1)

    def handle_endtag(self, tag):
        if tag == 'label':
            self.label_depth = max(0, self.label_depth - 1)

    def handle_data(self, data):
        self.text.append(data)


def inspect_html(html: str, case: dict, framework: str, *, contract: dict | None = None) -> list[dict]:
    if framework not in FRAMEWORKS:
        raise ValueError(f'Unsupported framework: {framework}')
    parser = Inspector()
    parser.feed(html)
    parser.close()
    findings = []
    tags = set(parser.tags)
    for tag in case['required_tags']:
        if tag not in tags:
            findings.append(_finding('missing-required-tag', tag))
    content = ' '.join(' '.join(parser.text).split()).casefold()
    for required in case['required_text']:
        if required.casefold() not in content:
            findings.append(_finding('missing-required-text', required))
    for tag in ('html', 'head', 'body', 'main', 'h1', 'title'):
        if tag not in tags:
            findings.append(_finding('missing-document-tag', tag))
    if not parser.html_has_lang:
        findings.append(_finding('missing-language', 'Add a nonempty html lang attribute'))
    if parser.script_count or parser.inline_handlers:
        findings.append(_finding('script-not-allowed', 'This benchmark requires no application JavaScript'))
    for name, count in Counter(parser.ids).items():
        if count > 1:
            findings.append(_finding('duplicate-id', name))
    for tag, data, wrapped in parser.fields:
        if tag == 'input' and (data.get('type') or 'text').lower() in UNLABELED_TYPES:
            continue
        if not (wrapped or (data.get('id') and data['id'] in parser.label_targets)
                or data.get('aria-label') or data.get('aria-labelledby')):
            findings.append(_finding('missing-label', f'{tag} needs a programmatic label'))
    for data in parser.forms:
        if not data.get('action') or data.get('action') == '#':
            findings.append(_finding('missing-form-action', 'Use a concrete application route'))
    for data in parser.buttons:
        if data.get('type') not in ('submit', 'button', 'reset'):
            findings.append(_finding('button-missing-type', 'Declare submit, button or reset'))
    for data in parser.images:
        if 'alt' not in data:
            findings.append(_finding('missing-image-alt', 'Provide alt, or empty alt for decoration'))
    ids = set(parser.ids)
    for href in parser.links:
        if not href or href == '#' or href.lower().startswith('javascript:'):
            findings.append(_finding('invalid-link', str(href)))
        elif href.startswith('#') and href[1:] not in ids:
            findings.append(_finding('unresolved-fragment', href))
    if parser.tables and (not parser.headers or parser.captions < parser.tables):
        findings.append(_finding('table-structure', 'Tables need headers and captions'))
    expected_css = {'syntyr': ('syntyr.css', 'syntyr.core.css', 'syntyr.all.css',
                                'syntyr.semantic-bundle.css'),
                    'tailwind': ('tailwind.css',), 'daisyui': ('daisyui.css',)}[framework]
    linked_names = {Path(urlsplit(href).path).name for href in parser.css_links}
    if not linked_names.intersection(expected_css):
        findings.append(_finding('missing-framework-css', f'Expected a {framework} stylesheet'))
    if framework == 'syntyr':
        checked = contract or json.loads(CONTRACT.read_text(encoding='utf-8'))
        for issue in validate_html(html, checked):
            findings.append(_finding('syntyr-' + issue['code'], issue['message']))
    return findings


def evaluate(root: Path, manifest: dict) -> dict:
    validate_manifest(manifest)
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    metadata_path = root / 'run.json'
    provenance = json.loads(metadata_path.read_text(encoding='utf-8')) if metadata_path.is_file() else None
    provenance_supplied = bool(isinstance(provenance, dict) and all(
        provenance.get(key) for key in ('model', 'prompt_set', 'css_versions', 'generation_settings')))
    results = []
    missing = []
    for case in manifest['cases']:
        for framework in manifest['frameworks']:
            path = root / case['id'] / f'{framework}.html'
            if not path.is_file():
                missing.append({'task': case['id'], 'framework': framework})
                continue
            raw = path.read_bytes()
            html = raw.decode('utf-8')
            inspector = Inspector()
            inspector.feed(html)
            inspector.close()
            results.append({
                'task': case['id'], 'framework': framework,
                'sha256': hashlib.sha256(raw).hexdigest(),
                'html_bytes': len(raw),
                'class_tokens': len(inspector.classes),
                'distinct_class_tokens': len(set(inspector.classes)),
                'class_attribute_bytes': inspector.class_bytes,
                'findings': inspect_html(html, case, framework, contract=contract),
            })
    complete = not missing
    return {
        'schema_version': 1,
        'task_count': len(manifest['cases']),
        'expected_outputs': len(manifest['cases']) * len(FRAMEWORKS),
        'completed_outputs': len(results),
        'complete': complete,
        'provenance_supplied': provenance_supplied,
        'comparable': complete and provenance_supplied,
        'missing_outputs': missing,
        'results': results,
        'limitations': [
            'No AI model is called by the evaluator; outputs must be independently supplied.',
            'Static HTML heuristics are not WCAG, screen-reader, browser, or visual-equivalence audits.',
            'Only Syntyr class names are checked against a versioned stylesheet contract; Tailwind and daisyUI class availability requires a compiled CSS/browser check.',
            'HTML bytes are source sizes, not model token usage, billable cost, or productivity.',
            'Comparable means a complete attributed run, not equal visual quality or a winning framework.',
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True,
                        help='Directory containing task-id/framework.html and run.json.')
    parser.add_argument('--tasks', type=Path, default=TASKS)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--strict', action='store_true', help='Fail on missing files or static findings.')
    args = parser.parse_args(argv)
    try:
        report = evaluate(args.inputs, load_manifest(args.tasks))
        payload = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding='utf-8')
            print(f'Report: {args.output}')
        else:
            print(payload)
        if args.strict and (not report['complete'] or any(r['findings'] for r in report['results'])):
            return 1
        return 0
    except (ValueError, OSError, UnicodeError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())
