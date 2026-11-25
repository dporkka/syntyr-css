"""Pinned, zero-runtime CSS preset contract; no optional browser dependencies."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.build import COMPONENTS, preset_distributions

ROOT = Path(__file__).resolve().parents[1]


class PresetContractTests(unittest.TestCase):
    def test_named_presets_contain_one_self_sufficient_stylesheet(self):
        presets = preset_distributions()
        self.assertEqual(set(presets), {
            'presets/minimal.css', 'presets/saas.css', 'presets/cinematic.css'
        })
        core = ('tokens.css', 'base.css') + COMPONENTS
        for name, sources in presets.items():
            with self.subTest(name=name):
                self.assertEqual(sources[:len(core)], core)
                self.assertIn('semantic.css', sources)
                self.assertEqual(len(sources), len(set(sources)))
                rendered = (ROOT / 'dist' / name).read_text(encoding='utf-8')
                self.assertIn('@layer syn.tokens', rendered)
                self.assertIn('@layer syn.semantic', rendered)
                self.assertNotIn('@import', rendered)
                self.assertNotIn('url(https://', rendered)
                self.assertNotIn('url(http://', rendered)
        self.assertNotIn('effects.css', presets['presets/minimal.css'])
        self.assertIn('recipes.css', presets['presets/saas.css'])
        self.assertIn('utilities.css', presets['presets/saas.css'])
        self.assertIn('effects.css', presets['presets/cinematic.css'])
        self.assertIn('geometry.css', presets['presets/cinematic.css'])
        self.assertNotIn('effects.css', presets['presets/saas.css'])

    def test_optional_semantic_native_overlays_and_progress(self):
        semantic = (ROOT / 'src' / 'semantic.css').read_text(encoding='utf-8')
        for tag in ('dialog', 'progress'):
            with self.subTest(tag=tag):
                self.assertIn(f'{tag}:not([class])', semantic)
                self.assertIn(f'{tag}[data-syn-semantic]', semantic)
        self.assertIn('[popover]:not([class])', semantic)
        self.assertIn('[popover][data-syn-semantic]', semantic)
        self.assertNotIn('dialog { display: block', semantic)

    def test_versioned_preset_manifest_matches_actual_dist_bytes(self):
        manifest = json.loads((ROOT / 'metadata' / 'css-contract.v1.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['schema_version'], 1)
        self.assertEqual(manifest['library_version'], (ROOT / 'VERSION').read_text().strip())
        self.assertEqual(set(manifest['presets']), {'minimal', 'saas', 'cinematic'})
        for name, sources in preset_distributions().items():
            preset = name.split('/')[1].removesuffix('.css')
            contract = manifest['presets'][preset]
            self.assertEqual(contract['file'], 'dist/' + name)
            self.assertEqual(contract['sources'], list(sources))
            contents = (ROOT / contract['file']).read_bytes()
            self.assertEqual(contract['sha256'], hashlib.sha256(contents).hexdigest())
            self.assertEqual(contract['raw_bytes'], len(contents))

    def test_maintainer_only_build_check_rejects_stale_contract(self):
        completed = subprocess.run([sys.executable, 'scripts/build.py', '--check'],
                                   cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn('css-contract.v1.json', completed.stdout)


if __name__ == '__main__':
    unittest.main()
