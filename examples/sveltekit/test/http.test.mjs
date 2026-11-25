import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';

// Vite's port: 0 probes a free port before binding; another process may
// claim it in between. Retry only that race with a fresh test server.
async function startServer(makeServer = createServer) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const server = await makeServer({
      server: { host: '127.0.0.1', port: 0, strictPort: true }
    });
    try {
      await server.listen();
      return server;
    } catch (error) {
      await server.close();
      // Vite's strict-port collision can be a plain Error without .code.
      const collision = error?.code === 'EADDRINUSE' ||
        /^Port \d+ is already in use$/.test(error?.message ?? '');
      if (!collision || attempt === 2) throw error;
    }
  }
  throw new Error('Unexpected retry exhaustion');
}

test('ephemeral test listener retries EADDRINUSE only, closing each failed server', async () => {
  let attempts = 0;
  let closes = 0;
  const server = await startServer(async () => ({
    async listen() {
      attempts++;
      if (attempts === 1) throw new Error('Port 48931 is already in use');
    },
    async close() { closes++; }
  }));
  assert.equal(attempts, 2);
  assert.equal(closes, 1);
  await server.close();

  let fatalAttempts = 0;
  await assert.rejects(
    () => startServer(async () => ({
      async listen() { fatalAttempts++; throw new Error('unrelated failure'); },
      async close() {}
    })),
    /unrelated failure/
  );
  assert.equal(fatalAttempts, 1);
});

test('SvelteKit renders and handles native HTML form POSTs without client scripts', async () => {
  const server = await startServer();
  try {
    const { port } = server.httpServer.address();
    const url = `http://127.0.0.1:${port}/settings`;

    const get = await fetch(url, { headers: { Accept: 'text/html' } });
    const initial = await get.text();
    assert.equal(get.status, 200);
    assert.match(initial, /method="POST"/);
    assert.match(initial, /name="name"/);
    assert.match(initial, /syn-detail-layout/);

    async function post(value) {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Origin: new URL(url).origin,
          Accept: 'text/html',
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({ name: value })
      });
      return { status: response.status, html: await response.text() };
    }

    const invalid = await post('x');
    assert.equal(invalid.status, 400);
    assert.match(invalid.html, /Check the submitted details/);
    assert.match(invalid.html, /Use at least 2 characters/);
    assert.match(invalid.html, /aria-invalid="true"/);
    assert.match(invalid.html, /aria-describedby="workspace-help workspace-error"/);

    const malformed = await fetch(url, {
      method: 'POST',
      headers: {
        Origin: new URL(url).origin,
        Accept: 'text/html',
        'Content-Type': 'multipart/form-data'
      },
      body: 'no-boundary'
    });
    assert.equal(malformed.status, 400);
    assert.match(await malformed.text(), /Malformed form submission/);

    const unicodeShort = await post('𠮷');
    assert.equal(unicodeShort.status, 400);
    assert.match(unicodeShort.html, /Use at least 2 characters/);
    const unicodeLimit = await post('A'.repeat(79) + '𠮷');
    assert.equal(unicodeLimit.status, 200);

    const valid = await post('  Example Workspace  ');
    assert.equal(valid.status, 200);
    assert.match(valid.html, /Example Workspace/);
    assert.match(valid.html, /passed server validation/);

    const escaped = await post('<script>alert(1)</script>');
    assert.equal(escaped.status, 200);
    assert.match(escaped.html, /&lt;script>alert\(1\)&lt;\/script>/);
    assert.doesNotMatch(escaped.html, /<script>alert\(1\)<\/script>/);

    // SvelteKit intentionally enforces its origin-based CSRF check only in
    // production; the development server must not be used to test that gate.
  } finally {
    await server.close();
  }
});
