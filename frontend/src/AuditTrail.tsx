import { useEffect, useState } from 'react';
import { audit } from './api';
import type { Audit, Result } from './api';
import { useNotify } from './Notifications';

type Props = { selected: Result | null; overview: Audit[]; overviewLoading: boolean; revision: number; onShowAll: () => void };
type ScopedAudit = { id: string | null; status: 'loading' | 'loaded' | 'error'; events: Audit[]; error: string };
const date = (text: string) => { const value = new Date(text); return Number.isNaN(value.getTime()) ? text : value.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }); };
export default function AuditTrail({ selected, overview, overviewLoading, revision, onShowAll }: Props) {
  const notify = useNotify();
  const selectedId = selected?.verification_id;
  const [attempt, setAttempt] = useState(0);
  const [scoped, setScoped] = useState<ScopedAudit>({ id: null, status: 'loading', events: [], error: '' });
  useEffect(() => {
    if (selectedId === undefined) return;
    const controller = new AbortController();
    let ignore = false;
    setScoped({ id: selectedId, status: 'loading', events: [], error: '' });
    audit(controller.signal, selectedId).then(events => {
      if (!ignore) setScoped({ id: selectedId, status: 'loaded', events, error: '' });
    }).catch(error => {
      if (!ignore) {
        const details = error instanceof Error ? error.message : 'Audit events could not be loaded.';
        setScoped({ id: selectedId, status: 'error', events: [], error: details });
        notify('Audit could not be loaded', details);
      }
    });
    return () => { ignore = true; controller.abort(); };
  }, [selectedId, revision, attempt, notify]);
  const current = scoped.id === selectedId;
  const loading = selected ? !current || scoped.status === 'loading' : overviewLoading;
  const error = selected && current && scoped.status === 'error' ? scoped.error : '';
  const events = selected ? current && scoped.status === 'loaded' ? scoped.events : [] : overview;
  return <section className="surface audit-surface motion-enter" aria-label="Audit events" aria-busy={loading}>
    <div className="section-bar"><div><h2>{selected ? 'Selected verification audit' : 'Recent audit events'}</h2><p>{selected ? 'Events fetched directly for this record, newest first.' : 'Latest 100 events loaded, newest first.'} Prototype audit; not tamper-proof.</p></div>{selected && <button onClick={onShowAll}>Show all events</button>}</div>
    {selected && <div className="audit-scope"><span className={`badge ${selected.status.toLowerCase()}`}>{selected.status === 'ACCEPTED' ? 'Accepted' : 'Quarantined'}</span><span>{selected.file_name ?? 'Invalid metadata'}</span><span className="mono">{selected.verification_id}</span></div>}
    {loading && <p className="audit-loading" role="status">{selected ? 'Loading this verification’s audit events…' : 'Refreshing recent events…'}</p>}
    {error && <div className="error"><strong>This audit could not be loaded</strong><p>{error}</p><button onClick={() => setAttempt(value => value + 1)}>Retry this audit</button></div>}
    {selected && events.length >= 200 && <p className="audit-limit" role="status">Showing the latest 200 events for this verification. Additional events may exist.</p>}
    <ol className="audit">{events.map(event => <li key={event.event_id}><span className="timeline-dot" aria-hidden="true" /><div><strong>{event.event_type.replaceAll('_', ' ').toLowerCase()}</strong><p>{event.details}</p></div><time dateTime={event.created_at}>{date(event.created_at)}</time></li>)}</ol>
    {!loading && !error && !events.length && <div className="empty-state"><h2>No audit events found</h2><p>{selected ? 'The receiver returned no events for this verification.' : 'Receiver audit events will appear here.'}</p></div>}
  </section>;
}
