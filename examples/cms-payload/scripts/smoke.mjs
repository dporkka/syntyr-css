import assert from 'node:assert/strict';
import { createSyntyrHomepageGlobal, syntyrPageSections } from '../.generated/SyntyrHomepage.js';

assert.throws(() => createSyntyrHomepageGlobal(), /explicit read and update/);
assert.throws(() => createSyntyrHomepageGlobal({ read: () => true }), /explicit read and update/);

const access = {
  read: ({ req }) => Boolean(req.user),
  update: ({ req }) => Boolean(req.user),
};
const config = createSyntyrHomepageGlobal(access);
assert.equal(config.slug, 'syntyrHome');
assert.equal(config.access, access);
assert.deepEqual(syntyrPageSections.blocks.map(block => block.slug),
  ['hero', 'features', 'pricing', 'faq', 'cta']);
assert.ok(config.fields.includes(syntyrPageSections));
console.log('PASS Payload 3.94.1 config defines five blocks and requires explicit access');
