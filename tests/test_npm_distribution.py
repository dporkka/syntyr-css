"""CSS-only npm distribution is optional, complete and release-safe."""
import json
from pathlib import Path
import unittest

from scripts.build import distributions, component_distributions

ROOT = Path(__file__).resolve().parents[1]


class NpmDistributionContract(unittest.TestCase):
    def setUp(self):
        self.package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))

    def test_public_css_only_package_metadata(self):
        self.assertEqual(self.package['name'], '@syntyr/css')
        self.assertEqual(self.package['version'], (ROOT / 'VERSION').read_text().strip())
        self.assertEqual(self.package['license'], 'MIT')
        self.assertFalse(self.package.get('private', False))
        self.assertEqual(self.package['style'], './dist/syntyr.core.css')
        self.assertEqual(self.package['exports']['.'], './dist/syntyr.core.css')
        self.assertEqual(self.package['exports']['./viz.css'], './dist/syntyr.viz.css')
        self.assertIn('**/*.css', self.package['sideEffects'])
        self.assertNotIn('main', self.package)
        for field in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies', 'bin'):
            self.assertNotIn(field, self.package, field)

    def test_every_distribution_is_explicitly_exported(self):
        expected = {
            ('./syntyr.css' if name == 'syntyr.css' else './' + name.removeprefix('syntyr.')): './dist/' + name
            for name in distributions()
        }
        expected.update({'./' + name: './dist/' + name for name in component_distributions()})
        expected['./tailwind.css'] = './integrations/tailwind/syntyr.theme.css'
        expected['./shadcn.css'] = './integrations/shadcn/syntyr.tokens.css'
        expected['./headless.css'] = './integrations/headless/interactions.css'
        expected['./htmx.css'] = './integrations/htmx/syntyr.htmx.css'
        expected['./menu.mjs'] = './integrations/dropdown/menu.mjs'
        expected['./contract.json'] = './metadata/css-contract.v1.json'
        expected['./gallery.json'] = './metadata/component-gallery.v1.json'
        expected['./animate'] = {
            'types': './dist/syntyr.animate.d.mts',
            'default': './dist/syntyr.animate.mjs',
        }
        expected['./copy'] = {
            'types': './dist/syntyr.copy.d.mts',
            'default': './dist/syntyr.copy.mjs',
        }
        self.assertEqual({key: value for key, value in self.package['exports'].items() if key != '.'}, expected)
        for exported in expected.values():
            for relative in exported.values() if isinstance(exported, dict) else (exported,):
                with self.subTest(relative=relative):
                    self.assertTrue((ROOT / relative.removeprefix('./')).is_file())

    def test_allowlisted_release_files_are_css_and_docs_only(self):
        self.assertEqual(set(self.package['files']), {'dist/', 'integrations/tailwind/', 'integrations/shadcn/', 'integrations/headless/', 'integrations/htmx/', 'integrations/dropdown/', 'metadata/css-contract.v1.json', 'metadata/component-gallery.v1.json', 'README.md', 'LICENSE'})
        self.assertIn('publishConfig', self.package)
        self.assertEqual(self.package['publishConfig']['access'], 'public')
        self.assertTrue((ROOT / 'docs/package-managers.md').is_file())


if __name__ == '__main__':
    unittest.main()
