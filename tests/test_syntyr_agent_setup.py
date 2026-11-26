"""Offline, release-pinned Syntyr consumer agent onboarding."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/syntyr_agent.py'


class AgentSetupTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              cwd=ROOT, capture_output=True, text=True)

    def test_skill_name_matches_folder_and_is_portable(self):
        skill = (ROOT / 'agents/syntyr/SKILL.md').read_text()
        self.assertIn('name: syntyr\n', skill)
        self.assertNotIn('../../', skill)

    def test_init_copies_exact_published_assets_and_versioned_reference(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            result = self.run_cli('init', '--project', project, '--json')
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload['release'], '0.3.0-alpha.4')
            config = json.loads((project / 'syntyr.agent.json').read_text())
            self.assertEqual(config['release'], '0.3.0-alpha.4')
            css = project / config['assets_dir'] / 'syntyr.core.css'
            self.assertEqual(css.read_bytes(), (ROOT / 'site-releases/0.3.0-alpha.4/syntyr.core.css').read_bytes())
            skill = project / '.agents/skills/syntyr/SKILL.md'
            self.assertTrue(skill.exists())
            catalog = json.loads((skill.parent / 'references/api.json').read_text())
            self.assertEqual(catalog['release'], '0.3.0-alpha.4')
            self.assertEqual(catalog['themes'], ['grid', 'noir', 'studio'])
            self.assertIn('syn-button', catalog['classes'])
            self.assertNotIn('syn-field-row', catalog['classes'])
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)

    def test_init_rejects_conflicts_without_overwriting(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            (project / 'syntyr.agent.json').write_text('custom')
            result = self.run_cli('init', '--project', project, '--json')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((project / 'syntyr.agent.json').read_text(), 'custom')
            self.assertFalse((project / '.agents').exists())

    def test_check_is_release_aware_and_has_actionable_diagnostics(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)
            page = project / 'page.html'
            page.write_text('<main class="syn-root syn-field-row syn-buttn"></main>')
            result = self.run_cli('check', '--project', project, '--json', page)
            self.assertEqual(result.returncode, 1, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload['release'], '0.3.0-alpha.4')
            self.assertIn('unknown-class', [x['code'] for x in payload['diagnostics']])
            self.assertTrue(all(x.get('file') for x in payload['diagnostics']))
            page.write_text('<main class="syn-root syn-panel"><button class="syn-button">OK</button></main>')
            result = self.run_cli('check', '--project', project, '--json', page)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)['diagnostics'], [])

    def test_check_fails_if_installed_asset_changed_or_missing(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)
            cfg = json.loads((project / 'syntyr.agent.json').read_text())
            (project / cfg['assets_dir'] / 'syntyr.core.css').unlink()
            result = self.run_cli('check', '--project', project, '--json')
            self.assertEqual(result.returncode, 1)
            self.assertIn('missing-asset', [d['code'] for d in json.loads(result.stdout)['diagnostics']])

    def test_explicit_candidate_is_not_mistaken_for_published(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            result = self.run_cli('init', '--project', project, '--release', '0.3.0-alpha.5', '--json')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'unreleased_candidate')
            catalog = json.loads((project / '.agents/skills/syntyr/references/api.json').read_text())
            self.assertIn('syn-field-row', catalog['classes'])

    def test_large_valid_html_is_not_limited_by_mcp_payload_cap(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)
            page = project / 'long.html'
            page.write_text('<main class="syn-root syn-panel">' + '<p>Long content.</p>' * 1600 + '</main>')
            result = self.run_cli('check', '--project', project, '--json', page)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout[:600])

    def test_init_rejects_symlinked_target_without_writing_other_files(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            external = project / 'outside'
            external.mkdir()
            (project / 'vendor').symlink_to(external, target_is_directory=True)
            result = self.run_cli('init', '--project', project, '--json')
            self.assertEqual(result.returncode, 1)
            self.assertFalse((project / 'syntyr.agent.json').exists())
            self.assertFalse((project / '.agents').exists())

    def test_init_preflights_nondirectory_ancestors_before_any_asset_write(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            (project / '.agents').write_text('consumer-owned file')
            result = self.run_cli('init', '--project', project)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((project / 'vendor').exists())
            self.assertFalse((project / 'syntyr.agent.json').exists())
            self.assertEqual((project / '.agents').read_text(), 'consumer-owned file')

    def test_check_does_not_silently_validate_jsx(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)
            page = project / 'page.tsx'
            page.write_text('<main className="syn-root syn-no-such-class"></main>')
            result = self.run_cli('check', '--project', project, '--json', page)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)['unchecked_files'], [str(page)])

    def test_info_unconfigured_project_is_read_only_and_explicit(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            result = self.run_cli('info', '--project', project, '--json')
            self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertEqual(data['status'], 'unconfigured')
            self.assertFalse(data['css_usage_verified'])
            self.assertEqual(list(project.iterdir()), [])

    def test_info_reports_exact_pinned_assets_and_release_aware_themes(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)
            result = self.run_cli('info', '--project', project, '--json')
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertEqual(data['status'], 'healthy')
            self.assertEqual(data['release'], '0.3.0-alpha.4')
            self.assertEqual(data['release_status'], 'published')
            self.assertEqual(data['themes'], ['grid', 'noir', 'studio'])
            self.assertFalse(data['css_usage_verified'])
            self.assertEqual({item['name'] for item in data['assets']}, {
                'syntyr.core.css', 'syntyr.recipes.css'})
            self.assertTrue(all(item['integrity'] == 'verified' for item in data['assets']))
            self.assertEqual(data['agent_skill'], '.agents/skills/syntyr/SKILL.md')
            self.assertEqual(data['diagnostics'], [])

    def test_info_detects_missing_and_modified_assets_without_writes(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)
            cfg = json.loads((project / 'syntyr.agent.json').read_text())
            core = project / cfg['assets_dir'] / 'syntyr.core.css'
            recipes = project / cfg['assets_dir'] / 'syntyr.recipes.css'
            core.unlink()
            recipes.write_text('changed')
            result = self.run_cli('info', '--project', project, '--json')
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertEqual(data['status'], 'degraded')
            self.assertEqual({item['integrity'] for item in data['assets']}, {'missing', 'modified'})
            self.assertEqual({d['code'] for d in data['diagnostics']}, {'missing-asset', 'modified-asset'})
            self.assertEqual(recipes.read_text(), 'changed')
            self.assertFalse(core.exists())

    def test_info_and_check_reject_modified_skill_and_reference(self):
        for agent, directory in (('codex', '.agents'), ('claude', '.claude'), ('cursor', '.cursor')):
            with self.subTest(agent=agent), TemporaryDirectory() as path:
                project = Path(path)
                self.assertEqual(self.run_cli('init', '--project', project, '--agent', agent).returncode, 0)
                page = project / 'page.html'
                page.write_text('<main class="syn-root"></main>')
                original = project / directory / 'skills/syntyr'
                pristine = self.run_cli('info', '--project', project)
                self.assertEqual(pristine.returncode, 0)
                self.assertTrue(all(a['integrity'] == 'verified' for a in
                                    json.loads(pristine.stdout)['agent_artifacts']))
                (original / 'SKILL.md').write_text('unexpected modification')
                (original / 'references/api.json').write_text('{}')
                for command in ('info', 'check'):
                    result = self.run_cli(command, '--project', project)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual({d['code'] for d in json.loads(result.stdout)['diagnostics']},
                                     {'modified-agent-skill', 'modified-api-reference'})
                self.assertEqual((original / 'SKILL.md').read_text(), 'unexpected modification')

    def test_check_matches_info_symlink_and_config_validation(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)
            cfg = project / 'syntyr.agent.json'
            config = json.loads(cfg.read_text())
            target = project / config['agent_skill']
            outside = project / 'outside.md'
            outside.write_bytes(target.read_bytes())
            target.unlink()
            target.symlink_to(outside)
            result = self.run_cli('check', '--project', project)
            self.assertEqual(result.returncode, 1)
            self.assertIn('symlink-agent-skill', [d['code'] for d in json.loads(result.stdout)['diagnostics']])
            other = project / 'outside.json'
            cfg.rename(other)
            cfg.symlink_to(other)
            for command in ('info', 'check'):
                result = self.run_cli(command, '--project', project)
                self.assertEqual(result.returncode, 1)
                self.assertIn('symlinked Syntyr configuration', result.stdout)

    def test_info_agent_paths_are_valid_on_posix_and_windows(self):
        from pathlib import PurePosixPath, PureWindowsPath
        from scripts.syntyr_agent import _valid_agent_paths

        skill = '.agents/skills/syntyr/SKILL.md'
        reference = '.agents/skills/syntyr/references/api.json'
        self.assertTrue(_valid_agent_paths(skill, reference, path_cls=PurePosixPath))
        self.assertTrue(_valid_agent_paths(skill, reference, path_cls=PureWindowsPath))
        self.assertFalse(_valid_agent_paths(skill, 'unexpected/api.json', path_cls=PureWindowsPath))

    def test_info_rejects_symlinked_assets(self):
        with TemporaryDirectory() as path:
            project = Path(path)
            self.assertEqual(self.run_cli('init', '--project', project).returncode, 0)
            cfg = json.loads((project / 'syntyr.agent.json').read_text())
            core = project / cfg['assets_dir'] / 'syntyr.core.css'
            core.unlink()
            outside = project / 'outside.css'
            outside.write_text('do not read')
            core.symlink_to(outside)
            result = self.run_cli('info', '--project', project, '--json')
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            data = json.loads(result.stdout)
            self.assertIn('symlink-asset', [d['code'] for d in data['diagnostics']])
            self.assertEqual(outside.read_text(), 'do not read')


if __name__ == '__main__':
    unittest.main()
