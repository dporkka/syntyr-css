import test from 'node:test';
import assert from 'node:assert/strict';
import { validateAccountName } from '../src/lib/validation.js';

test('trims and accepts a valid account name', () => {
  assert.deepEqual(validateAccountName('  Example Workspace  '),
                   { value: 'Example Workspace', error: null });
});

test('rejects empty and whitespace-only account names', () => {
  assert.equal(validateAccountName('').error, 'Enter an account name.');
  assert.equal(validateAccountName('  ').error, 'Enter an account name.');
});

test('rejects non-text FormData values', () => {
  assert.equal(validateAccountName(null).error, 'Enter an account name.');
  assert.equal(validateAccountName({ name: 'file' }).error, 'Enter an account name.');
});

test('bounds length and echoed values without truncating valid input', () => {
  assert.equal(validateAccountName('X'.repeat(80)).error, null);
  const result = validateAccountName('X'.repeat(500));
  assert.equal(result.error, 'Use 80 characters or fewer.');
  assert.equal(result.value.length, 80);
});

test('rejects one-character values', () => {
  assert.equal(validateAccountName(' x ').error, 'Use at least 2 characters.');
});

test('counts supplementary Unicode code points without splitting a surrogate pair', () => {
  assert.equal(validateAccountName('𠮷').error, 'Use at least 2 characters.');
  assert.equal(validateAccountName('A𠮷').error, null);
  assert.equal(validateAccountName('A'.repeat(79) + '𠮷').error, null);
  const tooLong = validateAccountName('A'.repeat(79) + '𠮷B');
  assert.equal(tooLong.error, 'Use 80 characters or fewer.');
  assert.equal(tooLong.value, 'A'.repeat(79) + '𠮷');
});
