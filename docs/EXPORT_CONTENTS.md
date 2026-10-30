# Approved local MVP ZIP contents

The owner approved these contents on 2026-10-27. Archive filename: `RapidReady_Verify_MVP.zip`. This archive captures the tested local MVP before the separately requested Vercel hosting adaptation.

Include:

- README.md, AGENTS.md, .gitignore and pytest.ini.
- backend/app Python source, backend/migrations SQL, backend/tools sender, backend/tests.
- backend/requirements.in and requirements.lock.
- frontend/src, index.html, package.json, package-lock.json, tsconfig.json, vite.config.js.
- docs: Phase 0 audit, Context7 log, manifest/API contracts, actual test results, final audit and this contents list.
- docs/browser-verification.png: screenshot of the synthetic manual-upload acceptance and seven passed checks.

Exclude:

- .git, virtual environments, node_modules, build output, caches and temporary/reproduction folders.
- var and all SQLite databases/audit history.
- generated fixture/public-demo directories; recreate them using the documented sender command so the public registry and signatures match.
- private keys, credentials, original personal attachments and unrelated source documents.

The original supplied ZIP and DOCX remain unchanged. The export is source plus reproducible setup instructions, not a preinstalled standalone binary. Hosted deployment changes and any new database integration require their own recorded evidence.
