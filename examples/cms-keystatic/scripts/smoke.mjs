import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createReader } from '@keystatic/core/reader';
import config from '../.generated/keystatic.config.js';

const reader = createReader(process.cwd(), config);
const actual = await reader.singletons.homepage.read();
const fixture = JSON.parse(await readFile('content/pages/home.json', 'utf8'));

assert.deepEqual(actual, fixture);
assert.deepEqual(actual.sections.map(block => block.discriminant),
  ['hero', 'features', 'pricing', 'faq', 'cta']);
console.log('PASS Keystatic 0.6.10 reader returns the expected five typed sections');
