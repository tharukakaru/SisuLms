# SISU release candidate — staging and production runbook

This is source/build preparation, not evidence of a working deployment. No real DNS, infrastructure, migration, merchant checkout, OpenAI call or production rollout was performed. Unit tests run without the real Frappe database/queues. Complete this checklist on staging before enabling customer traffic.

## 1. Establish and pin the runtime

Use Linux and an operator-managed Frappe Bench with MariaDB, Redis/cache/queues, web workers, short/default/long job workers, scheduler and HTTPS reverse proxy. Keep one site/database per organization, plus a separate control-plane site. All share the same app code, not database records. The custom app declares Frappe >=17.0.0-dev,<18 and LMS >=2.0.0-dev; this is a compatibility requirement, **not a tested commit pin**.

On staging, choose the intended Frappe 17 and LMS branches from their official repositories, record exact Git SHAs, inspect their Python/Node/MariaDB/Redis requirements, and build a compatible Bench. The local source suite used Python 3.12 and Node 24; do not infer the upstream runtime supports those versions without the staging check. Record OS/runtime versions, `bench version`, installed apps, dependency lock/snapshots and the release archive SHA. Pin the verified Frappe/LMS/app commits in your infrastructure repository before production. Never deploy floating development branches unattended.

Install this custom app through Bench's supported app workflow, preserving its package name `institute_lms`. Install LMS before institute_lms. Review `bench --help` / site command help for the selected Bench version before executing examples below. No package or migration commands in this document were run against a real site.

## 2. Configure sites securely

Use `docs/SITE_CONFIG_TEMPLATE.json` as a category reference, not a ready-to-copy live config. Blank placeholders intentionally cannot authenticate or activate providers. Store real values in a protected secret manager/site configuration, not Git, frontend assets, shell history or CI logs. Preserve each site's Frappe encryption key in encrypted backups; it is needed to recover encrypted settings/tokens.

Control plane: configure the verified platform owner using the existing registration/setup flow, `il_control_plane=true`, canonical HTTPS `host_name`, subscription Payments.lk merchant settings, and a distinct strong signing key per tenant in `il_tenant_signing_keys`. Configure outgoing Email Account and owner authentication. Never grant Institute Admin the configured platform-owner identity.

Tenant: `il_control_plane=false`, its registry-issued `il_tenant_id`, matching canonical `host_name`, matching per-site `il_control_plane_key`, and `il_control_plane_url` pointing to the dedicated billing portal. Create exactly one IL Institute and its named admin through the provisioning flow. Apply a fresh signed manifest with features, limits, state and expiry. Manifests lease for 24 hours; operators must provide reliable renewal/delivery and alerting before commercial release. The application does not currently run an unattended cross-site delivery service.

OpenAI stays in encrypted IL SOUL Settings. Review enabled models/rates/credit units, safety opt-in and hosted retrieval privacy before enabling student AI. `store=false` on Responses does not imply that hosted vector files are zero-retention. Configure Google Social Login Key through Frappe, SMTP through Email Account, and adapter implementation/secrets only on the server. Verify installed write/read hooks before selecting external storage; Frappe is the default.

## 3. Backup and stage migrations

For each site, obtain a consistent database backup **and public/private file backups**, configuration/encryption-key backup, previous app/upstream Git SHAs and deployed assets. Example operator command: `bench --site <canonical-site> backup --with-files`. Store encrypted copies off-host; verify restoration into an isolated test site. Provider-hosted RAG files are not a substitute for source-file backups.

Restore representative existing data to staging with scrubbed credentials and blocked outbound providers. Run the selected stack's dependency installation and migrations there first. Check patch logs, field/index creation, existing institution cardinality, wallet/enrollment reconciliation warnings, active subscriptions, provider settings, private-file paths and queue failures. Do not silence duplicate-constraint failures or edit tables manually.

Migration order follows `patches.txt`: RUN 1 SaaS/payment/notification/storage/mobile schemas and indexes; RUN 2 AI/knowledge schemas and indexes. RUN 3 adds `IL Price Assignment.tenant_id` through standard DocType synchronization (no destructive data conversion). Existing CUSTOM contracts without tenant_id are not silently adopted: assign a tenant-scoped contract through the control plane before creating new CUSTOM quotes. Existing immutable quotes/payment records remain intact. No RUN 3 manual SQL table alteration or production migration is required outside normal Frappe sync.

## 4. Controlled code rollout

Execute under a change window on one staging site, then a small tenant cohort. Maintenance mode may be needed because app code is shared even when migration is per site. Drain/stop job execution as appropriate for the verified Bench/process-manager setup; do not allow old workers to run incompatible new schemas.

1. Confirm approval, provider acceptance, backup/restore evidence and release/runtime pins.
2. Record queued jobs and maintenance status; create fresh DB/file/config backups.
3. Deploy the verified Frappe/LMS/custom-app revisions on the shared Bench.
4. Install locked/reviewed Python and Node dependencies using the selected Bench workflow. Frontend: `cd apps/institute_lms/frontend`, `npm ci`, `npm test`, `npm run build`.
5. Run `bench --site <site> migrate` for the control plane and each selected tenant. Stop rollout on any error; never skip failing patches. First install uses `install-app lms`, then `install-app institute_lms` as applicable.
6. Run the normal Bench asset build if required by your pinned runtime, then restart web/workers using the configured systemd/supervisor/Bench service process. Ensure the scheduler is enabled (`bench --site <site> enable-scheduler` where supported).
7. Check public `GET /api/method/institute_lms.health.live`. Authenticated local owner calls `health.readiness`; it checks DB, cache, recent scheduled-worker heartbeat, schema presence, identity and HTTPS. It does not certify every queue, exact migration state, upstream version compatibility or provider acceptance. Inspect Bench migration logs, `list-apps`, queue/scheduler process health and provider status separately.
8. Deliver current signed subscription manifests, verify tenant `saas.status` availability and run role-specific smoke tests below.
9. Resume traffic/jobs, monitor errors/latency/queue age/lease expiry/quotas/payment reconciliation, then roll out the next tenant. Store evidence in the release record.

The CI workflow runs source tests/static checks/dependency audits/build and uploads portal assets. It has no deployment secrets, production permissions or migration stage. Dependency audits require network; failures require investigation. Adopt organization-approved action SHA pinning and upstream runtime pins before production.

## 5. Domains, proxy and media

`sisu.example` and `*.sisu.example` are examples only. A wildcard DNS record can route tenant hosts to the proxy; every hostname must still map to its intended Frappe site. Reject unknown Host headers rather than serving a default tenant. Keep the control-plane host explicit. Do not trust a browser-provided institute code, tenant header or URL parameter to select a database.

Use TLS for every host, redirect HTTP to HTTPS, renew certificates automatically, and test the actual forwarded host/protocol behavior. Trust forwarded headers only from your configured proxy, not arbitrary internet clients. Use Bench-generated Nginx/proxy configuration for the pinned version, then review host mapping, request size/timeouts, socket/realtime endpoints and private-file locations. Do not expose database/Redis ports or bench services publicly. Tune worker timeouts for the bounded long ingestion jobs.

CUSTOM custom-domain metadata does not create DNS or certificates. Verify customer domain ownership out-of-band; require entitlement; map to the same canonical tenant, install a valid certificate, and test cookie, OAuth redirect, mobile host and payment return behavior. Prefer redirecting aliases to one canonical host so sessions/tokens remain host-bound. Do not configure permissive cross-tenant CORS. Cookies must be host-only/secure with the appropriate SameSite policy verified against OAuth.

CDN may cache public hashed assets; never publicly cache private materials, authenticated API responses or AI conversations. Uploaded videos need a tested scalable media/object-storage adapter before high-volume rollout. YouTube remains URL/ID references; no video download. External storage must preserve Frappe file authorization, quota accounting, backups and signed-link lifetimes. Configure SMTP domain SPF/DKIM/DMARC through the chosen provider, and validate delivery; no DNS record was configured here.

## 6. Customer onboarding: application vs operator

| Step | Responsibility |
|---|---|
| Register organization/code/host/admin, initial plan | Platform UI → registry + pending provisioning job; no server creation |
| Billing state | Authorized billing contact obtains immutable quote/checkout; only verified webhook settles. Owner may grant the bounded one-time trial. Zero allocations do not imply unlimited use |
| Export reviewed provisioning spec | Platform owner reads `platform.provisioning_spec`; no DB secrets in spec |
| Create isolated site/database and install apps | Linux operator runs `scripts/provision-organization.py <spec> --dry-run --create-site`, reviews commands, then explicitly uses `--apply --create-site` when authorized. Bench prompts hold passwords; don't pass secrets in command arguments |
| Initialize one institute/admin identity | Existing `provisioning.initialize`; idempotency checks tenant/site/code and existing admin; local operator registry records result |
| Apply fresh policy | Owner/server generates `platform.manifest`; trusted operator delivers payload/signature to tenant `saas.apply_manifest`. Never expose signing keys in Vue or use direct tenant SQL |
| Invite admin | Configure mail; operator invokes `provisioning.invite_admin` for the named admin. Billing contact invitation is a distinct control-plane login |
| Enable DNS/TLS and tenant | Operator maps verified host, confirms manifest/limits, records ready state, and performs smoke tests |

Application `provisioning_result` is an audited status record, not proof that infrastructure exists. The UI explicitly identifies next operator work. Suspension becomes effective on the tenant through delivered manifest or lease expiration; do not claim immediate distributed suspension without delivery confirmation.

## 7. Smoke tests and rollback

Smoke-test owner registry/plan/CUSTOM quote without cross-tenant academic analytics; admin teachers/students/programmes/classes/branding; teaching-only versus full-control edits; student paid/unpaid/free native and portal content; uploads/private downloads/quota rejection; papers/submissions/explicit grades; notification preferences/read state; OTP cooldown/expiry; AI consent/quota/citations/private conversations/source invalidation; mobile PKCE/revocation; verified payment callbacks/replay. Check desktop/tablet/mobile keyboard/focus/errors/empty states against real data. See PROVIDER_ACCEPTANCE.md.

On failure, stop admissions and workers as appropriate, preserve diagnostic/transaction evidence, and choose a tested rollback. Reverting code alone does not reverse schema/data migrations. Restore the matching database **and files/config/encryption key** plus prior app/upstream revisions when necessary, then reconcile external payments and provider resources created since the backup. Never replay signed payments into an inconsistent restored ledger without reconciliation. Test restore duration/RPO/RTO in advance. Roll out tenant-by-tenant while accounting for shared-code compatibility.

## Exact production gate

- [ ] Compatible upstream/runtime commits pinned; full deployment dependency/security scan clean or reviewed.
- [ ] Staging install and existing-data upgrade succeed; DB/file/encryption-key restoration demonstrated.
- [ ] Real MariaDB/Redis concurrent quota, payment and job recovery tests pass.
- [ ] Browser/mobile auth, roles, private files and tenant/course isolation pass.
- [ ] Required providers accepted with evidence; unavailable optional features disabled.
- [ ] Hosted AI privacy consent, retention, cost rates and reconciliation procedure approved.
- [ ] DNS/TLS/canonical hosts/proxy/cookies and email DNS verified.
- [ ] Manifest issuance/delivery/renewal and suspension propagation monitored.
- [ ] Backups, monitoring, queue/scheduler alerts and rollback ownership assigned.
- [ ] One-tenant rollout and all role smoke tests pass; maintenance/rollback window approved.
- [ ] No live release claim until the deployment owner signs off the evidence.
