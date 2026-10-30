export type Result = {
  verification_id: string; status: 'ACCEPTED' | 'QUARANTINED'; reason_code: string;
  details: string; received_at: string; file_name: string | null; file_size_bytes: number;
  computed_sha256: string; metadata_authenticated: boolean;
  claimed_laboratory_id: string | null; verified_laboratory_id: string | null;
  checks: { name: string; status: 'PASS' | 'FAIL' | 'SKIPPED' }[];
};
export type Audit = { event_id: number; created_at: string; event_type: string; details: string; verification_id: string | null };
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid server response.');
  return value as Record<string, unknown>;
}
function string(value: unknown): string {
  if (typeof value !== 'string') throw new Error('Invalid server response.');
  return value;
}
function nullable(value: unknown): string | null { return value === null ? null : string(value); }
export function result(value: unknown): Result {
  const r = object(value);
  if (r.status !== 'ACCEPTED' && r.status !== 'QUARANTINED') throw new Error('Invalid decision.');
  if (typeof r.metadata_authenticated !== 'boolean' || typeof r.file_size_bytes !== 'number' || !Array.isArray(r.checks)) throw new Error('Invalid decision fields.');
  const checks: Result['checks'] = r.checks.map(value => {
    const c = object(value);
    if (c.status !== 'PASS' && c.status !== 'FAIL' && c.status !== 'SKIPPED') throw new Error('Invalid check.');
    return { name: string(c.name), status: c.status };
  });
  if (checks.map(c => c.name).join(',') !== 'metadata,trusted_key,sender,signature,file_name,size,sha256') throw new Error('Incomplete checks.');
  if (r.status === 'ACCEPTED' && (r.reason_code !== 'VALID' || !r.metadata_authenticated || checks.some(c => c.status !== 'PASS'))) throw new Error('Inconsistent acceptance response.');
  return { verification_id: string(r.verification_id), status: r.status, reason_code: string(r.reason_code), details: string(r.details), received_at: string(r.received_at), file_name: nullable(r.file_name), file_size_bytes: r.file_size_bytes, computed_sha256: string(r.computed_sha256), metadata_authenticated: r.metadata_authenticated, claimed_laboratory_id: nullable(r.claimed_laboratory_id), verified_laboratory_id: nullable(r.verified_laboratory_id), checks };
}
export async function request(url: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(url, init);
  let data: unknown;
  try { data = await response.json(); }
  catch (error) {
    if (error instanceof SyntaxError || error instanceof TypeError) {
      throw new Error('The receiver returned an unreadable response. Check its connection and refresh records.');
    }
    throw error;
  }
  if (!response.ok) {
    const body = object(data);
    throw new Error(body.error ? string(object(body.error).message) : 'Backend is not ready. Prepare the synthetic packages first.');
  }
  return data;
}
export async function history(signal?: AbortSignal): Promise<Result[]> {
  const data = await request('/api/verifications', { signal });
  if (!Array.isArray(data)) throw new Error('Invalid history response.');
  return data.map(result);
}
export async function audit(signal?: AbortSignal, verificationId?: string): Promise<Audit[]> {
  const url = verificationId === undefined ? '/api/audit' : `/api/audit?verification_id=${encodeURIComponent(verificationId)}&limit=200`;
  const data = await request(url, { signal });
  if (!Array.isArray(data)) throw new Error('Invalid audit response.');
  const events = data.map(value => { const a = object(value); if (typeof a.event_id !== 'number') throw new Error('Invalid audit ID.'); return { event_id: a.event_id, created_at: string(a.created_at), event_type: string(a.event_type), details: string(a.details), verification_id: nullable(a.verification_id) }; });
  if (verificationId !== undefined && events.some(event => event.verification_id !== verificationId)) throw new Error('The receiver returned events for a different verification. Retry this audit.');
  return events;
}
export async function verify(file: File, manifest: string, signature: string): Promise<Result> {
  const body = new FormData();
  body.append('file', file); body.append('manifest', manifest); body.append('signature', signature);
  return result(await request('/api/verify', { method: 'POST', body }));
}
export async function demo(id: string): Promise<Result> {
  const b = object(await request(`/demo/${id}.json`));
  const bytes = Uint8Array.from(atob(string(b.file_base64)), c => c.charCodeAt(0));
  return verify(new File([bytes], string(b.file_name)), string(b.manifest), string(b.signature));
}
