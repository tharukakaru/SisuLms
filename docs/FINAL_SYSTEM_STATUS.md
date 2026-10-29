> Historical pre-V2 document. Current source/status/test results: SISU_FINAL_VERIFICATION_AND_COMPLETION_REPORT.md and SISU_FINAL_COMPLETION_MATRIX.md.

# Final system status and acceptance boundaries

Verified 2 October 2026 against actual RUN 3 source and the new isolated preview. This is a documented, preview-capable release candidate. **It is not a claim of production readiness or live provider acceptance.**

## IMPLEMENTED

| Area | Source-backed state |
|---|---|
| Core LMS | Existing Frappe/Vue classes, ownership, enrollment/access, programmes, sessions/materials, attendance, announcements, papers/attempts/marking and protected content boundaries |
| SaaS | Separate control-plane registry and one-site/one-database tenants; plan/subscription resolver, audited overrides, signed policy, quota/usage and provisioning contracts |
| Payments | Existing student Payments.lk flow; separate organization quote/attempt/webhook/transaction settlement; redirect never grants access |
| Notifications/OTP | Logical event + per-channel outbox, inbox/read/preferences, device-token model; secure channel-separated OTP with shared issuance lock |
| AI/RAG | Existing SOUL provider reuse, Responses generation, hosted course retrieval, knowledge versions, owned conversations, drafts, citations, usage and retention |
| Web integration | Real native AIWorkspace, Subscription, NotificationCenter, MobileVerification and ControlPlane components, plus existing role screens |
| Release preparation | Existing CI/source checks/deployment/provider/mobile handoffs and safe health/readiness contracts |
| Local preview | Existing mechanism extended to RUN 1/2/3 UI contracts; isolated static entry, state selector, loopback launcher and browser-verified fictional workflows |

## CONFIGURATION REQUIRED

| Category | Actual configuration boundary |
|---|---|
| Platform/tenant | `il_control_plane`, owner provisioning, registry `il_tenant_id`, canonical `host_name`, `il_control_plane_url`, distinct per-tenant signing keys and scheduled manifest delivery |
| Commercial | Positive configured prices/contracts, plan feature and capacity limits, trial/grace procedures, billing-contact identities; seed zero is not free/unlimited |
| Frappe runtime | Compatible pinned Frappe/LMS/Python/Node/MariaDB/Redis, installed apps, migrations, workers/scheduler, HTTPS proxy and per-site encrypted backup |
| AI | Encrypted `IL SOUL Settings.api_key`, enabled model/moderation/retrieval review, feature credit/rate metadata, student safety/privacy flags, retention/daily limits |
| Messaging | Email Account, Meta templates/webhook settings, concrete `il_sms_adapter` and `il_push_adapter`; browser push registration adapter is still an integration boundary |
| Storage | Default `il_storage_backend=frappe`; tested write/private-read adapter and credentials before selecting external object storage |
| Mobile | HTTPS canonical host, `il_mobile_redirect_uris`, Flutter PKCE/deep-link/token integration and device push implementation |

Use `SITE_CONFIG_TEMPLATE.json` for exact applicable keys; its blank values intentionally do not connect services. SMS/push vendor secret names depend on the chosen implementation and are not invented here. Database/Redis configuration is Bench-managed, not a new frontend environment system.

## PROVIDER ACCEPTANCE REQUIRED

| Provider | Required real evidence; none performed here |
|---|---|
| Payments.lk student merchant | Hosted checkout, valid and invalid signatures, exact amount/currency/mode binding, duplicate/reordered callbacks, receipt and wallet settlement |
| Payments.lk subscription merchant | Immutable quote expiry/contract, repeat checkout, verified activation/renewal, no redirect activation, separate merchant, manifest delivery |
| OpenAI | Configured Responses model/schema/moderation, usage receipts, timeout reconciliation, multilingual quality, hosted file/vector filtering/citations, deletion and data-processing review |
| Email | SMTP connection/TLS, sender authentication/DNS, queue/worker delivery, verification/invitation and reminder receipt |
| WhatsApp | Approved authentication/notification templates, token/phone ID, delivery callbacks/HMAC, opt-in/guardian conditions and retries |
| SMS | Chosen real adapter, OTP send/expiry/cooldown, delivery reference and ambiguous send reconciliation |
| Google | Student OAuth redirect/session proof; YouTube OAuth persistence/broadcast permissions; Calendar callback/queue sync |
| Push | Real web/mobile provider adapter, token ownership/revocation, foreground/background delivery and invalid-device handling |
| External storage/media | Authenticated private reads, quotas, backup/deletion, object/video delivery and scalability if configured |

## STAGING TEST REQUIRED

The 245 Python tests use local pure/stubbed contracts; they are not live Frappe database/Redis concurrency tests. Browser preview checks exercise real Vue rendering with fixtures; they do not test server permission enforcement. Required staging work includes:

1. Pin compatible upstream versions, install Frappe/LMS/custom app and run post-model-sync `patches.run1` and `patches.run2` plus current DocType synchronization on a backup-restored staging site.
2. Prove site/database separation using two tenants; test canonical host/proxy behavior, unknown hosts and per-site manifest keys/revision/lease expiry.
3. Test all four real role accounts, Google student restrictions, inactive members, teacher assignment/Full-control restrictions, paid/free/school-mode classes and direct native LMS/file access.
4. Exercise concurrent enrollments/uploads/AI reservations, payment callback ordering, outbox jobs, OTP parallel issuance/verification and token revocation against actual MariaDB/Redis.
5. Complete every relevant provider acceptance row, verify source revocation/cleanup, small-cohort privacy and no private conversation exposure.
6. Test real web desktop/tablet/mobile flows, mobile devices/PKCE, accessibility, file formats and large realistic datasets. Validate all queue health rather than assuming one heartbeat proves every worker.
7. Test tenant backups, file/config/encryption-key restore and rollback; deploy tenant-by-tenant only after acceptance and explicit operational authorization.

## WEB ONLY / WEB FIRST

Control-plane organizations/plans/provisioning/readiness and organization billing are web-first. Official paper publishing and advanced administrative configuration remain in existing web workflows unless separately integrated. Some original demo components (Results/GPA, competitions, marketing/video demo routes) remain in source; `App.vue` redirects or excludes unsupported production routes rather than presenting their synthetic data as live features. Actual paper results exist; a complete independent GPA/transcript system is not established by those old components.

## MOBILE INTEGRATION PENDING

One shared backend contract exists. The separate Flutter parity update adds/extends mobile UI/models/adapters while preserving prior work. It is not changed by this task. Final PKCE adoption, live API mapping, course/file/citation navigation, payment-state polling, device-token registration and real device/provider acceptance belong to the mobile handoff. No APK/AAB or mobile build was produced by this documentation task.

## Tests actually executed for this task

| Check | Result |
|---|---|
| Locked frontend install (`npm ci`) | PASSED; 46 packages installed, existing dependency versions retained |
| Complete frontend tests (`npm test`) | PASSED: 75 tests, zero failed; includes 8 new preview-focused tests |
| Complete backend local suite (`python -m unittest discover -s tests`) | PASSED: 245 tests, zero failed; no live Frappe runtime |
| Static schema/Python validation (`scripts/verify-static.py`) | PASSED: 228 Python sources and 72 JSON documents at source-check time |
| Normal production build (Vite native config loader + copy-entry) | PASSED; unchanged normal production configuration |
| Isolated static preview build (`npm run build:preview`) | PASSED; separate preview-dist output |
| Preview launcher/server | PASSED: Start-Preview.ps1 -NoBrowser -Port 5186; loopback static serving |
| Browser role/page sweep | PASSED: 25 core role/page combinations; no JS errors or external requests |
| Browser state/extended navigation suite | PASSED: 56 scenario/navigation checks, including teacher feedback, private conversations, admin insights and all platform tabs; no JS errors/external requests |
| Notification interaction | PASSED: mark read changes 1 unread to 0 unread in local fixtures |
| AI output/citations | PASSED: explicitly labelled fictional response and source UI; no provider request |
| Responsive example | PASSED: student AI at 390px, document width 390px; screenshot captured; not an exhaustive device audit |
| Guard probes | PASSED: both local API and external OpenAI fetch rejected before network |
| Production exclusion/source comparison | PASSED: no distinctive new fixture/selector markers; backend, schema and production UI/build assets identical to original archive |
| Packaged artifact smoke test | PASSED: extracted ZIP launches without node_modules; Student dashboard opens; API path returns 404 |
| Document validation | PASSED: requested files exist, local document links resolve and code fences balance |
| Archive integrity | ZIP CRC check passed; original release SHA-256 unchanged; no original files removed |
| Live Frappe/MariaDB/Redis E2E, providers, mobile, DNS/deployment | NOT RUN / REQUIRES STAGING or provider/infrastructure access |

The first preview build attempt hit this environment's esbuild config-loader access restriction; the explicit native config loader fixed it. Browser inspection then found a blocked Google Fonts stylesheet preventing a dynamic CSS load; a preview-only build transform removes the external import. Both were rechecked successfully. A browser test selector was corrected to match the existing wrapped form labels; no production UI change was needed. These resolved setup/test issues are not hidden test passes.

## Changes and production impact

Modified original files: `Start-Preview.ps1`, `frontend/package.json`, and preview-only `academy.js`, `adapter.js`, `Login.vue`, `PreviewShell.vue`. Added preview entry/config/server/guard/scenario/fixtures, eight unit tests, documentation, static preview and screenshot evidence. Exact file differences are in `PREVIEW_CHANGE_MANIFEST.json`.

No backend Python, DocType, production authorization, native production Vue component, production API client, normal Vite config or default production entry changed. No migration, provider call, real payment/message, tenant provisioning, production DNS or deployment was performed. The original release ZIP was not overwritten. Runtime browser state is fictional and cannot authorize real operations.

## Known preview limitations

- Provider calls, genuine authentication, protected downloads/uploads, real checkout and provisioning are disabled. Some legacy settings/actions intentionally show connected-backend-required.
- Scenario values are view fixtures, not complete production validation or suspension routing. Plan save acknowledgments and policy overrides are illustrative, not a durable SaaS administrator simulation.
- Existing academy fixtures are retained; new release examples are deterministic. A fresh tab/private window clears legacy sessionStorage examples; Reset scenarios is not a full legacy data wipe.
- Offline preview uses system font fallback. Browser coverage is representative, not exhaustive cross-browser accessibility or production E2E acceptance.
- Snapshot prices/usage/statistics are fictional. Seeded production prices/limits still require configuration. Preview images are not evidence of live users or production state.

## Controlled release gate

Follow `DEPLOYMENT_RUNBOOK.md`: verified backups → staged migration → pinned code/dependencies → tenant migration/build → restart web/workers → authenticated readiness and role smoke tests → provider/cross-tenant acceptance → controlled rollout/monitoring. Maintain current signed tenant leases. Do not treat code rollback as automatic database rollback; restore matching database/files/config and reconcile external transactions/resources when necessary. No deployment is authorized or executed by this task.
