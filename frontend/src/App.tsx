import { useEffect, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { Switch } from './components/ui/switch';
import { createAppearanceMotion } from './appearance-motion';
import { audit, demo, history, request, verify } from './api';
import type { Audit, Result } from './api';
import UploadForm from './UploadForm';
import AuditTrail from './AuditTrail';
import { suggestedNextStep } from './guidance';
import { applyAppearance } from './appearance';
import type { Appearance } from './appearance';
import { useNotify } from './Notifications';

type Page = 'Verify package' | 'History' | 'Audit trail';
type IconName = 'verify' | 'history' | 'audit' | 'arrow' | 'refresh' | 'file' | 'check' | 'close' | 'sun' | 'moon';
const pages: [Page, IconName][] = [['Verify package', 'verify'], ['History', 'history'], ['Audit trail', 'audit']];
const scenarios = [
  ['valid', 'Valid package', 'Complete metadata, trusted signature, intact file.', 'Accepted'],
  ['modified-file', 'Modified file', 'A single byte changes after the file is signed.', 'Quarantined'],
  ['invalid-signature', 'Invalid signature', 'The detached signature has been altered.', 'Quarantined'],
  ['missing-metadata', 'Missing metadata', 'The required sample identifier is absent.', 'Quarantined'],
];
const labs = [['A', 'Human Health', 'Prepare & send'], ['B', 'Animal Health', 'Receive & verify'], ['C', 'Environmental Health', 'Review results']];
const message = (error: unknown) => error instanceof Error ? error.message : 'An unexpected error occurred.';
const readable = (text: string) => text.replaceAll('_', ' ').toLowerCase();
const date = (text: string) => { const value = new Date(text); return Number.isNaN(value.getTime()) ? text : value.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }); };
function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, string> = {
    sun: 'M12 8a4 4 0 1 0 0 8a4 4 0 0 0 0-8ZM12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5',
    moon: 'M20.5 13A8.5 8.5 0 0 1 11 3.5 8.5 8.5 0 1 0 20.5 13Z',
    verify: 'M12 3 4 6v5c0 5 8 10 8 10s8-5 8-10V6l-8-3ZM8 12l3 3 5-6',
    history: 'M4 5v5h5M4 10a8 8 0 1 1 1 8M12 7v5l3 2',
    audit: 'M8 3h8v4H8zM8 5H5v16h14V5h-3M8 12h8M8 16h6',
    arrow: 'M5 12h14m-5-5 5 5-5 5', refresh: 'M20 4v6h-6M4 20v-6h6M5 9a7 7 0 0 1 12-4l3 5M4 14l3 5a7 7 0 0 0 12-4',
    file: 'M14 3H5v18h14V8l-5-5Zm0 0v5h5M8 13h8M8 17h5', check: 'm5 12 4 4L19 6', close: 'm6 6 12 12M18 6 6 18',
  };
  return <svg className="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
function Decision({ status }: { status: Result['status'] }) {
  return <span className={`badge ${status.toLowerCase()}`}><span className="status-dot" />{status === 'ACCEPTED' ? 'Accepted' : 'Quarantined'}</span>;
}
function ResultInspector({ result, onAudit, onClose }: { result: Result; onAudit: () => void; onClose: () => void }) {
  return <section className="inspector motion-enter" aria-label="Verification result">
    <div className="section-bar"><h2>Verification result</h2><button className="icon-button" onClick={onClose} aria-label="Close verification result"><Icon name="close" /></button></div>
    <div className="decision-summary"><Decision status={result.status} /><h3>{result.reason_code === 'VALID' ? 'Package verified' : readable(result.reason_code)}</h3><p>{result.details}</p></div>
    <div className="next-step"><h3>Suggested next step</h3><p>{suggestedNextStep(result)}</p></div>
    <div className="result-file"><Icon name="file" /><div><strong>{result.file_name ?? 'Invalid metadata'}</strong><small>{result.file_size_bytes.toLocaleString()} bytes · {date(result.received_at)}</small></div></div>
    <div className="checks">{result.checks.map(check => <div key={check.name}><span>{readable(check.name)}</span><strong className={check.status.toLowerCase()}>{check.status === 'PASS' ? 'Passed' : check.status === 'FAIL' ? 'Failed' : 'Skipped'}</strong></div>)}</div>
    <details className="technical-details"><summary>Technical details</summary><dl><dt>Verified sender</dt><dd>{result.verified_laboratory_id ?? 'Not authenticated'}</dd><dt>Claimed sender</dt><dd>{result.claimed_laboratory_id ?? 'Unavailable'}</dd><dt>Computed SHA-256</dt><dd className="mono">{result.computed_sha256 || 'Unavailable'}</dd><dt>Record ID</dt><dd className="mono">{result.verification_id}</dd><dt>Received</dt><dd>{result.received_at}</dd></dl></details>
    <button className="audit-link" onClick={onAudit}>View audit trail <Icon name="arrow" /></button>
    <p className="inspector-note">{result.status === 'QUARANTINED' ? 'Quarantine is a recorded decision. Uploaded file content is not retained.' : 'Origin and file integrity checks only. This does not establish biological validity.'}</p>
  </section>;
}
export default function App() {
  const notify = useNotify();
  const [appearance, setAppearance] = useState<Appearance>(() => document.documentElement.dataset.theme === 'light' ? 'light' : 'dark');
  const [appearanceNotice, setAppearanceNotice] = useState('');
  const [appearanceMotion] = useState(() => createAppearanceMotion({
    startTransition: typeof document.startViewTransition === 'function'
      ? update => document.startViewTransition(update) : undefined,
    reducedMotion: () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    setAnimating: active => { if (active) document.documentElement.dataset.themeTransition = 'active'; else delete document.documentElement.dataset.themeTransition; },
    apply: applyAppearance,
    onApplied: (theme, saved) => flushSync(() => {
      setAppearance(theme);
      setAppearanceNotice(saved ? '' : 'Appearance changed for this visit. This browser could not save your preference.');
      if (!saved) notify('Preference not saved', 'Your theme changed for this visit. Browser storage is unavailable.', 'warning');
    }),
  }));
  useEffect(() => () => appearanceMotion.dispose(), [appearanceMotion]);
  const [role, setRole] = useState('B');
  const [page, setPage] = useState<Page>('Verify package');
  const [mode, setMode] = useState<'upload' | 'demo'>('upload');
  const [records, setRecords] = useState<Result[]>([]);
  const [events, setEvents] = useState<Audit[]>([]);
  const [selected, setSelected] = useState<Result | null>(null);
  const [error, setError] = useState('');
  const [loadError, setLoadError] = useState('');
  const [online, setOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [reading, setReading] = useState('');
  const lock = useRef(false);
  const [revision, setRevision] = useState(0);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setLoadError(''); setLoading(true);
    Promise.all([history(controller.signal), audit(controller.signal), request('/api/health', { signal: controller.signal })])
      .then(([rows, logs, health]) => {
        if (controller.signal.aborted) return;
        setRecords(rows); setEvents(logs);
        setOnline(!!health && typeof health === 'object' && 'status' in health && health.status === 'OK');
      }).catch(error => { if (!controller.signal.aborted) { setLoadError(message(error)); setOnline(false); notify('Records could not be refreshed', message(error)); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [revision, notify]);
  async function submit(operation: () => Promise<Result>) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError(''); setSelected(null);
    try {
      const result = await operation(); setSelected(result);
      if (result.status === 'QUARANTINED') notify('Package quarantined', result.details + ' Review the recorded checks and suggested next step.', 'warning');
    }
    catch (error) { const details = `${message(error)} No completed decision was received. Refresh history before retrying.`; setError(details); notify('Verification not confirmed', details); }
    finally { lock.current = false; setBusy(false); setRevision(v => v + 1); }
  }
  const counts = { ALL: records.length, ACCEPTED: records.filter(r => r.status === 'ACCEPTED').length, QUARANTINED: records.filter(r => r.status === 'QUARANTINED').length };
  const query = search.trim().toLowerCase();
  const filtered = records.filter(r => (filter === 'ALL' || r.status === filter) && `${r.file_name ?? ''} ${r.verification_id} ${r.reason_code} ${r.verified_laboratory_id ?? ''}`.toLowerCase().includes(query));
  const blocked = busy || !!reading;
  const inspector = selected ? <ResultInspector key={selected.verification_id} result={selected} onClose={() => setSelected(null)} onAudit={() => setPage('Audit trail')} /> : <section className="inspector empty-inspector"><span className="empty-symbol"><Icon name="verify" /></span><h2>{busy ? 'Verifying package…' : 'Every decision, explained.'}</h2><p>{busy ? 'Waiting for a committed receiver decision. Checks will appear when the response arrives.' : 'Submit a package to see its decision, individual checks, and verification record here.'}</p><div className="empty-checks"><span>Metadata</span><span>Sender & signature</span><span>File integrity</span></div><p className="inspector-note">SHA-256 + Ed25519 · Private keys stay with the separate sender.</p></section>;
  return <div className="shell">
    <a className="skip-link" href="#main">Skip to workspace</a>
    <aside className="sidebar"><a className="brand" href="#main"><span className="brand-mark"><img src="/brand/tadusiq-01-signal.svg" alt="" width="28" height="28" /></span><span className="brand-wordmark">Tadus<strong>IQ</strong></span></a>
      <div className="role-switch"><label htmlFor="role">Simulated role</label><div className="role-select"><select id="role" value={role} disabled={blocked} onChange={event => { setRole(event.target.value); if (event.target.value === 'C') setPage('History'); }}>{labs.map(([id, name]) => <option key={id} value={id}>Lab {id} · {name}</option>)}</select></div><small>{labs.find(lab => lab[0] === role)?.[2]}</small></div>
      <nav aria-label="Main navigation">{pages.map(([item, icon]) => <button key={item} className={page === item ? 'active' : ''} aria-current={page === item ? 'page' : undefined} onClick={() => setPage(item)}><Icon name={icon} /><span>{item}</span>{item === 'History' && <span className="nav-count">{records.length}</span>}</button>)}</nav>
      <div className="sidebar-note"><svg className="collaboration-logo" viewBox="0 0 48 40" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" aria-hidden="true"><path d="M24 2 35 8v12l-11 6-11-6V8Z" /><path d="m13 14 11 6v12l-11 6-11-6V20Z" /><path d="m35 14 11 6v12l-11 6-11-6V20Z" /></svg><strong>One Health collaboration</strong><p>Human, animal and environmental health.</p><small>Role selection is a simulation, not authentication.</small></div>
      <div className="sidebar-version">Synthetic prototype <span>v0.1</span></div>
    </aside>
    <div className="main-shell"><header className="topbar"><div className="workspace-name">Verification workspace <span className="badge neutral">Synthetic demo</span></div><div className="topbar-actions"><div className="appearance-control"><label htmlFor="appearance">Dark mode</label><span className="appearance-switch"><Icon name="sun" /><Switch id="appearance" checked={appearance === 'dark'} onCheckedChange={checked => { const theme = checked ? 'dark' : 'light'; setAppearance(theme); appearanceMotion.change(theme); }} /><Icon name="moon" /></span></div><span className={`connection ${online && !loading ? 'online' : ''}`}><span className="status-dot" />{loading ? 'Connecting…' : online ? 'Receiver ready' : 'Receiver unavailable'}</span><button className="refresh-button" onClick={() => setRevision(v => v + 1)} disabled={busy || loading} aria-label="Refresh records" title="Refresh records"><Icon name="refresh" /><span>{loading ? 'Refreshing…' : 'Refresh'}</span></button></div></header>
    <main id="main" tabIndex={-1}>
      {appearanceNotice && <p className="preference-notice" role="status">{appearanceNotice}</p>}
      <div className="heading"><div><h1>{page}</h1><p>{page === 'Verify package' ? 'Check the origin and integrity of a laboratory package.' : page === 'History' ? 'Review recorded decisions and the checks behind them.' : 'Follow the events behind each verification decision.'}</p></div>{page === 'History' && role !== 'C' && <button className="primary" onClick={() => setPage('Verify package')}><Icon name="verify" />Verify package</button>}</div>
      {loadError && <div className="error"><strong>Records could not be refreshed.</strong><p>{loadError} Previously loaded records may be stale.</p><button onClick={() => setRevision(v => v + 1)} disabled={busy || loading}>Retry refresh</button></div>}
      <div className="sr-only" role="status" aria-live="polite">{busy ? 'Verification in progress. Waiting for a committed backend decision.' : selected ? `${selected.status}. ${selected.details}` : ''}</div>
      {error && <div className="error"><strong>Verification could not be confirmed</strong><p>{error}</p><button onClick={() => { setPage('History'); setRevision(v => v + 1); }}>Review history</button></div>}
      <div hidden={page !== 'Verify package'}>
        {role === 'C' && <section className="surface review-notice"><Icon name="history" /><h2>Ready for review</h2><p>Laboratory C reviews verification history and audit events in this simulated workflow.</p><button onClick={() => setPage('History')}>Open history <Icon name="arrow" /></button></section>}
        <div className="workspace-grid" hidden={role === 'C'}><section className="surface submission">
          <div className="view-switch" role="group" aria-label="Package source"><button aria-pressed={mode === 'upload'} onClick={() => setMode('upload')} disabled={blocked}>Upload package</button><button aria-pressed={mode === 'demo'} onClick={() => setMode('demo')} disabled={blocked}>Try a demo</button></div>
          <div hidden={mode !== 'upload'}><UploadForm busy={busy} reading={reading} onReading={setReading} onVerify={(file, manifest, signature) => void submit(() => verify(file, manifest, signature))} /></div>
          <div hidden={mode !== 'demo'}><div className="section-intro"><h2>Test the verification flow</h2><p>Four synthetic packages. Each run uses the real receiver API.</p></div><div className="scenarios">{scenarios.map(([id, title, description, outcome]) => <button key={id} disabled={blocked} onClick={() => void submit(() => demo(id))}><span className={`scenario-symbol ${id === 'valid' ? 'valid' : ''}`}><Icon name={id === 'valid' ? 'check' : 'file'} /></span><span><strong>{title}</strong><small>{description}</small><span className="expected">Expected: {outcome}</span></span><Icon name="arrow" /></button>)}</div><div className="demo-note"><Icon name="verify" /><p>Prepared by the separate Lab A sender. The browser never holds a private key. <a className="text-link" href="/demo-kit/index.html" target="_blank" rel="noreferrer">Download six demo packages</a></p></div></div>
        </section>{inspector}</div>
      </div>
      {page === 'History' && <><div className="history-toolbar"><div className="filters" role="group" aria-label="Filter decisions">{(['ALL', 'ACCEPTED', 'QUARANTINED'] as const).map(status => <button key={status} aria-pressed={filter === status} onClick={() => setFilter(status)}>{status === 'ALL' ? 'All decisions' : status === 'ACCEPTED' ? 'Accepted' : 'Quarantined'}<span>{counts[status]}</span></button>)}</div><label className="search-label"><span className="sr-only">Search loaded records</span><input type="search" placeholder="Search loaded records…" value={search} onChange={event => setSearch(event.target.value)} /></label></div><p className="window-note">Latest 50 records only · Search by file, record ID, reason, or verified sender.{loading ? ' Refreshing…' : ''}</p><div className={`history-grid ${selected ? 'with-inspector' : ''}`}><section className="surface history-surface" aria-label="Recorded verifications" aria-busy={loading}><div className="table-wrap"><table><thead><tr><th scope="col">File / received</th><th scope="col">Decision</th><th scope="col">Reason</th><th scope="col"><span className="sr-only">Inspect</span></th></tr></thead><tbody>{filtered.map(record => <tr key={record.verification_id} className={selected?.verification_id === record.verification_id ? 'selected-row' : ''}><td><strong>{record.file_name ?? 'Invalid metadata'}</strong><time dateTime={record.received_at}>{date(record.received_at)}</time><small className="mobile-reason">{readable(record.reason_code)}</small></td><td><Decision status={record.status} /></td><td className="reason-cell">{readable(record.reason_code)}</td><td><button className="icon-button" aria-label={`Inspect ${record.verification_id}`} aria-pressed={selected?.verification_id === record.verification_id} onClick={() => setSelected(record)}><Icon name="arrow" /></button></td></tr>)}</tbody></table></div>{!filtered.length && <div className="empty-state"><Icon name="history" /><h2>{loading ? 'Loading records…' : records.length ? 'No matching records' : loadError ? 'Records unavailable' : 'No verifications yet'}</h2><p>{loading ? 'Fetching decisions from the receiver.' : records.length ? 'Try another search or decision filter.' : loadError ? 'Retry the refresh to load the receiver history.' : 'Verify a synthetic package to create the first record.'}</p></div>}</section>{selected && inspector}</div></>}
      {page === 'Audit trail' && <AuditTrail selected={selected} overview={events} overviewLoading={loading} revision={revision} onShowAll={() => setSelected(null)} />}
      <footer><span>TadusIQ · Synthetic data only · Roles are simulated, not authentication.</span><span>Quarantine is logical; uploaded content is not retained.</span></footer>
    </main></div>
  </div>;
}
