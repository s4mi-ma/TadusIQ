import { useRef, useState } from 'react';
import { attachmentLabels, attachmentRoles, loadPackage, readAttachment, suggestAssignments, validateDraft } from './package';
import type { Assignment } from './package';
import { useNotify } from './Notifications';

type Props = { busy: boolean; reading: string; onReading: (target: string) => void; onVerify: (file: File, manifest: string, signature: string) => void };
const message = (error: unknown) => error instanceof Error ? error.message : 'The attachment could not be read. Choose the original file.';
export default function UploadForm({ busy, reading, onReading, onVerify }: Props) {
  const notify = useNotify();
  const [file, setFile] = useState<File | null>(null);
  const [manifest, setManifest] = useState('');
  const [signature, setSignature] = useState('');
  const [names, setNames] = useState({ manifest: '', signature: '' });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [candidates, setCandidates] = useState<File[]>([]);
  const [assignment, setAssignment] = useState<Assignment>({ payload: '', manifest: '', signature: '' });
  const [bulkError, setBulkError] = useState('');
  const [notice, setNotice] = useState('');
  const formRef = useRef<HTMLFormElement>(null);
  const assignmentRef = useRef<HTMLSelectElement>(null);
  const readLock = useRef(false);
  const blocked = busy || !!reading;
  const validation = validateDraft(file, manifest, signature);
  const presence = { payload: !!file, manifest: !!manifest, signature: !!signature };
  const ready = !reading && candidates.length === 0 && Object.keys(validation).length === 0 && !Object.values(fieldErrors).some(Boolean);
  const errors = { ...fieldErrors };
  for (const target of attachmentRoles) {
    if (validation[target] && (submitted || presence[target]) && !errors[target]) errors[target] = validation[target];
  }
  function updateText(target: 'manifest' | 'signature', value: string) {
    if (target === 'manifest') setManifest(value); else setSignature(value);
    setNames(previous => ({ ...previous, [target]: '' }));
    setFieldErrors(previous => { const next = { ...previous }; delete next[target]; return next; });
  }
  async function readOne(attachment: File | undefined, target: 'manifest' | 'signature') {
    if (!attachment || readLock.current) return;
    readLock.current = true; onReading(target); setNotice('');
    try {
      const text = await readAttachment(attachment, target);
      if (target === 'manifest') setManifest(text); else setSignature(text);
      setNames(previous => ({ ...previous, [target]: attachment.name }));
      setFieldErrors(previous => { const next = { ...previous }; delete next[target]; return next; });
      setNotice(`${attachmentLabels[target]} loaded. Package readiness updated.`);
    } catch (error) { setFieldErrors(previous => ({ ...previous, [target]: message(error) })); notify('Attachment could not be loaded', message(error)); }
    finally { readLock.current = false; onReading(''); }
  }
  async function applyPackage() {
    if (readLock.current || busy) return;
    readLock.current = true; onReading('package'); setBulkError(''); setNotice('');
    try {
      const draft = await loadPackage(candidates, assignment);
      setFile(draft.payload); setManifest(draft.manifest); setSignature(draft.signature); setNames(draft.names);
      setFieldErrors({}); setSubmitted(false); setCandidates([]);
      setNotice('Three files loaded. Review the package readiness before submitting.');
    } catch (error) { setBulkError(message(error)); notify('Package could not be loaded', message(error)); }
    finally { readLock.current = false; onReading(''); }
  }
  function submitUpload() {
    if (blocked || readLock.current || candidates.length) return;
    setSubmitted(true);
    const invalid = attachmentRoles.find(target => validation[target] || fieldErrors[target]);
    if (invalid) {
      formRef.current?.querySelector<HTMLElement>(`#${invalid === 'payload' ? 'payload' : invalid + '-file'}`)?.focus();
      notify('Package needs attention', validation[invalid] || fieldErrors[invalid]);
      return;
    }
    if (file) onVerify(file, manifest, signature);
  }
  return <>
    <div className="section-intro"><h2>Submit a package</h2><p>Add the three files prepared by the separate sender.</p></div>
    <div className="package-picker">
      <div><strong>Select the package together</strong><p>Choose three files, then review their assignments.</p></div>
      <div className="file-picker"><span>Select package files</span><input id="package-files" type="file" multiple aria-label="Select package files" disabled={blocked} aria-describedby="package-selection-error" onChange={event => {
        const files = Array.from(event.target.files ?? []); event.target.value = '';
        if (!files.length) return;
        setNotice(''); setBulkError('');
        if (files.length !== 3) { setCandidates([]); setBulkError('Select exactly three files. ZIP and folder imports are not supported.'); notify('Choose three package files', 'Select the synthetic file, manifest and signature together. ZIP and folders are not supported.'); return; }
        setCandidates(files); setAssignment(suggestAssignments(files));
      }} /></div>
      {candidates.length > 0 && <div className="assignment-review"><h3>Review file assignments</h3><p>Each role needs a different file. Your current draft stays until you use these files.</p><fieldset disabled={blocked}>{attachmentRoles.map((target, index) => <label key={target} htmlFor={`assign-${target}`}>{attachmentLabels[target]}<select ref={index === 0 ? assignmentRef : undefined} id={`assign-${target}`} value={assignment[target]} onChange={event => setAssignment(previous => ({ ...previous, [target]: event.target.value }))}><option value="">Choose selected file…</option>{candidates.map((candidate, fileIndex) => <option key={fileIndex} value={String(fileIndex)}>{fileIndex + 1}. {candidate.name} · {candidate.size.toLocaleString()} bytes</option>)}</select></label>)}<div className="assignment-actions"><button className="primary" type="button" onClick={() => { if (attachmentRoles.some(target => !assignment[target])) { setBulkError('Choose a file for every role.'); notify('Check file assignments', 'Choose a different file for each of the three roles.'); assignmentRef.current?.focus(); return; } void applyPackage(); }}>{reading === 'package' ? 'Reading package…' : 'Use these files'}</button><button type="button" onClick={() => { setCandidates([]); setBulkError(''); }}>Cancel</button></div></fieldset></div>}
      <p id="package-selection-error" className="field-error" >{bulkError}</p>
      <p className="sr-only" role="status">{notice}</p>
    </div>
    <section className="package-readiness" aria-label="Package readiness"><div className="readiness-heading"><h3>Package readiness</h3><strong role="status" aria-atomic="true">{ready ? 'Ready to submit' : reading ? 'Reading attachments…' : candidates.length ? 'Review selected files' : 'Complete the attachments'}</strong></div><ul>{attachmentRoles.map(target => {
      const present = target === 'payload' ? !!file : !!(target === 'manifest' ? manifest : signature);
      const state = reading === target || reading === 'package' ? 'Reading' : fieldErrors[target] || (present && validation[target]) ? 'Needs attention' : present ? 'Loaded' : 'Missing';
      return <li key={target}><span>{attachmentLabels[target]}</span><strong className={state === 'Needs attention' ? 'fail' : ''}>{state}</strong></li>;
    })}</ul><p>Readiness checks attachments only. Signature and file integrity are checked by the receiver after submission.</p></section>
    <form ref={formRef} noValidate onSubmit={event => { event.preventDefault(); submitUpload(); }}><fieldset disabled={blocked || candidates.length > 0}>
      <div className="attachment payload-attachment"><div className="attachment-heading"><label htmlFor="payload">Synthetic file</label><span>Up to 2 MiB</span></div><strong className="payload-name">{file?.name ?? 'Choose a file to verify'}</strong><p>{file ? `${file.size.toLocaleString()} bytes` : 'Only synthetic development data is permitted.'}</p><div className="file-picker"><span>{file ? 'Replace file' : 'Choose file'}</span><input id="payload" type="file" aria-invalid={!!errors.payload} aria-describedby="payload-error" onChange={event => { setFile(event.target.files?.[0] ?? null); event.target.value = ''; setNotice(''); setFieldErrors(previous => { const next = { ...previous }; delete next.payload; return next; }); }} /></div><p id="payload-error" className="field-error" >{errors.payload}</p></div>
      {(['manifest', 'signature'] as const).map(target => <div className="attachment" key={target}><div className="attachment-heading"><label htmlFor={`${target}-file`}>{target === 'manifest' ? 'Signed manifest' : 'Detached signature'}</label><span>{target === 'manifest' ? 'JSON · Up to 8 KiB' : 'Ed25519 · Base64'}</span></div><div className="file-picker"><span>{(target === 'manifest' ? manifest : signature) ? 'Replace file' : 'Choose file'}</span><input id={`${target}-file`} type="file" accept={target === 'manifest' ? '.json' : '.txt'} aria-invalid={!!errors[target]} aria-describedby={`${target}-hint ${target}-error`} onChange={event => { void readOne(event.target.files?.[0], target); event.target.value = ''; }} /></div><p id={`${target}-hint`} className="attachment-state">{reading === target ? 'Reading attachment…' : names[target] ? `Loaded: ${names[target]}` : (target === 'manifest' ? manifest : signature) ? 'Using pasted contents' : 'No contents loaded'}</p><details className="paste-details"><summary>Paste or inspect contents</summary><label htmlFor={target}>{target === 'manifest' ? 'Exact canonical JSON' : 'Exact signature contents · 88 characters'}</label><textarea id={target} rows={target === 'manifest' ? 5 : 3} value={target === 'manifest' ? manifest : signature} aria-invalid={!!errors[target]} aria-describedby={`${target}-error`} onChange={event => updateText(target, event.target.value)} spellCheck={false} /></details><p id={`${target}-error`} className="field-error" >{errors[target]}</p></div>)}
      <div className="submit-footer"><p>Preserve the exact signed contents. Do not reformat JSON.</p><button className="primary" type="submit">{busy ? 'Verifying…' : reading ? 'Reading file…' : 'Verify package'}<span aria-hidden="true">→</span></button></div>
    </fieldset></form>
  </>;
}
