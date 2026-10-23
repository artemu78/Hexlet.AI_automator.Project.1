import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeContact, sendContact } from './contact-api.js';

test('trim, required fields and Unicode length boundaries', () => {
  assert.deepEqual(normalizeContact(' hello ', ' @test '), { message: 'hello', contacts: '@test' });
  for (const [message, contacts] of [['', 'a'], ['a', ' '], ['a'.repeat(1001), 'a'], ['a', 'a'.repeat(101)]]) {
    assert.throws(() => normalizeContact(message, contacts));
  }
  assert.equal(normalizeContact('😀'.repeat(1000), '😀'.repeat(100)).message.length, 2000);
});
const payload = { id: 'id', message: 'hello', contacts: '@test' };
test('success requires saved status and matching ID', async () => {
  for (const body of [{}, { status: 'saved', id: 'other' }]) {
    await assert.rejects(sendContact('https://api', payload, async () => Response.json(body)));
  }
  await sendContact('https://api', payload, async () => Response.json({ status: 'saved', id: 'id' }));
});
test('network, server, rate limit and timeout fail without mutating payload', async () => {
  for (const status of [400, 409, 429, 503]) {
    await assert.rejects(sendContact('https://api', payload, async () => new Response('', { status })));
  }
  await assert.rejects(sendContact('', payload));
  await assert.rejects(sendContact('https://api', payload, async () => { throw new TypeError('network'); }));
  await assert.rejects(sendContact('https://api', payload, (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('timeout', 'AbortError')));
  }), 5));
  assert.equal(payload.message, 'hello');
});
