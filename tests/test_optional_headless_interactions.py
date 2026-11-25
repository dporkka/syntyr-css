"""Optional headless integrations remain separate from the zero-JS Syntyr runtime."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OptionalHeadlessInteractions(unittest.TestCase):
    def test_opt_in_adapter_has_three_distinct_interaction_surfaces(self):
        css = (ROOT / 'integrations/headless/interactions.css').read_text()
        for name in ('syn-menu-surface', 'syn-menu-item',
                     'syn-combobox', 'syn-combobox-popover', 'syn-combobox-option',
                     'syn-toast-region', 'syn-toast'):
            with self.subTest(name=name):
                self.assertIn('.' + name, css)
        for state in ('[data-highlighted]', '[data-focused]', '[data-selected]',
                      '[aria-selected="true"]', '[data-disabled]'):
            self.assertIn(state, css)
        self.assertIn(':where(.syn-root, .syn-root *)', css)
        self.assertIn('@media (forced-colors: active)', css)
        self.assertIn('@media (prefers-reduced-motion: reduce)', css)
        self.assertNotIn('display: none', css)
        self.assertNotIn('outline: none', css)
        self.assertNotIn('pointer-events: none', css)
        self.assertNotIn('@import', css)
        self.assertNotIn('url(', css)

    def test_no_headless_behavior_or_css_is_in_public_core_bundles(self):
        from scripts.build import all_distributions, assemble
        for name, paths in all_distributions().items():
            with self.subTest(name=name):
                self.assertNotIn('integrations/headless/interactions.css', paths)
                self.assertNotIn('.syn-menu-surface', assemble(paths))
        core = (ROOT / 'dist/syntyr.core.css').read_text()
        self.assertNotIn('.syn-toast-region', core)
        self.assertFalse(list((ROOT / 'src').rglob('*.js')))

    def test_optional_example_is_separate_runnable_react_project(self):
        base = ROOT / 'examples/headless-react'
        pkg = json.loads((base / 'package.json').read_text())
        self.assertTrue(pkg['private'])
        for library in ('react', 'react-dom', 'react-aria-components',
                        '@radix-ui/react-dropdown-menu', '@radix-ui/react-toast'):
            self.assertIn(library, pkg['dependencies'])
        self.assertTrue((base / 'package-lock.json').is_file())
        self.assertIn('build', pkg['scripts'])
        self.assertIn('test', pkg['scripts'])
        self.assertIn('@playwright/test', pkg['devDependencies'])
        markup = (base / 'src/App.tsx').read_text()
        for part in ('DropdownMenu.Root', 'DropdownMenu.Trigger', 'DropdownMenu.Item',
                     'ComboBox', 'Input', 'Popover', 'ListBox', 'ListBoxItem',
                     'Toast.Provider', 'Toast.Viewport', 'Toast.Root', 'Toast.Close'):
            self.assertIn(part, markup)
        for attribute in ('syn-menu-surface', 'syn-menu-item',
                          'syn-combobox-popover', 'syn-combobox-option',
                          'syn-toast-region', 'syn-toast'):
            self.assertIn(attribute, markup)
        self.assertIn('aria-label=', markup)
        self.assertIn('onOpenChange=', markup)
        self.assertIn('duration=', markup)
        self.assertIn('type="button"', markup)
        html = (base / 'index.html').read_text()
        self.assertIn('class="syn-root', html)
        self.assertIn('id="root"', html)
        self.assertNotIn('https://', html, 'demo must self-host assets')

    def test_real_sortable_grid_uses_headless_keyboard_behavior_without_core_js(self):
        markup = (ROOT / 'examples/headless-react/src/App.tsx').read_text()
        browser = (ROOT / 'examples/headless-react/tests/interactions.spec.ts').read_text()
        self.assertIn('TableHeader', markup)
        self.assertIn('isRowHeader allowsSorting', markup)
        self.assertIn('onSortChange={setSortDescriptor}', markup)
        self.assertIn('sortDescriptor={sortDescriptor}', markup)
        self.assertIn('aria-label="Campaign inventory"', markup)
        self.assertIn('sortDescriptor.column === "faces"', markup)
        self.assertIn('getByRole("grid", { name: "Campaign inventory" })', browser)
        self.assertIn('toHaveAttribute("aria-sort", "descending")', browser)
        self.assertIn('toContainText("Transit shelter")', browser)
        self.assertIn('sortable data grid works from keyboard', browser)
        self.assertNotIn('react-aria-components', (ROOT / 'package.json').read_text())

    def test_local_enterprise_selection_demo_has_bounded_scope_and_no_core_runtime(self):
        markup = (ROOT / 'examples/headless-react/src/App.tsx').read_text()
        browser = (ROOT / 'examples/headless-react/tests/interactions.spec.ts').read_text()
        example = (ROOT / 'examples/headless-react/src/main.tsx').read_text()
        guide = (ROOT / 'docs/headless-interactions.md').read_text()
        for piece in ('selectionMode="multiple"', 'selectionBehavior="toggle"',
                      'selectedKeys={selectedKeys}', 'onSelectionChange',
                      'setSelectedKeys(new Set())', 'keys === "all"',
                      'setInspectedId', 'role="status"', 'Preview selection'):
            self.assertIn(piece, markup)
        self.assertIn('inventory filtering constrains selection scope', browser)
        self.assertIn('inventory offers a safe preview action', browser)
        self.assertIn('inventory empty filter state', browser)
        self.assertIn('dist/syntyr.recipes.css', example)
        self.assertIn('not every record in a server database', guide)
        self.assertNotIn('react-aria-components', (ROOT / 'package.json').read_text())

    def test_agent_index_discovers_optional_selection_scope_workflow(self):
        index = (ROOT / 'llms.txt').read_text()
        entry = next(
            (line for line in index.splitlines()
             if '[Optional React Aria resource-selection workflow]' in line),
            ''
        )
        self.assertIn('https://syntyr-css.pages.dev/docs/headless-interactions.md', entry)
        self.assertIn('local-only', entry)
        self.assertIn('server-side', entry)
        self.assertIn('opt-in', entry.lower())

    def test_guide_explains_semantics_portals_and_dependencies(self):
        guide = (ROOT / 'docs/headless-interactions.md').read_text()
        for phrase in ('React Aria', 'Radix', 'popover', 'datalist',
                       'aria', 'portal', 'focus', 'toast', 'no runtime',
                       'npm ci', 'npm run build'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), guide.lower())
        self.assertIn('../integrations/headless/interactions.css', guide)
        self.assertIn('React Aria Table', guide)
        self.assertIn('actual sort order', guide)
        self.assertIn('GET links', guide)
        self.assertIn('role="grid"', guide)
        self.assertIn('github.com/dporkka/syntyr-css/tree/main/examples/headless-react', guide)
        self.assertIn('headless-interactions.md', (ROOT / 'README.md').read_text())
        self.assertIn('headless-interactions.md', (ROOT / 'scripts/build_cloudflare_site.py').read_text())

    def test_no_dependency_addition_to_css_package_or_library(self):
        pkg = json.loads((ROOT / 'package.json').read_text())
        self.assertNotIn('react', pkg.get('dependencies', {}))
        self.assertNotIn('@radix-ui/react-dropdown-menu', pkg.get('dependencies', {}))
        self.assertNotIn('react-aria-components', pkg.get('dependencies', {}))
        self.assertFalse((ROOT / 'integrations/headless/package.json').exists())


if __name__ == '__main__':
    unittest.main()
