# TadusIQ presenter kit

Six synthetic packages, each containing exactly three upload files. All are signed by the separate Lab A sender; the human/animal/environment labels describe fictional development data, not real biological results.

## Present the workflow

1. Open the hosted app at https://rapidready-verify.samihakim779.workers.dev/ and select simulated Lab B.
2. Pick one folder below. Select its payload, manifest.json and signature.txt together.
3. Confirm three distinct assignments, then Use these files. Ready to submit is only a local attachment check.
4. Submit manually. Inspect the recorded checks, suggested next step and linked audit events.
5. Select simulated Lab C to demonstrate history/review.

| Folder | Payload | Expected recorded outcome |
|---|---|---|
| 01-valid-human | 01-valid-human.txt | ACCEPTED / VALID |
| 02-valid-animal | 02-valid-animal.csv | ACCEPTED / VALID |
| 03-valid-environment | 03-valid-environment.json | ACCEPTED / VALID |
| 04-modified-file | 04-modified-file.txt | QUARANTINED / HASH_MISMATCH |
| 05-invalid-signature | 05-invalid-signature.txt | QUARANTINED / INVALID_SIGNATURE |
| 06-missing-metadata | 06-missing-metadata.txt | QUARANTINED / INVALID_METADATA |

## Sending the examples

Send each complete folder as a unit. Do not rename a payload, pair files from different folders, reformat JSON, add whitespace to signed text, or edit signature.txt. TadusIQ imports three files, not ZIP/folders. Instructions, catalog and public-key.json stay outside the three upload files.

These packages are prepared for the hosted TadusIQ receiver database. A different receiver must have the supplied public demo key independently registered by its maintainer before the valid examples can pass. The upload itself never grants trust. The kit contains no private key, and its signatures cannot be regenerated without preparing a new kit. Keep this kit intact; to generate another, run the sender with a fresh output directory and the intended local database.

No patient data, production authentication or biological validation. Quarantine is logical. The local audit is not tamper-proof.
