export type Assignment = { payload: string; manifest: string; signature: string };
export const attachmentRoles = ['payload', 'manifest', 'signature'] as const;
export const attachmentLabels = { payload: 'Synthetic file', manifest: 'Manifest', signature: 'Signature' };

export function suggestAssignments(files: readonly File[]): Assignment {
  const unique = (name: string) => {
    const matches = files.map((file, index) => file.name === name ? String(index) : '').filter(Boolean);
    return matches.length === 1 ? matches[0] : '';
  };
  const manifest = unique('manifest.json');
  const signature = unique('signature.txt');
  const remaining = files.map((_, index) => String(index)).filter(index => index !== manifest && index !== signature);
  return { manifest, signature, payload: manifest && signature && remaining.length === 1 ? remaining[0] : '' };
}

export async function readAttachment(file: File, target: 'manifest' | 'signature'): Promise<string> {
  const limit = target === 'manifest' ? 8192 : 88;
  if (!file.size) throw new Error(`${attachmentLabels[target]} is empty. Choose another file.`);
  if (file.size > limit) throw new Error(`${attachmentLabels[target]} exceeds ${target === 'manifest' ? '8 KiB' : '88 bytes'}. Choose another file.`);
  try {
    // Signed bytes must survive decoding, including a BOM that the receiver will reject.
    return new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(await file.arrayBuffer());
  } catch (error) {
    if (error instanceof TypeError) throw new Error(`${attachmentLabels[target]} is not valid UTF-8. Choose the original sender file.`);
    throw error;
  }
}

export function validateDraft(file: File | null, manifest: string, signature: string): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!file) errors.payload = 'Choose a synthetic file.';
  else if (!file.size) errors.payload = 'Synthetic file is empty. Choose another file.';
  else if (file.size > 2097152) errors.payload = 'Synthetic file exceeds 2 MiB.';
  for (const [target, text, limit] of [['manifest', manifest, 8192], ['signature', signature, 88]] as const) {
    if (!text) errors[target] = `Load ${attachmentLabels[target].toLowerCase()} or paste its exact contents.`;
    else if (new TextEncoder().encode(text).length > limit) errors[target] = `${attachmentLabels[target]} exceeds ${target === 'manifest' ? '8 KiB' : '88 bytes'}. Preserve the original contents.`;
  }
  return errors;
}

export async function loadPackage(files: readonly File[], assignment: Assignment) {
  if (files.length !== 3) throw new Error('Select exactly three files: a synthetic file, manifest, and signature.');
  const indices = attachmentRoles.map(role => assignment[role]);
  if (indices.some(index => !/^[0-2]$/.test(index)) || new Set(indices).size !== 3) {
    throw new Error('Assign a different selected file to each role.');
  }
  const payload = files[Number(assignment.payload)];
  if (!payload.size || payload.size > 2097152) throw new Error('Synthetic file must contain 1 byte to 2 MiB.');
  const [manifest, signature] = await Promise.all([
    readAttachment(files[Number(assignment.manifest)], 'manifest'),
    readAttachment(files[Number(assignment.signature)], 'signature'),
  ]);
  return { payload, manifest, signature, names: { manifest: files[Number(assignment.manifest)].name, signature: files[Number(assignment.signature)].name } };
}
