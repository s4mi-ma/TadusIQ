# Vercel hosting assessment — 2026-10-27

## Owner's alternative: Heroku

The owner offered Heroku using an existing student plan. Heroku CLI is not installed and no Heroku connector is available in this session. Official documentation confirms Heroku dyno filesystems are also ephemeral, so moving hosting alone does not remove the persistent-database requirement. Recommended revised path: serve the built React frontend and FastAPI from one Heroku app, with Heroku Postgres for hosted persistence and a pinned Python PostgreSQL driver. Preserve local SQLite development. No Heroku resource or dependency has been installed/provisioned yet.

The official student offer currently describes $13/month credits for 24 months, usable for first-party dynos and Postgres. Actual remaining credits and existing account usage have not been checked. Source: https://www.heroku.com/github-students/ . Ephemeral storage: https://devcenter.heroku.com/articles/preparing-a-codebase-for-heroku-deployment . This alternative avoids a separate Neon account and can use the owner's existing credits. Database/driver and resource spending approval remains necessary under the original request.

Owner approved packaging the local MVP and requested Vercel hosting. Account inspection confirmed the connected team `samihakim779s-projects` (`team_2mzxhoVRHzOKpeJLQFb9RkE7`). No RapidReady project was found. No hosted deployment or storage resource has been created yet.

## Required decision

Vercel Functions expose a read-only filesystem plus temporary `/tmp` scratch space. A local SQLite file there cannot satisfy the approved durable result/audit requirement across function instances and restarts. Do not deploy the receiver with temporary SQLite and present its history as persistent.

Recommended hosted adaptation, pending the owner's explicit database/dependency approval:

1. Keep the tested SQLite path for local execution. Add a PostgreSQL persistence adapter for the hosted receiver, using Neon and a pinned Python driver, without introducing an ORM.
2. Preserve the five logical tables, trusted-key binding, parameterized queries and atomic verification/audit transaction. Use a hosted schema migration, suitable row locking and error handling; test the actual PostgreSQL path before release.
3. Deploy Vite and FastAPI together in one new `rapidready-verify` project in the connected team. Vercel Services is currently beta. Route `/api/*` to the Python backend and other requests to the frontend, preserving the existing public API prefix.
4. Configure an explicit hosted Host/Origin allowlist; the current local-only guard would reject hosted requests. Store database credentials only in server-side Vercel environment variables.
5. Prepare synthetic public packages in a separate sender process, register only its public key in the hosted database, and upload no local audit database or private key. No existing local history migration is proposed.
6. Stage the deployment, verify readiness and all four real scenarios plus persisted history/audit, then publish the verified deployment and report its URL. Check provider plan/terms before provisioning or accepting charges.

The database service and driver are significant additions. The original owner request explicitly requires approval for such changes, so an approval question was presented before implementation/provisioning. A simpler alternative is to keep SQLite on a separate backend host with durable disk, while serving the frontend on Vercel; that requires another hosting provider and cross-origin/backend configuration. A frontend-only deployment does not satisfy the requested complete application.

## Documentation consulted

Context7 resolved `Vercel` to `/websites/vercel` (high-reputation official documentation index), then retrieved targeted filesystem, storage and Services/FastAPI configuration docs. These are unversioned platform docs, not exact deployed-runtime evidence.

- https://vercel.com/docs/functions/runtimes — filesystem limitations
- https://vercel.com/docs/storage — external transactional databases through Marketplace
- https://vercel.com/docs/services — coordinated frontend/backend deployment and routing
- https://vercel.com/docs/frameworks/backend/fastapi — exported ASGI app entrypoint

Skills read: deployments-cicd, vercel-services, vercel-storage and marketplace. No third-party skill was installed. No package, CLI, cloud database or hosted app was installed/created during this assessment.

## Approved local archive

`RapidReady_Verify_MVP.zip`: 38 entries, 93,501 bytes. Each entry was decompressed and SHA-256 compared with its source file. Excluded-path checks passed. Archive SHA-256:

`A1CC8B2E3DBEE7562409599358BAC9E558BB3EA333FB159FC7685464BFDE09B9`

The archive captures the approved local MVP before hosting adaptation; this later assessment is not included in that archive.
