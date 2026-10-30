import type { Result } from './api';

export function suggestedNextStep(result: Result): string {
  if (result.status === 'ACCEPTED') return 'Review the recorded checks and audit events.';
  switch (result.reason_code) {
    case 'HASH_MISMATCH':
    case 'SIZE_MISMATCH': return 'Request the original file and its matching signed package from the sender.';
    case 'INVALID_SIGNATURE': return 'Obtain a matching manifest and signature pair from the sender.';
    case 'INVALID_METADATA': return result.checks.some(check => check.name === 'file_name' && check.status === 'FAIL')
      ? 'The uploaded filename does not match the signed manifest. Request the original file with its original name and matching signed package.'
      : 'Request a corrected, newly signed package from the sender. Do not edit the signed manifest yourself.';
    case 'UNKNOWN_OR_REVOKED_KEY':
    case 'SENDER_KEY_MISMATCH': return 'Ask the sender and registry maintainer to confirm the authorized signing identity.';
    default: return 'Review the individual checks and contact the sender.';
  }
}
