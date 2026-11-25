/**
 * Narrow reproducible patch for @codemirror/view 6.43.15's rectangleFor
 * >2000-column path. It can generate a range past a short line's end.
 *
 * Apply only to the pinned dev-only docs editor before esbuild bundling.
 * Fail closed if a future CodeMirror version changes this source; remove the
 * patch when upstream ships a verified fix. No runtime dependency is added.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const BEFORE = [
  '            if (line.length <= endOff)',
  '                ranges.push(EditorSelection.range(line.from + startOff, line.to + endOff));'
].join('\n');
const AFTER = [
  '            if (line.length < startOff)',
  '                ranges.push(EditorSelection.cursor(line.to));',
  '            else',
  '                ranges.push(EditorSelection.range(line.from + startOff, line.from + Math.min(endOff, line.length)));'
].join('\n');

export function patchRectangularSelection(source) {
  if (source.includes(AFTER) && !source.includes(BEFORE)) return source;
  if (source.split(BEFORE).length !== 2) {
    throw new Error('Unsupported CodeMirror rectangular-selection source. Inspect pinned dependency before rebuilding.');
  }
  return source.replace(BEFORE, AFTER);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const view = new URL('./node_modules/@codemirror/view/dist/index.js', import.meta.url);
  const source = readFileSync(view, 'utf8');
  const patched = patchRectangularSelection(source);
  if (source !== patched) writeFileSync(view, patched);
  console.log('Verified and patched CodeMirror >2000-column rectangular-selection range.');
}
