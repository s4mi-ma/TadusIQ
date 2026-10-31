# TadusIQ project instructions

The owner approved continuing the Phase 0 recommended plan on 2026-10-26 and approved Cloudflare Workers + D1 hosting adaptation and free-plan compatibility testing on 2026-10-27. Use `docs/PHASE_0_AUDIT_AND_APPROVAL_PLAN.md` and the original French DOCX as recorded there. The local MVP archive contents were approved and packaged separately. Preserve that archive. On 2026-10-30, the owner explicitly requested importing https://github.com/VoltAgent/awesome-design-md for this project's redesign. That design reference collection is approved for import as the project-local `awesome-design-md` skill; no other third-party skill is adopted by this approval.

- Before implementation changes, consult Context7 for the relevant library/API and record versions, sources, limitations and decisions in `docs/CONTEXT7_VERIFICATION_LOG.md`. Stop the affected code if documentation is unavailable.
- Use established Ed25519 and SHA-256 implementations. Sign every manifest field, enforce the documented canonical bytes, and reject unknown/inactive/mismatched keys and invalid metadata.
- Private keys belong only to the separate local sender; never expose them to the receiver, UI, source control, logs or exports.
- Use parameterized SQLite statements, explicit transactions, and commit results/audit before reporting acceptance. An operational failure must never become ACCEPTED.
- Implement the six approved API routes and five-table schema. The kit's earlier three-route/two-table restriction has been reconciled in the approved plan.
- All lab roles, data and fixtures are synthetic. Roles are a simulation, quarantine is logical, and the local audit is not tamper-proof. Do not claim production authentication or biological validation.
- Work in small tested slices; record actual tests and failures. No fabricated evidence. Do not add optional integrations, frameworks or infrastructure.
- Keep the original ZIP and DOCX unchanged. Do not create a final ZIP before contents approval.

## Project design skill

For website redesign work, read `.agents/skills/awesome-design-md/SKILL.md` and select a relevant imported design reference. This project-local skill adapts the owner-approved VoltAgent collection; its visual guidance does not override the functional, security, documentation, and archive requirements above.
