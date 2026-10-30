# TadusIQ design

Approved direction: Linear-inspired verification workspace, 2026-10-30. Source: `.agents/skills/awesome-design-md/references/design-md/linear.app/DESIGN.md`; adapt to RapidReady's synthetic laboratory workflow and identity.

## TadusIQ identity and feedback — 2026-10-30

- Rename the local interface, browser title/description, footer and user instructions to TadusIQ. Preserve historical archive/deployment names, API identifiers and the existing appearance storage key. Published to the existing Cloudflare Worker after the owner requested deployment.
- Four editable SVG directions are in `frontend/public/brand`: Signal T, IQ monogram, Connected labs, Guarded T. Each has a standalone mark and a system-font wordmark. Compare them at `/brand/index.html`; Signal T is the current app/favicon. Original vectors, transparent backgrounds, no asset service or extra dependency.
- Center the synthetic upload area's header, filename, helper text, chooser and error text, with balanced padding. Keep other attachment controls and exact signed text behavior unchanged.
- Dismissible error notifications supplement inline field/recovery guidance. They announce errors, support Escape/44px dismiss controls, keep focus with the form when appearing and return focus on dismissal when the originating control is visible. No automatic timeout/retry. Duplicate notices are replaced; at most three are displayed. Recorded quarantines use a warning, never an operational-failure acceptance. Theme tokens apply to both themes; no extra entrance animation.
- `/demo-kit/index.html` provides six signed synthetic example folders and expected outcomes. Three valid TXT/CSV/JSON examples and three deliberate rejection examples demonstrate the existing receiver semantics. Each folder contains exactly three upload files. The separate sender retains private keys only in memory and registers its public key in the local receiver. Other receiver registries require independent setup. Public-key metadata stays outside uploaded packages; imports never establish trust.

- Dark graphite canvas `#101114`, sidebar `#151619`, raised surface `#191a1f`, hover `#22232a`, borders `#303139`.
- Text `#f1f1f4`, secondary `#a5a6b2`; lavender `#b5afff` for selected navigation; primary fill `#6558c9` with white text. Keyboard focus uses a dedicated neutral 2px outline: dark `#b7b9c4`, light `#555966`, including file pickers. Status colors have text labels and never carry the decision alone.
- System sans stack, 16px body, 14px controls and metadata, 30px page heading with restrained negative tracking; system monospace for exact package contents and identifiers. No external/proprietary fonts.
- 4/8px spacing rhythm, 6–8px radii, hairline borders, no decorative gradients, glows, oversized hero, or pre-heading eyebrows.
- Narrow persistent desktop navigation, compact simulated-role switcher, slim connection/refresh header. Verification uses an upload/demo view switch and adjacent result inspector. History uses loaded-record search, counted decision filters, and an adjacent inspector. Audit uses an event timeline and explicit selected-record scope.
- Keep upload DOM mounted while navigating to retain file inputs and controlled draft contents. Display selected filenames and field errors. Manual manifest/signature entry remains available. Preserve exact signed text; never trim or rewrite it.
- Backend-confirmed decisions only; loading has no simulated check progress. Unknown network outcomes remain explicit. Preserve previous records on refresh errors with a stale-data notice. Role simulation, synthetic-only scope, logical quarantine and non-tamper-proof audit remain visible.
- Below 1100px stack inspector under content; at 760px use compact horizontal navigation and a single-column form. Touch controls at least 44px, visible keyboard focus, reduced-motion support, and no page-level horizontal overflow. Inspection never steals keyboard focus; result announcements use a dedicated polite live region.

Implementation stays in existing React/TypeScript and plain CSS. The approved theme-switch addition uses only the pinned direct dependency `@radix-ui/react-switch` 1.4.1. Reference documents are guidance, not permission to change verification semantics or add infrastructure.

## Package workflow additions — 2026-10-30

- Bulk file selection is a shortcut above the existing inputs, with an inline review of three distinct file assignments. Known names are suggested only when unique. Selected file options are numbered to distinguish duplicate names. Use or cancel the selection before submitting the current draft; neither selection nor confirmation submits a package automatically.
- Bulk replacement is atomic after size/encoding checks. Failed replacement and Cancel retain the previous draft. Exact decoded UTF-8 contents retain BOM and whitespace; the receiver remains responsible for canonical representation and signature checks.
- Readiness uses Missing, Reading, Loaded and Needs attention, with inline errors and a polite summary. Ready to submit indicates attachment readiness only. Preserve the explicit receiver-verification explanation.
- Result guidance is a functional Suggested next step section within the inspector. It explains how to recover from each recorded reason without editing signed contents or changing the trust registry.
- Selected audits load directly by verification ID with up to 200 newest-first events, independent loading/error/retry states, cancellation and response-scope checks. The recent overview remains the latest 100. A 200-event response displays a possible-truncation notice.
- Appearance uses a labeled Dark mode switch in the top bar; checked means dark. Dark is the initial default. Store only `rapidready-appearance`; bootstrap from the head before app/CSS rendering. Blocked storage leaves the current-visit theme usable and announces the persistence limitation.
- Light tokens: canvas `#f8f9fb`, surface `#ffffff`, text `#1c1d22`, secondary `#5d616d`, borders `#d9dce3`, primary `#6558c9`. All component colors use semantic tokens shared by the themes. Theme colors commit together; supported browsers crossfade snapshots of workspace/sidebar rather than interpolating text/background colors.

## Switch and motion — 2026-10-30

Toolbar/sidebar polish: group the sun/switch/moon cues with a consistent label gap and a quiet desktop separator. Use a bordered Refresh button with icon and visible text. At phone widths, place workspace/status on one row and theme/refresh on the next. Keep the native role selector with 38px trailing padding and a chevron inset 16px; forced colors restores the native arrow. Replace the A/B/C avatar circles with an original three-part line logo for the adjacent One Health collaboration text.

- The local `frontend/src/components/ui/switch.tsx` adapts the official shadcn/ui Radix Switch Root/Thumb source to existing CSS tokens. Attribution and full MIT notices are in `frontend/THIRD_PARTY_NOTICES.md`. No Tailwind, style reset, hosted fonts or icon dependency.
- Dark mode has decorative sun/moon cues, native switch semantics and a 64×44px target. Space/Enter and pointer input retain focus. The thumb moves over 180ms ease-out.
- Native View Transitions crossfade workspace/sidebar over 200ms; the toolbar remains live so rapid input can supersede an animation. Skip obsolete transitions and guard delayed callbacks with a generation counter. Unsupported browsers, reduced motion and startup failure apply the theme immediately. Verification requests never wait for an animation.
- Newly mounted result inspectors and audit panels fade in over 180ms with at most 4px vertical movement. No audit-row, layout-size or verification-progress animation. Interactive control borders respond over 140ms. Reduced motion disables these effects.
