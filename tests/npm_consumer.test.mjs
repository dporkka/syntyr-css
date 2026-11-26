/** Install the packed candidate outside the repository, without registry access. */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { lstatSync, mkdtempSync, mkdirSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));

test('actual npm tarball installs offline in an independent consumer and resolves every public export', () => {
  const scratch = mkdtempSync(join(tmpdir(), 'syntyr-consumer-'));
  try {
    const consumer = join(scratch, 'consumer');
    const cache = join(scratch, 'cache');
    mkdirSync(consumer);
    const npm = (args, cwd) => execFileSync('npm', [
      ...args, '--offline', '--ignore-scripts', '--cache', cache,
      '--no-audit', '--no-fund',
    ], { cwd, encoding: 'utf8', timeout: 120_000 });
    const packed = JSON.parse(npm(['pack', '--json', '--pack-destination', scratch], root));
    assert.equal(packed.length, 1);
    // npm chooses the archive name; derive it independently from known metadata.
    const filename = 'syntyr-css-' + source.version + '.tgz';
    assert.equal(packed[0].filename, filename);
    const archive = join(scratch, filename);
    writeFileSync(join(consumer, 'package.json'), JSON.stringify({
      name: 'syntyr-clean-consumer', version: '1.0.0', private: true,
    }));
    npm(['install', archive], consumer);

    const installed = join(consumer, 'node_modules', '@syntyr', 'css');
    assert.equal(lstatSync(installed).isSymbolicLink(), false);
    const manifest = JSON.parse(readFileSync(join(installed, 'package.json'), 'utf8'));
    assert.equal(manifest.name, source.name);
    assert.equal(manifest.version, source.version);
    assert.deepEqual(manifest.exports, source.exports);
    for (const field of ['dependencies', 'optionalDependencies', 'peerDependencies', 'scripts']) {
      assert.equal(manifest[field], undefined, field);
    }
    const lock = JSON.parse(readFileSync(join(consumer, 'package-lock.json'), 'utf8'));
    assert.deepEqual(Object.keys(lock.packages).sort(), ['', 'node_modules/@syntyr/css']);
    assert.match(lock.packages['node_modules/@syntyr/css'].integrity, /^sha512-/);
    const require = createRequire(join(consumer, 'package.json'));
    for (const [subpath, entry] of Object.entries(source.exports)) {
      const target = typeof entry === 'string' ? entry : entry.default;
      assert.equal(typeof target, 'string', subpath);
      const specifier = subpath === '.' ? source.name : source.name + subpath.slice(1);
      const actual = require.resolve(specifier);
      assert.equal(realpathSync(actual), realpathSync(join(installed, target)), specifier);
      assert.deepEqual(readFileSync(actual), readFileSync(join(root, target)), specifier);
      if (typeof entry === 'object' && entry.types) {
        assert.deepEqual(readFileSync(join(installed, entry.types)),
          readFileSync(join(root, entry.types)), specifier + ' types');
      }
    }
    assert.equal(require.resolve(source.name), require.resolve(source.name + '/core.css'));
    assert.throws(() => require.resolve(source.name + '/dist/syntyr.core.css'),
      { code: 'ERR_PACKAGE_PATH_NOT_EXPORTED' });
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
});
