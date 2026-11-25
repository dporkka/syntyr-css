import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { patchRectangularSelection } from '../tools/playground-editor/patch-rectangular-selection.mjs';

const source = readFileSync(new URL('../tools/playground-editor/node_modules/@codemirror/view/dist/index.js', import.meta.url), 'utf8');

function rectangle(sourceText) {
  const begin = sourceText.indexOf('function rectangleFor(state, a, b)');
  const end = sourceText.indexOf('function absoluteColumn(', begin);
  assert.ok(begin >= 0 && end > begin, 'pinned dependency must contain rectangleFor');
  const body = sourceText.slice(begin, end);
  const selection = {
    range(from, to) {
      if (from < 0 || to < from || to > 2104) throw new RangeError('Selection out of bounds');
      return { from, to };
    },
    cursor(pos) {
      if (pos < 0 || pos > 2104) throw new RangeError('Cursor out of bounds');
      return { from: pos, to: pos };
    }
  };
  return new Function('EditorSelection', 'MaxOff', 'findColumn', body + '\nreturn rectangleFor;')(selection, 2000, () => 0);
}

test('unpatched CodeMirror reproduces the long-line rectangular range failure, patched build does not', () => {
  const a = { line: 1, off: 2101, col: -1 };
  const b = { line: 2, off: 1, col: -1 };
  const doc = {
    line(n) {
      return n === 1
        ? { from: 0, to: 2102, length: 2102, text: 'x'.repeat(2102) }
        : { from: 2103, to: 2104, length: 1, text: 'x' };
    }
  };
  const patched = patchRectangularSelection(source);
  // npm ci installs the vulnerable upstream source; npm run build patches it.
  // Reconstruct the upstream branch to prove the regression regardless of
  // whether this test runs before or after the bundle-generation step.
  const unsafe = [
    '            if (line.length <= endOff)',
    '                ranges.push(EditorSelection.range(line.from + startOff, line.to + endOff));'
  ].join('\n');
  const safe = [
    '            if (line.length < startOff)',
    '                ranges.push(EditorSelection.cursor(line.to));',
    '            else',
    '                ranges.push(EditorSelection.range(line.from + startOff, line.from + Math.min(endOff, line.length)));'
  ].join('\n');
  assert.ok(patched.includes(safe), 'the pinned source is patched precisely once');
  const original = patched.replace(safe, unsafe);
  assert.throws(() => rectangle(original)({ doc }, a, b), RangeError);
  const ranges = rectangle(patched)({ doc }, a, b);
  assert.deepEqual(ranges, [{from: 1, to: 2101}, {from: 2104, to: 2104}]);
  assert.equal(patchRectangularSelection(patched), patched, 'patch remains idempotent');
});
