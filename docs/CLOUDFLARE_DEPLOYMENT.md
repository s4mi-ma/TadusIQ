# Cloudflare deployment

**Live app:** https://rapidready-verify.samihakim779.workers.dev

## TadusIQ release 2026 10 30

Published the TadusIQ interface, shadcn theme switch, notifications, logo options, six downloadable demo packages, ZIP and testing guide on the existing Worker and D1 database. **Current Worker version: `c9ae30c9-b87e-44c5-a1b4-68b99b35f964`.** The service URL retains its existing identifier; no new domain, resource or paid plan was introduced.

- Before publishing: 21 frontend tests and 69 regression tests passed; production build passed. Dry-run validated the pinned Python bundle, existing D1 binding and 55 static files. First publication uploaded 39 changed assets; the final publication corrected only the ZIP start instructions. Worker sources and receiver policy were unchanged.
- Independently verified both existing built-in fixture and new kit signing identities. The existing hosted key matched exactly; inserted one missing public Lab A demo key with INSERT OR IGNORE, then checked both public bytes/identity/active state. No existing key was replaced or reactivated. No private signing material was uploaded.
- The existing public acceptance suite passed: four core scenarios, committed record/audit round trips, unknown-key and sender binding checks, signed-metadata tamper, 2 MiB bound, registry/filter, malformed transport, validation and Origin failures, and TadusIQ HTML branding.
- All six delivered packages fetched from the public site and submitted to the hosted receiver returned their expected outcomes: three ACCEPTED/VALID, then HASH_MISMATCH, INVALID_SIGNATURE and INVALID_METADATA quarantines. Each returned a matching record and nine scoped audit events. Outcome IDs are recorded in the verification log.
- Live logo assets, gallery pages, all 18 attachments, ZIP and PDF matched local source bytes. Cloudflare redirects `/brand/index.html` and `/demo-kit/index.html` to canonical directory URLs; normal redirect following passed. An initial direct-DNS probe failed before testing; checks passed using the normal configured connection.
- Browser confirmed actual acceptance with seven passed checks for `f07ec0b6-c096-4db8-a506-b912fed2b6b3` and the matching nine-event audit. No browser warning/error captured. Screenshot: `tadusiq-live-accepted.jpg`.
- After final publication, health remained OK, both current downloads matched exactly, and pre-deployment record `6a334eb8-40cb-4c2c-8ae4-6233b356703f` plus its nine audit events remained byte-for-byte unchanged. The newly accepted browser record/audit also remained available.
- Guide now points to the hosted app. Previous local-only ZIP/PDF were backed up; all signed attachments remain unchanged. Current demo ZIP SHA-256: `99ba6203b35293a8dd4469531d4789ae562e791726d6d9ec991713f7fc12eaf8`. Original approved MVP archive remains unchanged.

Public downloads: [all demos and guide ZIP](https://rapidready-verify.samihakim779.workers.dev/downloads/TadusIQ_Demo_Kit.zip), [testing guide PDF](https://rapidready-verify.samihakim779.workers.dev/downloads/TadusIQ_Demo_Test_Guide.pdf), [demo gallery](https://rapidready-verify.samihakim779.workers.dev/demo-kit/), [logo options](https://rapidready-verify.samihakim779.workers.dev/brand/).

## Earlier deployment 2026 10 27

The complete app was published and its public HTTP API acceptance checks passed on 2026-10-27. Browser verification also confirmed real acceptance, file-tamper quarantine, Lab C history and nine persisted audit events. No paid plan upgrade was performed.

Previous Worker version: `52986607-1d8f-484f-94dd-0d9b265418fb`. After that frontend-only deployment, readiness remained OK and previously accepted record `83188883-83c9-4838-9536-4123bf436de4` plus its nine audit events remained readable through fresh HTTP requests. Reloaded public browser history showed nine persisted synthetic decisions (two accepted, seven quarantined). Screenshot: `docs/cloudflare-live.png`.

Owner approved Cloudflare Workers + D1 and free-plan compatibility testing on 2026-10-27. This is the complete synthetic demo: frontend static assets, Python FastAPI Worker, and D1 persistent records. Simulated roles remain unauthenticated. Do not upload real laboratory or patient data.

## Architecture

The existing `backend/app/policy.py`, canonical schema and bounded multipart parser are shared with the local verifier. Local verification retains cryptography 49.0.0 and SQLite transactions. The Worker uses native WebCrypto Ed25519 because cryptography 49.0.0 has no usable wheel for the configured Pyodide runtime. No cryptographic mathematical primitive is implemented by the project.

The Worker uses Pydantic 2.12.5 because its core has a supported WebAssembly wheel. Runtime pins and hashes are recorded in `cloudflare/pylock.toml`; tool pins are recorded in `cloudflare/uv.lock` and package-lock.json. Tools: workers-py 1.17.9, workers-runtime-sdk 1.9.5, uv 0.13.6 and Wrangler 4.153.0. Compatibility date 2026-10-27 selects Python 3.14.2 / Pyodide 314.0.7.

D1 cannot hold an interactive database transaction while Python verifies a signature. The Worker reads the primary trust record, verifies the exact manifest, then commits submission, result and nine events in one D1 batch. A conditional submission insert checks that the key's identity, bytes and active status still match the read snapshot. If they changed, the result's foreign key fails and the whole batch rolls back. An operational failure returns a safe error, never ACCEPTED. Public results and audit remain readable by anyone with the demo URL.

## Reproduce preparation

Run from the repository root in PowerShell:

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m tools.prepare_cloudflare
Pop-Location
Push-Location frontend
npm ci --ignore-scripts --no-audit --no-fund
npm run build
Pop-Location
Push-Location cloudflare
uv sync --locked
npm ci --no-audit --no-fund
.\.venv\Scripts\uv.exe run pywrangler dev --port 8787
```

Preparation copies an explicit source whitelist into cloudflare/src/shared, converts the versioned local schema to D1 migration SQL, and creates fresh public synthetic packages. It signs only in the separate sender process and writes only public key material to `cloudflare/seed.sql`. Local SQLite databases are outside the Worker source/assets directories. Regenerating packages creates a new key: seed the corresponding D1 registry and rebuild/deploy assets together. It also registers that public key in the local demo database so localhost fixtures continue to work.

Initialize local D1 before starting the dev server on Windows, avoiding concurrent schema-file access:

```powershell
.\node_modules\.bin\wrangler.cmd d1 migrations apply DB --local
.\node_modules\.bin\wrangler.cmd d1 execute DB --local --file seed.sql
```

## Publish

Cloudflare CLI sign-in is required. Do not put API tokens into source files or chat. Required OAuth scopes used here: account:read, user:read, workers:write, workers_scripts:write and d1:write. The first narrower authorization could provision D1 but Cloudflare denied deployment, requiring the additional script permission.

The configured account ID and D1 ID identify the owner's resources; they are not credentials. For another account create a separate D1 database and update these IDs rather than modifying the owner's database.

```powershell
.\node_modules\.bin\wrangler.cmd d1 migrations apply DB --remote
.\node_modules\.bin\wrangler.cmd d1 execute DB --remote --file seed.sql
.\.venv\Scripts\uv.exe run pywrangler deploy --dry-run
.\.venv\Scripts\uv.exe run pywrangler deploy
```

No paid plan upgrade is authorized or required by this procedure. Free-plan request/CPU/storage quotas still apply. No custom domain or additional integration is included.

After publishing, run the real API acceptance check from backend:

```powershell
..\.venv\Scripts\python.exe -m tools.check_hosted https://THE-DEPLOYED-URL
```

This writes seven synthetic verification records (four core scenarios and three trust/tamper negatives). It verifies expected decisions, persisted record round trips, nine audit events per core scenario, unknown keys, sender binding, signed-metadata tampering, the 2 MiB file bound, lab registry, status filtering, safe validation/transport/Origin errors and frontend HTML. A successful bundle upload alone is not acceptance evidence.

## Evidence so far

- Native Ed25519 and SHA-256 probe passed in workerd.
- 67 tests passed, one existing TestClient deprecation warning; five new tests cover D1 adapter roundtrip, revoke/replace/lab-change guards and audit rollback.
- The same 67 tests also passed with the hosted Pydantic 2.12.5 selection (8.26s, same warning).
- All four full local Worker/D1 scenarios and additional API checks passed.
- Frontend production build passed.
- Source-only deployment bundle dry run passed: 2,228.77 KiB gzip, 447 runtime modules plus ten public static assets.
- New D1 database rapidready-verify created in WEUR; schema and public key applied successfully.
- First publish attempt was denied for missing Worker-script permission. An authorization expired; the user then completed a fresh device authorization including workers_scripts:write. Publishing succeeded.
- Public API acceptance suite passed: core scenario record IDs 617f4ea6-3d85-4a41-920d-a051b0030af0 (valid), 4a573d18-4a81-4e9a-987b-ffcd0c8117ca (modified), 691389da-8673-4074-adc0-f4084089b7fe (invalid signature), 944e109e-10bd-4d82-878f-d76d858f857d (missing metadata). Unknown key, wrong sender, signed metadata tamper, size bound and error checks also passed.
- Public browser accepted 83188883-83c9-4838-9536-4123bf436de4 and quarantined 41c9fb5c-dc08-4227-aed6-cf4b316798ba for HASH_MISMATCH. Lab C history and the selected nine-event audit were visibly verified. A leftover local-SQLite label was corrected to a runtime-neutral prototype audit label and rebuilt successfully.

The earlier approved `RapidReady_Verify_MVP.zip` is preserved as the local MVP snapshot. It predates this hosting adaptation and is not replaced by deployment work.
