# TadusIQ

[Live demo](https://tadusiq.tadusiq.workers.dev/) · [Demo packages](https://tadusiq.tadusiq.workers.dev/demo-kit/) · [Testing guide](https://tadusiq.tadusiq.workers.dev/downloads/TadusIQ_Demo_Test_Guide.pdf)

A synthetic three-laboratory demonstration. Lab A prepares signed development packages, Lab B verifies them with SHA-256 and Ed25519, and Lab C reviews results and the SQLite audit. No patient data, biological analysis or external services are used.

## Start locally (Windows PowerShell)

Tested with Python 3.14.3, Node 24.14.0 and npm 11.9.0. Run from the project root. Initial dependency installation requires internet access. Do not expose these development servers to a network.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock
Push-Location backend
..\.venv\Scripts\python.exe -m tools.prepare_demo
Pop-Location
Push-Location frontend
npm ci --ignore-scripts --no-audit --no-fund
Pop-Location
```

The sender creates four public synthetic packages in `fixtures/generated` and `frontend/public/demo`, and registers its public key in `var/rapidready.sqlite3`. Its private key exists only in the sender process. Re-running preparation generates a new key and overwrites the generated demo packages; existing public keys/history remain. Scenario outcomes are deterministic; signatures/key IDs differ between preparations.

Start the backend in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```powershell
Set-Location frontend
npm run dev
```

Open [TadusIQ](http://127.0.0.1:5173/). Stop either server with Ctrl+C. Ports 8000/5173 must be available. If backend readiness fails, run preparation against the same database used by the server. An optional `RAPIDREADY_DB` environment variable selects the receiver database; pass the matching absolute path with `--database` to the sender.

## Demonstrate

1. Use the **Simulated role** selector to select Lab A to represent the sender. Package preparation/signing happens in the separate CLI above, not in the browser.
2. Select Lab B, open **Verify package → Try a demo**, and run each synthetic scenario. Every button posts to the actual receiver API: valid → ACCEPTED; modified file → HASH_MISMATCH; invalid signature → INVALID_SIGNATURE; missing metadata → INVALID_METADATA. The latter three are QUARANTINED.
3. For manual submission, open **Upload package** and use **Select package files** to select `synthetic-result.txt`, `manifest.json`, and `signature.txt` from `fixtures/generated/valid`. Review the three assignments, then choose **Use these files**. Distinct files are required for each role; **Cancel** and failed imports preserve the current draft. Individual file inputs and **Paste or inspect contents** remain available. Preserve exact signed contents: do not reformat JSON or add a signature newline. Draft uploads persist while navigating within the app, but not across a page reload.
4. The **Package readiness** checklist shows missing, reading, loaded, or invalid attachments. **Ready to submit** only confirms local attachment checks, not signature or file integrity. Choose **Verify package** for the receiver's decision, then read **Suggested next step** for guidance.
5. Select Lab C to open **History**. Filter/search loaded decisions and use the arrow action to inspect a record, then **View audit trail** to fetch that record's events directly. **Retry this audit** retries only the selected audit. **Show all events** returns to the recent overview. Role selection only changes the UI; it is not access control.
6. Use the **Dark mode** switch in the top bar: on means dark, off means light. Click it or focus it and press Space/Enter. Dark is the first-visit default; only the appearance preference is remembered locally. If browser storage is blocked, switching still works for the current visit. Subtle transitions respect reduced-motion preferences and fall back to immediate theme changes where unsupported.

The dashboard displays the latest 50 results and an overview of the latest 100 audit events. History filtering/search applies to those loaded results. A selected record's audit is fetched separately, up to 200 events; a notice appears when that limit is reached. A network failure means the client does not know whether a decision committed; refresh history before retrying a submission. Duplicate submissions are not deduplicated.

## Validate

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
Push-Location frontend
npm run build
npm test
Pop-Location
```

Tests use temporary databases and synthetic keys. Some execution sandboxes block Windows asyncio loopback sockets before the app starts; run the tests in a normal local terminal with loopback permitted. Starlette currently emits a TestClient HTTPX deprecation warning; the pinned compatibility path passes the tests.

## Scope and evidence

See [manifest contract](docs/MANIFEST_V1.md), [API contract](docs/API_CONTRACT.md), [test evidence](docs/TEST_RESULTS.md), [final audit](docs/FINAL_AUDIT.md), and [Context7 log](docs/CONTEXT7_VERIFICATION_LOG.md).

Quarantine is a database decision: uploaded content is processed in memory and not retained. The local audit is not tamper-proof. This is not production authentication, scientific validation, equipment interoperability, replay prevention or an independently audited security system. All dependencies are pinned; vulnerability scanning and production deployment are outside the verified scope.

The approved local MVP snapshot is `RapidReady_Verify_MVP.zip`; its verified contents are listed in [EXPORT_CONTENTS.md](docs/EXPORT_CONTENTS.md). It predates the Cloudflare hosting adaptation and is preserved unchanged locally, outside the public source repository.

## Cloudflare hosting

Cloudflare Workers + D1 was approved on 2026-10-27. The hosted receiver uses the same strict decision policy and multipart parser as the local app, with native WebCrypto Ed25519 and D1 atomic writes. See [Cloudflare deployment instructions and evidence](docs/CLOUDFLARE_DEPLOYMENT.md). The deployment log there distinguishes local runtime verification from a verified public deployment.

Open the hosted app: **https://tadusiq.tadusiq.workers.dev**. The full public API acceptance suite and core browser workflow passed. No paid plan upgrade was performed; free-plan quotas apply. All roles and data remain synthetic; anyone with the URL can view this demonstration's records.


## TadusIQ review assets

- [All six demos and the testing guide in one ZIP](https://tadusiq.tadusiq.workers.dev/downloads/TadusIQ_Demo_Kit.zip). Extract first, then open the included three-page PDF guide. A [standalone guide PDF](https://tadusiq.tadusiq.workers.dev/downloads/TadusIQ_Demo_Test_Guide.pdf) is also available. The archive contains only demo files and presenter materials; it preserves the original MVP ZIP and does not install or publish the app.

- [Compare four editable logo options](https://tadusiq.tadusiq.workers.dev/brand/index.html). Option 01 is used in the live app. Source SVGs are under `frontend/public/brand`.
- [Download six demo packages](https://tadusiq.tadusiq.workers.dev/demo-kit/index.html), or use `frontend/public/demo-kit`. Each numbered folder contains a payload, manifest and signature; select those three files together. See the kit's README for expected results and receiver compatibility. The separate local sender registered only a public demo key in the local and hosted registries. Private signing material was never exported.
- Error notifications remain visible until dismissed and supplement field-level guidance/retry controls. Errors do not retry automatically or create an accepted result. A recorded quarantine shows a warning notification and its checks.
- TadusIQ is published at https://tadusiq.tadusiq.workers.dev/ on the renamed existing Cloudflare Worker. The public demo signing key is registered in the hosted receiver, so all six supplied examples can be tested there. Existing database identifiers and saved appearance preferences remain compatible; historical evidence and the original approved archive are preserved.
