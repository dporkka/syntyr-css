import test from 'node:test';
import assert from 'node:assert/strict';
import { matchCommand } from '../examples/command-launcher.mjs';

test('matches multiple keywords regardless of order or case', () => {
  assert.equal(matchCommand('View account dashboard reports', 'REPORTS ACCOUNT'), true);
  assert.equal(matchCommand('View account dashboard reports', 'reports invoices'), false);
});
test('supports empty queries, whitespace and accented destination names', () => {
  assert.equal(matchCommand('Résumé settings', 'resume'), true);
  assert.equal(matchCommand('Billing', '   '), true);
  assert.equal(matchCommand('Billing', 'billing  '), true);
});
