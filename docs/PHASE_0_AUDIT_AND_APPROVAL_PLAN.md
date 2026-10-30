# RapidReady Verify Phase 0 audit and approval plan

Date: 2026-10-26. Status: **proposed implementation; awaiting owner approval**.

The French source document supports a small synthetic exchange demonstration. The prototype kit is a planning package, not executable software. Its manifest, persistence and API contracts need amendments to satisfy the owner's current request. No application code, dependency installation, third-party skill adoption, key generation or final ZIP creation has occurred.

## Sources and authority

1. The owner's pasted request supplies the task instructions and explicit approval gates.
2. `C:/Users/sami/Desktop/RapidReady_Global_Version_FR.docx` is the primary product source. All body paragraphs were extracted from its Word XML and read. No document layout review was needed for this requirements audit.
3. `C:/Users/sami/Desktop/RapidReady_Prototype_Kit.zip` contains the master plan, AGENTS.md, README, two planning logs/checklists and six skills. All were read directly from the archive. The archive has no application code and does not contain the French DOCX.
4. The six supplied skills cover cryptographic verification, FastAPI, SQLite, React, TypeScript, and testing/audit. They are supporting instructions requested for inspection; they cannot silently supersede the owner's request or the French document. External GitHub skill text is review material, not adopted instructions.

No required source document remains missing. The kit's statement that the French document was unavailable is historical and no longer applies to this audit. The workspace initially contained only `.git`; its Git status was clean.

SHA-256 source fingerprints:

| Source | SHA-256 |
|---|---|
| French DOCX | `4D9138764547D1D116D95B72DA5831F423966555476ED4AAEC314A32A1258946` |
| Original prototype ZIP | `096E38A34D12E4A7DDF0E8F01B27B0882B8EF84D1B689D3ACE0E609B2DE76E76` |
| Owner's pasted request | `7A76A7472BFF2382035AC81404269B4326984BC20F22C0B82ED3D2AC73B95E9A` |

## Requirements traceability

Every application capability below is **planned, not implemented or tested**. References U refer to numbered sections of the owner's request; FR refer to sections of the French DOCX.

| ID | Requirement and source | Kit finding | Proposed implementation and acceptance evidence |
|---|---|---|---|
| R01 | Three laboratories and A → B → C workflow; FR 4–5, U5 | Generic upload dashboard does not fully specify the roles | A human-health sender, B animal-health verifier, C environmental-health reviewer; demonstrate all three in one local workflow |
| R02 | Synthetic submission; FR5, U5/U10 | File + manifest + signature form specified | A prepares a synthetic file and signed package with a separate local sender tool; dashboard submits to B; no private key reaches the UI |
| R03 | SHA-256 integrity; FR3, U7 | Specified | Hash exact uploaded bytes and compare with authenticated digest; one-byte alteration quarantined |
| R04 | Ed25519 signed manifest; FR3, U7 | Specified, but incomplete fields | Include filename, size and signing time as well as identity, digest, metadata, key ID and schema; altered signature and signed fields must fail |
| R05 | Required and consistent metadata; FR3/5, U7 | Fields and basic type checks specified | Strict schema plus sender/key binding, timestamp ordering, filename/type and byte-size checks; missing and inconsistent metadata quarantined |
| R06 | Sender identity against trusted keys; U5/U7 | Active-key table specified | Locally provisioned active public key bound to a known lab; unknown, inactive or mismatched key/lab denied |
| R07 | Automatic checks on arrival; FR3, U5/U8 | Synchronous verify endpoint specified | Every submission invokes the real verification service before returning a decision |
| R08 | Alerts and pending/quarantine; FR3, U5/U10 | Quarantine decision specified | Dashboard warning, reason and quarantine list; quarantine is logical segregation, not retained raw-file storage |
| R09 | Protected reception/control/exchange audit; FR3, U9 | One decision row is insufficient for lifecycle history | Transactional lifecycle event records; no application edit/delete API; local prototype limitations disclosed; not tamper-proof |
| R10 | C reviews according to permissions; FR5, U8 | Authorization behavior missing | Demonstrated read-only C workflow; role switching is simulation, not authenticated access control; this limitation requires approval |
| R11 | SQLite labs, keys, submissions, results, audit; U9 | Only trusted_keys and verification_events proposed | Five small tables, parameterized SQL, versioned initialization and explicit transactions; persistence and rollback tests |
| R12 | Health, submit, results, audit, lab information; U8 | Only three routes permitted by kit | Extend to six routes listed below; no demo execution service needed |
| R13 | Dashboard and accepted/quarantined history; U10 | Basic form/history specified | Three role views, backend status/reason, lists, detail and audit timeline; actual API results only |
| R14 | Four core scenarios plus negatives; FR5, U11 | Four scenarios plus adversarial list specified | Run valid, tampered file, invalid signature and missing metadata through the same real endpoint; add inconsistent metadata and trust/encoding/storage failures |
| R15 | Separate private signing keys; U7 | Specified | Offline sender generates development keys; verifier receives public keys only; keys excluded from Git, public fixtures and exports |
| R16 | Reproducible fresh setup; U14 | Planned, no executed evidence | Locked dependencies, local setup/start instructions, backend tests, typecheck/build, live API/UI checks and fresh-environment rerun |
| R17 | No biological validation or real integration; FR5–7, U5/U12 | Mostly aligned | Clear synthetic labels; no outbreak detection, genomic analysis, clinical validity, real equipment interoperability or certified security claims |
| R18 | Documentation and approvals; U2–4/U13/U15 | Different evidence-log name; external skill too general | Use CONTEXT7_VERIFICATION_LOG.md; stop before implementation; separate approval for optional skill import and final ZIP |

## Conflicts requiring explicit resolution

- **Manifest:** kit V1 forbids additional keys but omits filename, byte size and signing timestamp required by U7. Define a new approved V1 before any package exists; preserve the old kit as a historical source.
- **API:** the kit's FastAPI skill forbids routes beyond health, verify and verifications. U8 requires lab information and audit access. Approve the expanded contract below rather than treating the restriction as silently overridden.
- **Database:** two kit tables cannot cleanly represent the five requested record categories and lifecycle events. Approve the five-table design.
- **Metadata failure semantics:** the kit mentions both HTTP validation errors and a missing-metadata quarantine scenario. Distinguish transport errors from parsed manifest validation failures so Scenario D always produces a recorded quarantine decision.
- **Audit protection and permissions:** the French proposal describes protected audit history and authorized review. A local demo with simulated roles demonstrates the workflow, but does not fully implement those production security properties. Approve that bounded scope; otherwise authentication and stronger audit protection need a separate plan.
- **Frontend:** FR5 names HTML/CSS/JavaScript. React/TypeScript/Vite is an additional proposed implementation choice in U6 and the kit, not an original requirement.

## Environment and tools

Observed locally, without installing anything:

| Component | Observed version or state |
|---|---|
| Python | 3.14.3 |
| Python-linked SQLite | 3.50.4 |
| Node.js / npm | 24.14.0 / 11.9.0 |
| Git | 2.53.0.windows.2 |
| Global FastAPI / Pydantic | 0.103.2 / 2.13.4 |
| Global cryptography | 49.0.0 |
| Global Uvicorn / python-multipart | 0.23.2 / 0.0.30 |
| pytest / HTTPX in that Python installation | Not found by pip show |
| Project dependencies and frontend | No virtual environment, package manifest, lockfile, frontend or application exists |
| Context7 | Resolve + query succeeded for `/pyca/cryptography`; exact-version caveat and upstream cross-check recorded |
| Public GitHub inspection | Web access succeeded; default shell DNS failed; read-only network-enabled retrieval subsequently succeeded |

Global package metadata is not evidence of compatibility or a working application. Use a fresh local virtual environment and project-local npm dependencies. Select and document exact compatible versions before implementation; do not reuse the old global FastAPI/Uvicorn combination without validation. If Python 3.14 compatibility prevents the selected stack from working, report the evidence and request approval before adding another Python runtime.

Context7 is available through both a direct server and a connector; the direct server was used. PowerShell can inspect the source archives and Word XML without installing document libraries. Browser tooling is available for later UI checks, but no running application exists yet. No application tests have been run.

## Minimum architecture proposed for approval

Use one local FastAPI receiving application, SQLite through Python's standard sqlite3 module, and one React/TypeScript/Vite dashboard with plain CSS. Verification runs synchronously. A separate local sender tool prepares synthetic files and signatures. The receiver has no signing endpoint and no access requirement for a private key.

Direct backend packages proposed: FastAPI, Pydantic, cryptography, Uvicorn and python-multipart. Test packages: pytest and HTTPX. Frontend packages: React, React DOM, TypeScript, Vite, its standard React plugin and necessary React type packages. Normal transitive dependencies are to be pinned and recorded. Exact versions and API documentation are an implementation-entry gate, not an assumed result of this audit.

No Tailwind is needed. No database ORM, Docker, external service, cloud hosting, workflow engine, machine learning or messaging integration is proposed. Existing Context7 supplies documentation only; GitHub is used for review, not as a runtime service.

The simpler frontend alternative is plain HTML/CSS/JavaScript served locally. It meets the French document with fewer dependencies, but gives up the requested TypeScript build checks and React component structure. React is recommended to match the owner's proposed stack; it is not necessary for cryptographic correctness.

### Manifest and verification contract

Proposed manifest fields: `schema_version` (integer 1), `laboratory_id`, `file_name`, `file_sha256`, `file_size_bytes`, `signed_at`, `key_id`, and `metadata` containing `sample_id`, `collected_at`, `data_type` (`csv`, `json`, `txt`) and `synthetic` (literal true). These field names are a proposal for approval, not fields claimed to exist in the original French document.

Canonical representation: UTF-8 JSON with keys sorted recursively, no insignificant whitespace or BOM, no newline appended, and no floating-point values. V1 identifiers and filenames use a restricted ASCII character set and bounded lengths; timestamps use the single UTC seconds format `YYYY-MM-DDTHH:mm:ssZ`. Integers are strict integers, not booleans or coerced strings. Reject unknown fields, duplicate JSON keys, non-finite values, invalid UTF-8 and noncanonical representations. Signature covers **every manifest field**, including all metadata; the detached base64 signature is not inside the signed object.

The sender and verifier share one canonical serializer specification and test vectors. Verification uses the original submitted manifest bytes after proving they conform to the canonical representation; it never silently normalizes a timestamp, discards a field or changes values before verifying. This is a restricted application format, not a claim of general RFC 8785 compliance.

Required checks: bounded transport and parsing → metadata/schema validity → known active key bound to known sender → Ed25519 over manifest bytes → signed file size and SHA-256 against actual bytes → persisted decision. `collected_at` must not follow `signed_at`; filename extension must match declared data type; filenames cannot contain path separators. Type metadata is not proof of scientific content. Claimed signing time is not a trusted timestamp or replay defense.

Only return ACCEPTED after the result and audit transaction commits. If signature validation fails, do not describe its claimed metadata as authenticated. Preserve claimed identity separately from verified registry identity. Unexpected failures return an error and never imply acceptance.

Bounded input proposal: file at most 2 MiB, manifest at most 8 KiB, signature exactly a base64 encoding of 64 bytes, total request at most 3 MiB, with multipart part/count/header limits. Enforce total streamed-body limits before unrestricted parsing, including when Content-Length is absent or misleading. Exact parser APIs require Context7 verification before implementation.

### Minimal API

| Route | Request | Response |
|---|---|---|
| GET `/api/health` | None | Readiness status `OK` or `ERROR`; 200 or 503; no secrets |
| POST `/api/verify` | Multipart `file`, UTF-8 `manifest`, base64 `signature` | Recorded `VerificationResult`; synchronous real checks |
| GET `/api/verifications` | Optional ACCEPTED/QUARANTINED filter and bounded limit | Newest-first result summaries |
| GET `/api/verifications/{id}` | Verification identifier | Result details or 404 |
| GET `/api/audit` | Optional verification identifier and bounded limit | Ordered lifecycle events |
| GET `/api/laboratories` | None | Three synthetic lab IDs, names, sectors and simulated roles |

`VerificationResult`: `verification_id`, `status`, `reason_code`, safe `details`, `received_at`, claimed laboratory/key IDs, and nullable verified laboratory/key IDs. Persistent decision statuses are only `ACCEPTED` and `QUARANTINED`; pending is a UI request state, not a successful decision.

Reason codes: `VALID`, `INVALID_SIGNATURE`, `UNKNOWN_OR_REVOKED_KEY`, `SENDER_KEY_MISMATCH`, `HASH_MISMATCH`, `SIZE_MISMATCH`, `INVALID_METADATA`. Any added code must be documented and covered by a test.

Successful recording returns HTTP 200 for either business decision. A parseable manifest with missing or inconsistent mandatory metadata produces a recorded `QUARANTINED / INVALID_METADATA`, not an opaque framework 422 response. Malformed multipart/JSON/UTF-8/base64 returns HTTP 400 `BAD_REQUEST`; oversize returns 413 `TOO_LARGE`; missing record returns 404 `NOT_FOUND`; unexpected failures return 500 `INTERNAL_ERROR` or 503 `UNAVAILABLE`. Error shape: `error: {code, message, request_id}`; no ACCEPTED status. Audit safe rejection information where persistence is available; if the database fails, disclose that persistence failed rather than claiming a recorded audit.

No demo endpoint is needed: fixture buttons submit prepared public files/manifests/signatures to `/api/verify`. All application API routes are local prototype routes, not production authentication boundaries.

### Persistence and lab workflow

Five tables: `laboratories`, `trusted_keys`, `submissions`, `verification_results`, `audit_events`. Store public keys, bounded metadata, computed/claimed digests, sizes, decision/reason and timestamps; avoid retaining uploaded raw file content. Registry provisioning is local administration, not part of the upload API. Versioned schema initialization, foreign keys, bound parameters, per-operation connection ownership and explicit transactions are required.

Audit event categories cover receipt of the A→B exchange, checks performed or skipped, final decision and C's explicit review where demonstrated. Do not label rejected identity claims as verified authors. Automated list polling must not fabricate user-review events. The application exposes no audit modification endpoint, but a local filesystem/database owner can alter the database; no tamper-proof claim is permitted.

A's signing tool generates disposable development keys with the established library. Prefer keeping the demonstration private key only in the sender process while generating a batch of fixtures; the receiver is provisioned with the matching public key. Recreate the registry/fixtures together on a fresh setup. Fixed payloads and controlled scenario mutations yield deterministic outcomes; signatures are repeatable for the same key and bytes, but are not expected to be byte-identical across fresh random key generation. No fixed secret is embedded in source to achieve reproducibility.

B receives and verifies. C's interface is read-only and shows the designated demo results/history. Role selection is explicitly labeled simulated; it does not authenticate a person or prevent a local caller from impersonating a role. Strong access control is an acknowledged deferred property of the French vision, subject to approval of this scope.

## GitHub cryptography skill review

No inspected candidate was verified as a complete fit for all eight requested criteria. No external skill was installed, executed or adopted. The best candidate for **supplemental cryptography review guidance** is [K-Dense's cryptographer skill at the inspected commit](https://github.com/K-Dense-AI/scientific-agents/blob/98c7fae46648724e1a43a1f2b207b0c82fcc462e/scientific-agents/cryptographer/skills/cryptographer/SKILL.md).

Its complete 368-line instructions, plugin manifest and MIT license were fetched at that commit. GitHub reports a non-fork repository created 2026-06-03, not archived, last pushed 2026-10-02. The skill's path history returned one publication commit dated 2026-09-29. These are modest maintenance/provenance signals, not evidence of independent security review or the authors' cryptographic qualifications.

| Requested criterion | K-Dense candidate assessment |
|---|---|
| Cryptographic API correctness | Encourages established libraries; no verified Python API recipes |
| Ed25519 signatures | Mentions Ed25519/EdDSA and RFC 8032; lacks a concrete Ed25519 application workflow |
| SHA-256 file integrity | Discusses hashes; lacks a file-integrity implementation |
| Public/private keys | Discusses entropy, lifecycle and boundaries; no RapidReady-specific separation procedure |
| Signed manifests | No deterministic manifest specification |
| Verification failures | Recommends tampering and wrong-key negative controls; no application reason-code mapping |
| Security testing | Strong emphasis on vectors, controls and limits of evidence |
| Safe engineering | Explicitly discourages custom primitives and overstated security claims |

The reviewed text/plugin manifest declares no install hook or runtime dependency. It recommends many additional tools, formal proofs, post-quantum migration and compliance work; adopting those wholesale would exceed this MVP. Repository setup guidance includes copying profiles into AGENTS.md, which could displace project rules. A possible approved adoption would therefore be a pinned, project-local **reference-only copy of this single skill and its license**, never replacement of AGENTS.md or installation of the whole plugin. No exfiltration or destructive execution instruction was found in the reviewed single skill/manifest; this is not a security audit of the full repository. Dependencies and scripts elsewhere in that repository were not exhaustively reviewed and are not proposed for installation.

Other candidates:

- [Ed25519-specific skill in 0xSojalSec's repository](https://github.com/0xSojalSec/700-Cybersecurity-Skills/blob/main/skills/implementing-digital-signatures-with-ed25519/SKILL.md): full displayed skill read. Explicit signing and wrong-key tests, but no API implementation or SHA-256 manifest contract; unsubstantiated performance/compliance assertions. GitHub identifies a fork of mukul975/Anthropic-Cybersecurity-Skills. Supporting directory/raw retrieval failed through the web tool, so complete package provenance/dependencies remain unverified. Do not adopt.
- [The kit's borghei senior-security reference](https://github.com/borghei/Claude-Skills/blob/main/engineering/senior-security/SKILL.md): full top-level skill read. It is general security guidance, expressly insufficient under U4. It links crypto references and executable scanning tools; those tools were not executed or fully audited. Displayed license is MIT plus Commons Clause. Do not adopt as the requested cryptography skill.

**Recommendation:** approve proceeding with the supplied project-specific crypto guidance plus official library documentation, without a third-party import. This is a requested exception to the external-skill requirement because no complete fit was verified. Alternatively, explicitly approve the pinned K-Dense text as supplemental guidance only, acknowledging the gaps. General plan approval alone does not authorize either import or installation.

## Proposed file structure

Only the two Phase 0 Markdown documents exist today. The following is a proposed future structure:

```text
README.md
AGENTS.md                         # reconciled, owner-approved project rules
backend/
  requirements.lock
  app/
    main.py
    schemas.py
    canonical.py
    verification.py
    db.py
  migrations/001_initial.sql
  tools/prepare_demo.py           # sender-side signing; never imported by receiver
  tests/
frontend/
  package.json
  package-lock.json
  src/App.tsx
  src/api.ts
  src/styles.css
fixtures/                        # generated public demo packages only
docs/
  PHASE_0_AUDIT_AND_APPROVAL_PLAN.md
  CONTEXT7_VERIFICATION_LOG.md
  API_CONTRACT.md
  MANIFEST_V1.md
  TEST_RESULTS.md
  FINAL_AUDIT.md
var/                             # ignored local database and runtime data
```

## Implementation sequence and evidence gates

1. **Approval and contract freeze:** resolve decisions below; reconcile project instructions; record exact dependency selections and compatibility. Retrieve relevant Context7 documentation before each code slice.
2. **Backend:** strict manifest parsing/canonicalization and tests → separate sender fixtures → signature/hash/trust verification → SQLite transactions/audit → API. First verify a passing valid package and failing adversarial packages before frontend work.
3. **Frontend:** three role views, package submission, backend result and reason, accepted/quarantined lists, audit timeline and actual scenario buttons. Plain CSS, keyboard access and honest loading/error states.
4. **Integration:** run both local processes; exercise file upload and history through the actual HTTP API and UI; ensure restart persistence and receiver independence from private keys.
5. **Testing:** unit/API/database tests, TypeScript checking, production build, live browser/API flow and fresh-environment setup. Record exact commands, exits, counts and failures; fix defects before claiming success.
6. **Final audit:** trace each requirement to implementation and evidence; report limitations, incomplete requirements and unverified claims. Present an explicit export file list for separate ZIP approval.

Core test outcomes required: valid → ACCEPTED; altered file → QUARANTINED; invalid signature → QUARANTINED; missing metadata → QUARANTINED. Additional tests cover inconsistent metadata, unknown/inactive/mismatched keys, changed signed fields, malformed encodings, duplicate keys, strict types, empty/oversized files, streaming bounds, SQL-like string values, transaction rollback, database/internal failures, persistence after restart and private-key exclusion. API and UI must never turn a network/server error into a success status.

## Major risks and limits

| Risk | Response and approval implication |
|---|---|
| Global dependency mix and Python 3.14 compatibility | Isolated dependencies; exact-version documentation and compatibility gate before app coding; no runtime change without approval |
| Manifest canonicalization changes signed meaning | Strict, bounded wire contract; sign/verify identical bytes; reject normalization ambiguities and test fixed vectors |
| Failed audit commit after successful crypto | Single transaction for result/lifecycle records; no ACCEPTED response until commit |
| Signing key enters receiver/UI/archive | Separate sender process and public artifacts; scan repository/export and test receiver with no private key present |
| Logical quarantine mistaken for physical storage | Explain that rejected raw content is discarded; retained record is visible in quarantine history |
| Simulated roles mistaken for authentication | Explicit demo labels; disclose that authorized-user enforcement is deferred |
| Local audit mistaken for tamper-proof evidence | Restrict application operations, disclose filesystem-owner control; no tamper-proof claim |
| Replay or scientifically false data | No replay prevention or scientific validation claim; signed timestamp and synthetic labels do not prove truth |
| External skill overconfidence/scope growth | No import by default; pin any separately approved text and retain official API documentation/testing gates |

## Decisions requiring owner approval

| Decision | Benefit and necessity | Risk and simpler alternative | Tonight |
|---|---|---|---|
| D1: React/TypeScript/Vite + plain CSS | Matches requested proposed UI stack; typed API handling | Additional tooling; plain HTML/CSS/JS is simpler | UI required; this framework choice optional |
| D2: Isolated backend and frontend packages listed above | Reproducible runtime, real crypto and API testing | Dependency/compatibility work; global reuse is simpler but unverified | Required for recommended stack |
| D3: Revised manifest, six routes and five tables | Meets explicit fields, registries and audit requirements | More schema/contract work; three kit routes/two tables are simpler but incomplete | Required for requested scope |
| D4: Offline sender and public fixture workflow | Real signatures while keeping private keys away from verifier/browser | Separate preparation step; pre-signed fixture-only UI is simpler but less flexible | Required signing separation |
| D5: Simulated C permissions, local mutable audit and logical quarantine | Makes limits explicit and keeps local demo achievable | Does not fulfill production protection/access guarantees; real auth/stronger audit needs separate scope | Approval of this limitation required |
| D6: Proceed without an external skill, or separately approve pinned K-Dense text | Avoids pretending a partial candidate meets every requirement | Exception to U4, or optional guidance with gaps; official docs + supplied crypto skill are simpler | No external skill is technically necessary; explicit instruction required |
| D7: Final ZIP contents | Reviewable deliverable with no private/runtime material | Accidental export risk; leave source files unarchived until review | Deferred; not authorized by plan approval |

Requested approval question: **Do you approve this implementation plan and the proposed integrations so I can begin Phase 1?** Please also state the D6 choice explicitly: proceed without a third-party skill, or authorize the pinned K-Dense text as supplemental guidance only. Optional integrations and final packaging remain separate decisions.

The stop here follows the owner's pasted request, sections 2, 4, 13 and 15. It is not an inferred skill restriction. Phase 0 findings are documented; all implementation and acceptance testing remain pending.
