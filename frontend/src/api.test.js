import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { getDecks } from './api.js';

const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; });

test('reads the backend list contract and sends format and pagination', async () => {
  const data = { items: [{ id: 1, name: 'Mono Red', format: 'Standard', archetype: 'Aggro' }], total: 21, limit: 20, offset: 20 };
  globalThis.fetch = async url => {
    assert.equal(url, '/api/decks?limit=20&offset=20&format=Standard');
    return Response.json(data);
  };
  assert.deepEqual(await getDecks({ format: 'Standard', offset: 20 }), data);
});

test('an empty database stays empty rather than becoming sample data', async () => {
  globalThis.fetch = async () => Response.json({ items: [], total: 0 });
  assert.deepEqual((await getDecks()).items, []);
});

test('reports HTTP failures and invalid responses for the sample fallback', async () => {
  globalThis.fetch = async () => new Response(null, { status: 500 });
  await assert.rejects(getDecks(), /HTTP 500/);
  globalThis.fetch = async () => Response.json({ detail: 'wrong shape' });
  await assert.rejects(getDecks(), /unexpected response/);
});
