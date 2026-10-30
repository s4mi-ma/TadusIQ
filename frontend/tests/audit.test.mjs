import test from 'node:test';
import assert from 'node:assert/strict';
import { audit } from '../src/api.ts';
import { suggestedNextStep } from '../src/guidance.ts';
const event = (id, record) => ({event_id:id, verification_id:record, created_at:'2026-10-30T12:00:00Z', event_type:'check_metadata', details:'PASS'});
test('overview URL is unchanged, selected record is encoded and requests 200 events', async () => {
  const original = globalThis.fetch;
  const calls = [];
  const controller = new AbortController();
  globalThis.fetch = async (url, init) => { calls.push({url, signal:init.signal}); return Response.json([event(2, 'old / record'),event(1,'old / record')]); };
  try {
    await audit();
    const rows = await audit(controller.signal, 'old / record');
    assert.equal(calls[0].url, '/api/audit');
    assert.equal(calls[1].url, '/api/audit?verification_id=old%20%2F%20record&limit=200');
    assert.equal(calls[1].signal, controller.signal);
    assert.deepEqual(rows.map(row => row.event_id), [2,1]);
  } finally { globalThis.fetch = original; }
});
test('scoped audit rejects foreign/null record events and malformed responses', async () => {
  const original = globalThis.fetch;
  try {
    for (const body of [[event(1,'other')], [event(1,null)], {}, [{...event(1,'selected'),event_id:'invalid'}]]) {
      globalThis.fetch = async () => Response.json(body);
      await assert.rejects(audit(undefined,'selected'));
    }
    globalThis.fetch = async () => Response.json([]);
    assert.deepEqual(await audit(undefined,'selected'), []);
  } finally { globalThis.fetch = original; }
});
test('scoped audit passes cancellation through and never invents events', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (_url, init) => { init.signal.throwIfAborted(); return Response.json([]); };
  try {
    const controller = new AbortController(); controller.abort();
    await assert.rejects(audit(controller.signal,'selected'), {name:'AbortError'});
  } finally { globalThis.fetch = original; }
});
test('every supported decision has actionable, non-mutating guidance', () => {
  const result = {status:'QUARANTINED', checks:[]};
  for (const reason_code of ['HASH_MISMATCH','SIZE_MISMATCH','INVALID_SIGNATURE','INVALID_METADATA','UNKNOWN_OR_REVOKED_KEY','SENDER_KEY_MISMATCH','FUTURE_REASON']) {
    assert.ok(suggestedNextStep({...result, reason_code}).length > 30);
  }
  assert.match(suggestedNextStep({...result, reason_code:'INVALID_METADATA',checks:[{name:'file_name',status:'FAIL'}]}), /filename/);
  assert.match(suggestedNextStep({...result,status:'ACCEPTED',reason_code:'VALID'}), /audit events/);
});
