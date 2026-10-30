import test from 'node:test';
import assert from 'node:assert/strict';
import { loadPackage, readAttachment, suggestAssignments, validateDraft } from '../src/package.ts';

const payload = () => new File(['synthetic'], 'result.txt');
const manifest = (name = 'manifest.json') => new File(['{"synthetic":true}\r\n'], name);
const signature = (name = 'signature.txt') => new File(['a'.repeat(88)], name);
test('unordered standard package is assigned without reading untrusted metadata', async () => {
  const files = [signature(), payload(), manifest()];
  const assigned = suggestAssignments(files);
  assert.deepEqual(assigned, { payload: '1', manifest: '2', signature: '0' });
  const draft = await loadPackage(files, assigned);
  assert.equal(draft.payload, files[1]);
  assert.equal(draft.manifest, '{"synthetic":true}\r\n');
  assert.deepEqual(validateDraft(draft.payload, draft.manifest, draft.signature), {});
});
test('ambiguous filenames require explicit assignments, including duplicate basenames', async () => {
  const files = [payload(), manifest('part.txt'), signature('part.txt')];
  assert.deepEqual(suggestAssignments(files), { payload: '', manifest: '', signature: '' });
  const draft = await loadPackage(files, { payload: '0', manifest: '1', signature: '2' });
  assert.equal(draft.signature, 'a'.repeat(88));
});
test('incomplete, repeated, invalid indices and non-three-file selections are rejected', async () => {
  const files = [payload(), manifest(), signature()];
  for (const assignment of [{payload:'0',manifest:'',signature:'2'}, {payload:'0',manifest:'0',signature:'2'}, {payload:'0',manifest:'1',signature:'3'}]) {
    await assert.rejects(loadPackage(files, assignment), /different selected file/);
  }
  await assert.rejects(loadPackage(files.slice(1), {payload:'0',manifest:'1',signature:'2'}), /exactly three/);
});
test('invalid UTF-8, empty and oversized attachments fail rather than replacing text', async () => {
  await assert.rejects(readAttachment(new File([new Uint8Array([0xff])], 'manifest.json'), 'manifest'), /not valid UTF-8/);
  await assert.rejects(readAttachment(new File([''], 'signature.txt'), 'signature'), /empty/);
  await assert.rejects(readAttachment(new File(['x'.repeat(8193)], 'manifest.json'), 'manifest'), /8 KiB/);
  await assert.rejects(readAttachment(new File(['x'.repeat(89)], 'signature.txt'), 'signature'), /88 bytes/);
  await assert.rejects(loadPackage([new File([new Uint8Array(2097153)],'large.txt'),manifest(),signature()], {payload:'0',manifest:'1',signature:'2'}), /2 MiB/);
});
test('UTF-8 BOM, whitespace and newlines round-trip without normalization', async () => {
  const bytes = new Uint8Array([0xef,0xbb,0xbf,...new TextEncoder().encode(' {"a":1}\r\n')]);
  const text = await readAttachment(new File([bytes], 'manifest.json'), 'manifest');
  assert.equal(text.charCodeAt(0), 0xfeff);
  assert.deepEqual(new TextEncoder().encode(text), bytes);
});
test('readiness validates presence and byte lengths without certifying package validity', () => {
  assert.equal(Object.keys(validateDraft(null, '', '')).length, 3);
  assert.ok(validateDraft(new File([''], 'empty.txt'), '{}', 'a').payload);
  assert.ok(validateDraft(payload(), 'é'.repeat(4097), 'a').manifest);
  assert.deepEqual(validateDraft(payload(), 'not canonical JSON', 'not a valid signature'), {});
});
