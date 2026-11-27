import json
import unittest

from integrations.genui import GenUIError
from integrations.genui.a2ui import BASIC_CATALOG_ID, render_a2ui


def message(components, **extra):
    return json.dumps({'version': '1.0', 'createSurface': {
        'surfaceId': 'demo', 'catalogId': BASIC_CATALOG_ID,
        'components': components, **extra}})


def component(id, kind, **props):
    return {'id': id, 'component': kind, **props}


class A2UITests(unittest.TestCase):
    def test_single_message_renders_fixed_tree_in_child_order(self):
        doc = message([component('second', 'Text', text='<script>'),
                       component('root', 'Card', child='column'),
                       component('column', 'Column', children=['first', 'second', 'line']),
                       component('first', 'Text', text='First'),
                       component('line', 'Divider', axis='horizontal')])
        html = render_a2ui(doc)
        self.assertIn('class="syn-panel"', html)
        self.assertIn('class="syn-stack"', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)
        self.assertLess(html.index('First'), html.index('&lt;script'))
        self.assertIn('<hr>', html)

    def test_rejects_untrusted_graphs(self):
        for components in [
            [component('root', 'Column', children=['root'])],
            [component('root', 'Column', children=['missing'])],
            [component('root', 'Text', text='A'), component('root', 'Text', text='B')],
            [component('root', 'Text', text='A'), component('orphan', 'Text', text='B')],
            [component('root', 'Column', children=['x', 'x']), component('x', 'Text', text='A')],
            [component('x', 'Text', text='A')],
        ]:
            with self.subTest(components=components), self.assertRaises(GenUIError):
                render_a2ui(message(components))

    def test_rejects_unsupported_semantics_not_silently_downgraded(self):
        for root in [component('root', 'Button', action={'event': {'name': 'pay'}}),
                     component('root', 'Text', text={'@path': '/secret'}),
                     component('root', 'Text', text={'@call': 'read'}),
                     component('root', 'Text', text='A', variant='caption'),
                     component('root', 'Divider', axis='vertical'),
                     component('root', 'Column', children={'componentId': 'x', 'path': '/items'}),
                     component('root', 'Text', text='A', **{'@catalogId': 'other'})]:
            with self.subTest(root=root), self.assertRaises(GenUIError):
                render_a2ui(message([root]))
        for extra in [{'catalogId': 'https://evil.invalid'}, {'dataModel': {'secret': 'x'}}, {'sendDataModel': True}]:
            with self.assertRaises(GenUIError):
                render_a2ui(message([component('root', 'Text', text='A')], **extra))

    def test_rejects_duplicate_envelope_keys_and_bounded_depth(self):
        with self.assertRaises(GenUIError):
            render_a2ui('{"version":"1.0","version":"1.0","createSurface":{}}')
        chain = [component('root', 'Column', children=['0'])]
        chain += [component(str(i), 'Column', children=[str(i+1)]) for i in range(15)]
        chain += [component('15', 'Text', text='A')]
        with self.assertRaises(GenUIError):
            render_a2ui(message(chain))
        with self.assertRaises(GenUIError):
            render_a2ui(' ' * 262145)

    def test_rejects_wrong_version_and_message_type(self):
        for doc in ['{"version":"0.9","createSurface":{}}', '{"version":"1.0","updateComponents":{}}']:
            with self.assertRaises(GenUIError):
                render_a2ui(doc)
