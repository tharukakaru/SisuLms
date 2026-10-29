# SISU RUN 3 release review

**Release candidate for staging and production acceptance — not production accepted.** Continued from the completed RUN 2 working copy; RUN 1/RUN 2 archives are unchanged. The ZIP contains the active `institute_lms` custom app and deployable portal assets, not the Frappe/LMS distributions or unrelated old archives.

## Actual verification

| Check | Result |
|---|---|
| Complete Python unittest suite | **PASSED — 245 tests**, exit 0; 15 new RUN 3 tests |
| Complete frontend Node suite | **PASSED — 67 tests**, exit 0; 14 new RUN 3 tests |
| Vue production build | **PASSED**, Vite native config loader; entry-copy script passed |
| Static syntax/schema | **PASSED — 228 Python files, 71 JSON documents** before generated review manifest |
| Undefined names (Ruff F821/F822) | **PASSED**, not a full style-lint claim |
| Python dependency consistency | **PASSED**, pip check: no broken requirements |
| Frontend installed dependencies | **PASSED**, npm.cmd ls --depth=0; matches unchanged package versions |
| Real Frappe/MariaDB/Redis, install/upgrade/migrations | **ENVIRONMENT UNAVAILABLE / REQUIRES STAGING** |
| Real browser/mobile E2E, responsive/accessibility acceptance | **NOT RUN / REQUIRES STAGING** |
| Payments.lk/OpenAI/other provider acceptance | **NOT RUN / REQUIRES STAGING** |
| GitHub workflow execution / production rollout | **NOT RUN** |

No failing final local check remains. The Windows PowerShell npm.ps1 wrapper was execution-policy blocked during one dependency-check invocation; calling npm.cmd succeeded without changing policy. An initial build invocation used the wrong working directory; the corrected frontend build passed. Neither issue is a claim of application E2E testing. No fresh advisory-network scan was performed in RUN 3; RUN 2 scans are historical. CI includes advisory scans, and staging must scan the actual full deployment stack.

## Files added/modified

41 added and 18 modified packaged files relative to RUN 2, including rebuilt assets, plus this generated review and change manifest. Old hashed portal assets are replaced by the current Vite build. The old generated RUN 2 manifest is superseded; historical handoff docs remain.

Source, schema, configuration and documentation changes:

- ADDED: `.github/workflows/release-checks.yml`
- ADDED: `docs/API_METHOD_INDEX.json`
- ADDED: `docs/DEPLOYMENT_RUNBOOK.md`
- ADDED: `docs/MOBILE_API_HANDOFF.md`
- ADDED: `docs/PROVIDER_ACCEPTANCE.md`
- ADDED: `docs/RUN_3_IMPLEMENTATION.md`
- ADDED: `docs/SITE_CONFIG_TEMPLATE.json`
- MODIFIED: `frontend/src/App.vue`
- MODIFIED: `frontend/src/ContactSettings.vue`
- MODIFIED: `frontend/src/materials/client.js`
- MODIFIED: `frontend/src/materials/MaterialUpload.vue`
- ADDED: `frontend/src/native/AIWorkspace.vue`
- MODIFIED: `frontend/src/native/client.js`
- ADDED: `frontend/src/native/contracts.js`
- ADDED: `frontend/src/native/ControlPlane.vue`
- MODIFIED: `frontend/src/native/MobileVerification.vue`
- ADDED: `frontend/src/native/NotificationCenter.vue`
- MODIFIED: `frontend/src/native/Papers.vue`
- MODIFIED: `frontend/src/native/PortalRoot.vue`
- ADDED: `frontend/src/native/release.css`
- ADDED: `frontend/src/native/Subscription.vue`
- MODIFIED: `frontend/src/service.js`
- ADDED: `frontend/tests/release.test.mjs`
- ADDED: `institute_lms/health.py`
- MODIFIED: `institute_lms/hooks.py`
- MODIFIED: `institute_lms/institute_lms/doctype/il_price_assignment/il_price_assignment.json`
- MODIFIED: `institute_lms/portal_session.py`
- ADDED: `institute_lms/release.py`
- MODIFIED: `institute_lms/saas.py`
- MODIFIED: `institute_lms/setup.py`
- MODIFIED: `institute_lms/subscription_payments.py`
- MODIFIED: `institute_lms/www/campus.html`
- MODIFIED: `README.md`
- ADDED: `scripts/verify-static.py`
- ADDED: `tests/test_run3_release.py`

A complete per-file SHA-256 inventory, removed asset paths and real verification metadata are in `docs/RUN_3_CHANGE_MANIFEST.json` (excluding its own recursive hash). No node_modules, virtual environment, cache, live site config, private key files or unrelated ZIPs are packaged. Secret-marker scans are a sanity check, not a comprehensive security certification. Nonfunctional unit-test fixtures remain for reproducible tests; no usable credentials were created.

## Required handoff documents

- `docs/MOBILE_API_HANDOFF.md` and `docs/API_METHOD_INDEX.json`
- `docs/DEPLOYMENT_RUNBOOK.md` — exact ordered production checklist and rollback gates
- `docs/SITE_CONFIG_TEMPLATE.json` — placeholders/categories only
- `docs/PROVIDER_ACCEPTANCE.md` — every live provider remains unaccepted

The following implementation review covers each role, plans/payments, notifications, AI/RAG, backend fixes, schema, CI, credentials/infrastructure and known blockers. Completion means source is prepared for staging review; it does not assert live infrastructure correctness.

---

# RUN 3 implementation and acceptance boundary

This release candidate continues RUN 2. RUN 1/RUN 2 source copies and ZIPs remain untouched. It preserves Vue/Vite, Frappe/LMS, MariaDB/Redis and separate organization sites. No deployment, DNS change, live provider transaction or production migration was performed.

## Frontend and role status

| Area | Implemented or retained production behavior |
|---|---|
| Platform Owner | Dedicated control-plane route, paginated organization registry, identity/host/contact/status, registration, suspension/reactivation, bounded trials, subscription state/grace, plan price/features/limits, tenant-scoped CUSTOM contracts and audited overrides, provisioning spec/status/next operator action, local registry counts and protected readiness |
| Institute Admin | Existing tenant-local teacher/student, programme, classroom, sessions/materials/announcements, attendance/papers/marking, branding and profile flows retained; direct member/learning navigation added. New plan/usage/storage, notifications, knowledge management and eligible aggregate AI insights |
| Student | Existing real dashboard/classes/schedule/materials/invoices/papers/own results/profile retained; new AI conversations/study tools/search/recommendations, notifications and plan status. Demo-only results navigation redirects to actual Papers results; unsupported demo areas remain isolated |
| Teacher | Existing assigned/owned classes, teaching permissions, schedules/materials/papers/submissions/marking/attendance/wallet retained. AI plans/explanations/revision/questions/flashcards, indexing and draft assignment feedback added; no automatic grade or publish action |
| Plans | Server-resolved STARTER/PREMIUM AI/CUSTOM features/limits/status/dates, storage and AI allowance; detailed tenant usage remains admin-only. CUSTOM tenant policy is the effective signed configuration; override history remains on the control plane |
| Organization checkout | Separate authenticated control-plane billing contact route; server quote → explicit confirmation → validated Payments.lk host → returned page reads/polls server attempt. Only succeeded server state displays paid. No redirect activates a subscription |
| Student checkout | Existing Payments.lk class/invoice UI and verified-settlement backend retained; no merchant replacement |
| Notifications | New logical-event inbox, total unread count/badge, mark-read, paging, channel preferences preserving existing event overrides; configuration/entitlement gating and honest unavailable channels |
| Push | Reviewed deployment adapter boundary plus owned register/revoke UI. No vendor SDK, FCM credentials or working provider invented |
| Profile/OTP | SMS/WhatsApp channel selection, actual configured/verified state, challenge binding, expiry display, resend cooldown (including failed sends), visible attempt/provider errors. Existing email verification retained; implemented Google Calendar consent/connect/disconnect exposed, Outlook honestly unavailable |
| AI/RAG | Course selector, own paged conversations/messages, archive/deletion scheduling, grounded Q&A with consent/modes, summaries/notes/cards/practice/search, verified sources with protected material links, deterministic recommendations and aggregate insights, usage/error states |
| Knowledge | Authorized material/session selection or existing native lesson ID, ingestion/reindex, explicit readiness/failure/unsupported state, deactivation and confirmed reset. No provider IDs displayed |
| Storage/retention | Server usage/remaining bytes and material preflight warning; exact server upload errors preserved. Existing server quota/private-file control unchanged. Lifecycle/access reasons displayed; no purge button |
| Accessibility/layout | Touched forms use labels, semantic buttons, error/status regions, focus outlines, responsive grids and scrollable tables. Plain-text AI rendering avoids HTML execution. Real-browser keyboard/screen-reader/viewport testing remains required |

The existing native campus UI remains the primary learning/administration workspace; this run adds focused panels rather than a visual rewrite. Local preview still requires a development build, loopback host and explicit preview query. Production API failures do not fall back to synthetic records. Historical demo source/tests are preserved for isolated development; they are not evidence of production academic features.

## Backend fixes and schema

- `portal_session.current`: a control-plane billing user no longer enters tenant institute/onboarding lookup. Owner and billing routes use server-issued control-plane metadata, not frontend role selection.
- `release.py`: authenticated read contracts for tenant plan/storage, scoped billing/plans, owner registry/jobs, actual provider availability/OTP state, unread count and authorized ready learning sources. No cross-site SQL.
- `IL Price Assignment.tenant_id`: new standard Link field and index. `release.custom_price` binds a CUSTOM contract to one registry organization. Subscription CUSTOM quote lookup now uses this binding, preventing one billing contact's contracts from being conflated across organizations and avoiding a fictitious tenant institute on the control plane. Old unscoped contracts require explicit reassignment; existing quotes are unchanged.
- Papers UI now uses centralized `ai.quiz`, retains request IDs on retry and offers AI feedback separately from editable/saved grades.
- Notification preference saves retain per-event overrides; total unread count derives from delivered in-app events, not historical WhatsApp/email outbox rows.
- Source selection reuses actual AI membership/course/payment/lifecycle checks; new facade methods do not grant generic DocType access.
- `health.live` reveals only reachability. Owner-only readiness checks DB/cache/schema/site/HTTPS and scheduled-worker heartbeat, with provider **configuration booleans**, never values. Hook dispatch supplies heartbeat. Exact migrations/upstream compatibility still require staging evidence.
- SaaS request guard allows the explicitly authorized release/health facade so recovery/plan status can remain accessible. Each method retains its own identity/owner/course boundary.

No new Python/Node runtime dependencies. RUN 3 schema synchronization/index changes use normal Frappe migration hooks; no migrations were run here. Existing RUN 1/2 patches remain ordered in `patches.txt`.

## Release materials

- `MOBILE_API_HANDOFF.md`: canonical-host isolation, browser PKCE approval, seven-day `Authorization: Sisu` tokens, logout, Google policy, CSRF distinction, all requested API categories, payload/citation/error examples and source-derived method signatures.
- `API_METHOD_INDEX.json`: 133 whitelisted method signatures from the relevant modules; declarations are not authorization grants.
- `DEPLOYMENT_RUNBOOK.md`: Linux/Bench/runtime pinning, backup/files/encryption keys, staging migration, controlled rollout/restart/health checks, tenant onboarding, manifest delivery, DNS/TLS/proxy/CDN/email DNS and restore-based rollback.
- `SITE_CONFIG_TEMPLATE.json`: nonfunctional placeholders/categories only. OpenAI/Google/SMTP encrypted settings remain in existing Frappe configuration.
- `PROVIDER_ACCEPTANCE.md`: all provider statuses remain NOT TESTED; includes required acceptance evidence and SMS/push adapter contracts.
- `.github/workflows/release-checks.yml`: install, Python/JS tests, syntax/schema/undefined-name checks, dependency checks/audits, Vue build and artifact upload. No deployment or migration privileges. GitHub execution itself has not been tested here.

## Verification meaning

New RUN 3 coverage adds 15 backend mocked-framework tests and 14 frontend contract tests. It covers contact/owner scope, liveness/readiness privacy, provider absence, source authorization, organization-bound custom pricing, plan/state mapping, paid-versus-pending display, checkout host validation, citation sanitization, quotas, actionable errors, stable request identity, notification preference/read/revoke wiring and draft review boundaries.

The final review records actual complete-suite/build counts and exit codes. Tests include earlier development-preview tests, pure rules and mocked Frappe/provider tests. They do **not** run a real MariaDB transaction, Redis worker, Frappe migration, browser, Flutter client or provider checkout. Do not describe this as production accepted.

## Known limitations and release blockers

1. **Staging required:** install/upgrade on the chosen Frappe 17/LMS commits; real transaction/queue behavior; paid native LMS boundaries; browser/Flutter sessions/CSRF and role/tenant isolation. No upstream commit pins are invented.
2. **Operator infrastructure:** isolated sites/databases, Redis/workers/scheduler, host/proxy/TLS/DNS, SMTP DNS and monitored backups. Registry ready status is an operator assertion, not an infrastructure probe.
3. **Manifest delivery:** 24-hour policy leases need reliable operator-controlled issuance/delivery/renewal and suspension propagation. UI never pretends registry changes have already reached a tenant.
4. **Provider credentials/acceptance:** both separate Payments.lk merchants, OpenAI, approved WhatsApp templates, selected SMS/push adapters, Google/YouTube/Calendar and SMTP. All configuration-present flags are distinct from acceptance.
5. **RAG limits inherited from RUN 2:** supported text extraction only, bounded documents/context/results, no OCR, DOC/PPT conversion, hosted privacy review and student consent, 30-day inactive store expiry/reset, uncertain provider outcomes requiring reconciliation. No unlimited AI or invented provider costs.
6. **Browser push:** external reviewed adapter/service worker still required. UI fails explicitly when absent. Provider-neutral foundation is complete; actual push delivery is not.
7. **Bounded UI lists:** existing course pages load incrementally; AI course picker uses loaded authorized classes. Knowledge lists cap at 100, message pages at 50, billing organizations at 100 and recent attempts at 20. Admin AI usage renders up to 50 rows from the bounded backend response. No cross-site academic/usage aggregation is fabricated.
8. **Existing product boundaries:** generalized GPA/bulk results, cross-site learning aggregation, Outlook and unsupported assessment/video workflows are not made real by this release. Actual paper results/native authorized LMS links are used instead. Uploaded-video production scale needs a tested media adapter; default files remain Frappe.
9. **CUSTOM migration:** reassign unscoped legacy CUSTOM contracts per registry organization; do not infer ownership or silently reuse one customer's price across tenants.
10. **UX acceptance:** touched components compile and contract tests pass; device screenshots, keyboard/screen-reader behavior, payment return flows and real provider/indexing latency still require browser acceptance. Historical untranslated keys and existing untouched screens may need product polish after staging feedback.

## Production deployment checklist

Use the ordered, checkable gate in `DEPLOYMENT_RUNBOOK.md`: pin verified runtime/app revisions → demonstrate DB/files/config restore → pass staging migrations and concurrent/security/E2E tests → accept required providers → configure isolated sites/secrets/manifest delivery → verify DNS/TLS/proxy/cookies/email → backup → deploy dependencies/code → migrate per site → build → restart → health/smoke tests → monitored tenant cohort rollout. Stop at any failing gate; rollback may require matching database/files/config restoration and external-payment reconciliation. No automatic production deployment is included.
