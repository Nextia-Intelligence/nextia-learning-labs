// Checks of the secret check. Run: node --test "scripts/*.test.mjs"
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { findSecrets, readEnv } from './check-bundle.mjs';

test('reads a .env file and skips comments', () => {
  assert.deepEqual(readEnv('# a comment\nVITE_API_URL=http://127.0.0.1:8100\nPROVIDER_API_KEY="abc"\n'), {
    VITE_API_URL: 'http://127.0.0.1:8100',
    PROVIDER_API_KEY: 'abc',
  });
});

test('finds the value of a server secret in the bundle', () => {
  const env = { PROVIDER_API_KEY: 'demo-not-a-real-key-123' };
  const problems = findSecrets([['dist/assets/index.js', 'const k="demo-not-a-real-key-123";']], env);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /PROVIDER_API_KEY/);
});

test('a VITE_ variable with KEY in its name is a mistake, even if it is not used', () => {
  const problems = findSecrets([], { VITE_PROVIDER_API_KEY: 'demo-not-a-real-key-123' });
  assert.match(problems[0], /VITE_ variable is public/);
});

test('finds text that looks like a key', () => {
  const problems = findSecrets([['a.js', 'fetch(u,{headers:{"api-key":"x"}});const apiKey = "0123456789abcdef";']], {});
  assert.equal(problems.length, 1);
});

test('clean files give no problem', () => {
  assert.deepEqual(findSecrets([['a.js', 'const url="http://127.0.0.1:8100";']], { VITE_API_URL: 'http://127.0.0.1:8100' }), []);
});

test('says in which file the value of a VITE_ secret is, when the code reads it', () => {
  const env = { VITE_PROVIDER_API_KEY: 'demo-not-a-real-key-123' };
  const problems = findSecrets([['dist/assets/index.js', 'const k="demo-not-a-real-key-123";']], env);
  assert.equal(problems.length, 2);
  assert.match(problems[1], /^dist\/assets\/index\.js: contains the value of VITE_PROVIDER_API_KEY/);
});
