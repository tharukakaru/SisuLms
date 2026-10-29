# RUN 1: core backend handoff

This document supersedes older roadmap/status claims for the changes below. This is an implemented backend foundation, **not production acceptance**. No tenant database, production service, DNS record, merchant account or real provider was changed. RUN 2 and RUN 3 have not started.

## Architecture and operational boundary

- Keep Frappe 17-compatible `institute_lms`, Frappe LMS, MariaDB, Redis and Vue. Pin exact compatible Frappe/LMS commits in staging before release; their code and runtime are not bundled here.
- Use a **dedicated control-plane Frappe site/database** plus **one independent Frappe site/database per organization**. No code opens or queries another site's database.
- Only the configured platform-owner account may administer the registry, plans, overrides and provisioning results. Institute Admin is a site-local membership, never platform authority. Do not grant Institute Admin users System Manager or bench access.
- Institute codes are public identifiers. Host routing, user authentication and site-local membership establish isolation.
- The control plane holds registry and organization subscription billing. Each tenant receives a signed, monotonically versioned subscription snapshot using its own secret. `platform.manifest` produces it; `saas.apply_manifest` verifies signature, tenant ID, exact site hostname, revision, issue age and lease.
- **Deployment must supply the transport:** an operator/worker obtains a fresh owner-authorized manifest and POSTs its exact payload/signature to the named tenant over HTTPS. It must retry failures, report delivery, and refresh leases well before 24 hours. No cross-site service, DNS or fleet orchestrator is simulated. Suspension takes effect on delivery, or at lease expiry (maximum 24 hours); it is not instantaneous while a tenant is disconnected. Deliver suspension manifests immediately.
- Subscription dates and signed lease timestamps are UTC. Course/session dates and monthly AI usage buckets use the tenant's Frappe site time zone.

## Implemented modules and bug fixes

| Area | Source under `institute_lms/` | Behavior |
|---|---|---|
| School billing | `api.py`, `class_billing.py` | Only institute-owned school classes are exempt. Teacher-owned paid classes retain invoices. Free classes need neither a platform pricing assignment nor a wallet. Legacy zero-fee enrollments in paid independent classes fail closed pending finance review; records are not fabricated or erased. |
| Wallets | `wallet.py`, `class_billing.py` | Independent teachers resolve wallets without institute association; institute revenue uses the institute wallet. Provisioning serializes on owner/institute rows and rejects conflicting beneficiary wallets. Existing transaction/earning protection remains. |
| OAuth | `youtube.py` | Single-use state under Redis lock, user/member revalidation, explicit callback commit matching the Calendar pattern. |
| Native paid access | `native_access.py`, `hooks.py`, `api.py` | Course reads and protected files reuse SISU access. Reviewed course-scoped native APIs are allowed; unreviewed native RPC/REST is denied for portal users when SISU-linked courses exist. Free linked classes retain upstream publication checks. Operators retain maintenance access. |
| Control plane | `platform.py`, `provisioning.py`, `scripts/provision-organization.py` | Registry, hostname/code uniqueness, owner APIs, billing-contact invitation, auditable provisioning specification/status and operator command. No passwords in specifications. |
| Plans | `saas.py`, `saas_rules.py` | STARTER/PREMIUM AI/CUSTOM snapshots, centralized feature/limit resolution, server gates, custom audited overrides, support tier, grace/expiry/suspension and lease enforcement. |
| Organization payments | `subscription_payments.py` | Separate quote/attempt/transaction/webhook ledger; immutable quote snapshot, stable provider idempotency key, signed bound settlement, locked renewal and replay protection. Redirects cannot activate access. |
| Usage/storage | `usage.py`, `storage.py`, `materials.py`, `papers.py` | Seat/class/course admissions and storage quota under subscription lock; current locking reads; usage ledger; File metadata and bounded metadata backfill; local Frappe storage default and private-read adapter boundary. |
| Retention | `retention.py` | Configurable access expiry/grace/archive/pending-delete states, scheduler, financial/academic preservation, explicit audited detached-orphan purge only. |
| Notifications | `notification_service.py`, `notification_events.py`, `notifications.py`, `providers.py`, `devices.py` | Recipient events, channel outbox, preferences, in-app unread/read, deduplication, provider acceptance/failure timestamps, SMS/push interfaces, existing Email Queue/Meta delivery, signed Meta status webhook. |
| OTP | `otp.py`, `mobile_verification.py`, `private_contact.py` | Shared user issuance lock, distinct SMS/WhatsApp challenges, HMAC digest, 10-minute expiry, five attempts, one-minute cooldown, user/phone/IP throttles, single-use verification. Provider failures still consume cooldown. |
| Mobile | `mobile_auth.py`, `mobile_api.py`, `portal_policy.py` | Per-user/site hashed tokens via browser Google/Frappe login plus PKCE approval; seven-day expiry and owned revocation. No shared API key or client-controlled Google attestation. |
| Existing AI boundary only | `soul.py`, `papers.py` | Existing provider entrypoints now require plan features and debit monthly credits before provider work. No RAG, embeddings, new AI features or conversation implementation. |

The only source UI change is WhatsApp OTP verification's explicit channel in `frontend/src/commerce/PrivateContact.vue`. Production portal assets were rebuilt. Existing frontend commercial/notification screens are not fully wired to these new contracts; that is RUN 3.

## Schema and migration

Fourteen new standard Frappe DocTypes, under `institute_lms/institute_lms/doctype/`:

- `IL SaaS Plan`, `IL Organization`, `IL Subscription`, `IL Provisioning Job`, `IL SaaS Audit`.
- `IL Payment Attempt`, `IL Payment Transaction`, `IL Webhook Event`, `IL Usage Entry`.
- `IL Stored Object`, `IL Notification Event`, `IL Notification Preference`, `IL Device Token`, `IL Mobile Session`.

Existing schema extensions:

- `IL Checkout Quote`: tenant and immutable subscription-plan snapshot.
- `IL Notification`: event/device links, additional channels/statuses, sent/failure timestamps.
- `IL Classroom` and `IL Enrollment`: expiry, grace, archive, delete and lifecycle fields.

Schema JSON is synchronized by Frappe. `patches.txt` registers `patches/run1.py` post-model-sync; installation also invokes its idempotent initialization. It seeds missing plans, preserves existing plans/data, fills blank lifecycle values and adds indexes. Unique fields protect tenant IDs/hostnames/codes, attempts, transaction references, event keys and token identities. New internal records have no generic REST permissions; managed service flags restrict writes and immutable ledgers reject edits/deletion.

`before_migrate` stops on specified duplicate legacy identities or paid native lessons containing public files/SCORM; it does not delete or merge them. Resolve those findings before retrying a backed-up staging migration. Existing damaged teacher enrollments require finance to reconstruct/reconcile billing through authorized workflows. No speculative debts or automatic paid grants are created.

**All seeded monetary prices and numeric allocations are zero/unconfigured. Zero means no allocation, not unlimited.** Configure reviewed prices and all limits on the control plane before a trial/checkout. Register and provision each existing tenant and apply a signed subscription; missing policy fails closed. Do not put this build on a running tenant without that preparation.

## Operator provisioning sequence

1. Back up existing databases/files. Create a dedicated control-plane site and install matching LMS/institute_lms code. Configure `il_control_plane`, platform owner and outgoing email through secure site configuration.
2. Configure plans via `platform.configure_plan`. `platform.register` reserves the organization, creates an unprivileged billing-contact account if needed, and creates a past-due subscription/provisioning job. `invite_billing_contact` queues a password-setup invitation when mail is ready.
3. Export `platform.provisioning_spec(job)` to an operator-only file. On the Linux Bench host, run `python scripts/provision-organization.py spec.json --dry-run --create-site`; review, then explicitly use `--apply --create-site` (omit creation permission if the site already exists).
4. The command uses a host-local locked registry, prompts through Bench for site secrets, installs only missing required apps, migrates, and calls non-whitelisted `provisioning.initialize`. An existing conflicting site or admin is rejected. Failure is recorded, not treated as completion. Publish the actual job outcome using `platform.provisioning_result`.
5. Configure the tenant-specific signing key on both sides through the deployment secret store. Set tenant host/HTTPS, provider configuration and approved mobile redirect URIs. Apply a fresh signed manifest after a bounded trial or verified payment. Configure outgoing email and invoke bench-only `provisioning.invite_admin` for the named tenant Admin.
6. Run staging acceptance, then enable routing/workers/scheduler and manifest refresh. DNS/server creation, certificate issuance, backups and health monitoring remain infrastructure tasks.

The older single-site setup utility remains available for legacy development. Use this provisioning workflow for SaaS registration; the old utility does not assign a commercial subscription.

## Payment contract

Student tuition keeps `payments_lk.py`, `IL Invoice` and the existing wallet settlement flow. Organization subscription payments run only on the control plane with **different merchant configuration**.

1. Billing contact authenticates on the control-plane host; `subscription_payments.quote(tenant, plan)` freezes server pricing/features/limits for 15 minutes. CUSTOM uses existing `IL Price Assignment`/`owner_pricing` with an LKR monthly/yearly Platform contract.
2. `checkout(quote)` stores an immutable attempt before provider contact and reuses its request/idempotency identity. Ambiguous responses retain that attempt for reconciliation; an old/terminal attempt is not silently replaced.
3. `notify` verifies raw-body timestamped HMAC, event mode, payment/checkout/reference, exact minor amount/currency and provider identity before settlement. A unique transaction plus locked subscription prevents duplicate extension. Reordered failure/cancel events cannot undo success. Administrative suspension remains in force after payment.
4. Only this verified settlement updates the purchased period; the tenant changes only after a signed snapshot. Owner restoration is limited to a previously verified, unexpired suspended subscription. Browser success/cancel URLs are informational.

Webhook arrival before checkout identity has been persisted must retry; do not accept an unbound callback. Reconcile ambiguous checkout/provider outcomes. Refunds, automatic recurring debits, pro-rating, tax invoices and provider-led account reconciliation are not added in this foundation. Never manually mark a quote paid to simulate provider acceptance.

## Notification and provider behavior

Events cover announcements, session changes, materials, published papers/assignments, due reminders, quiz results, payment success/failure, subscription renewal/expiry, course expiry and certificates. Hooks preserve current emission paths. Existing papers supply assignment/quiz events; native certificate hooks depend on the installed LMS schema and require staging verification.

- IN_APP deliveries are durable with owned `inbox`/`mark_read` APIs.
- Email transfers to Frappe Email Queue in the same transaction. Email Account supplies transport credentials.
- SMS: `il_sms_adapter` points to trusted server code accepting `(phone, message, idempotency_key)` and returning `{"provider_id": "..."}`. The legacy verification hook is retained for OTP only and must raise on failure. Absence of a configured provider fails OTP clearly; delivery jobs remain queued.
- PUSH: `il_push_adapter` accepts `(token, platform, body, idempotency_key)` and returns a provider reference. Device tokens are Password fields, hash-indexed, owned and revocable. No FCM service account is invented.
- WhatsApp retains approved template/opt-in rules, bounded 429 retries, and uncertain outcomes in Review. Delivery callbacks validate Meta's HMAC and configured phone ID. SMS/push ambiguous outcomes also stay in Review; operators/providers must reconcile before retrying. There is no claim of exactly-once delivery across an unreliable external network.
- Preferences are rechecked at dispatch. Existing channel opt-in/verified-contact requirements still apply. Missing credentials never create a fake accepted delivery.

## Storage and retention boundary

Frappe local private/public storage stays the default. `before_write_file` checks quota before physical writes; File hooks cover deduplicated attachments too. The subscription row serializes uploads/admissions until transaction commit, with locking reads rather than a stale transaction snapshot. Logical File sizes count separately even when Frappe shares physical bytes (conservative accounting). Existing files already count before metadata backfill finishes.

`IL Stored Object` tracks institute, class/course, owner, size, backend/key, creation, expiry/archive/delete, status and legal hold. A daily bounded backfill creates metadata for old File records. Usage is not reduced simply by archiving metadata. No automatic file, video, result, certificate or financial-record purge is introduced.

`il_storage_read_adapter` is a **trusted private-reader boundary**, not a complete S3 uploader. A replacement storage backend must provide Frappe-compatible write/delete hooks, private authorization and bounded reads. Keep `il_storage_backend=frappe` until that adapter has passed staging tests. Uploaded-video transcoding/CDN infrastructure remains a deployment task. YouTube still stores identifiers/metadata, not downloaded videos.

Paid native public files and SCORM cannot be protected by Python after nginx serves them. Migration refuses known unsafe links; move such content to protected materials first. Native API allowlisting intentionally restricts unreviewed LMS UI calls; use the SISU facade until exact upstream calls are reviewed and covered by payment-boundary tests.

## Mobile contract for RUN 3

Use the tenant's canonical HTTPS host; never send an institute code as a credential.

1. Open `mobile_auth.authorize` in the system browser with a random `state`, S256 PKCE challenge and pre-registered redirect URI. User authenticates and approves a CSRF-protected form. Students retain Google-only policy.
2. Validate returned `state` in Flutter. POST the short-lived code, original verifier, redirect URI and device ID to `mobile_auth.exchange` without browser cookies. Store the returned token in OS secure storage.
3. Use `Authorization: Sisu <token>` only on `/api/method/institute_lms.*`; no browser cookies and no shared API key. This scheme is authenticated through Frappe auth_hooks. Membership/object checks still run. `mobile_auth.logout` revokes the owned session; reauthenticate after seven days (no refresh token in RUN 1).
4. Reuse `mobile_api.current/classes/enrollments/lesson`, `profiles.me/save_profile`, `api.classroom_detail/invoices`, `materials.content`, paper listing/start/submit, existing payment checkout, `saas.status`, `notification_service.inbox/mark_read/save_preferences` and `devices.register/revoke`.

A browser session calling the regular APIs keeps Frappe's normal CSRF requirements. The new token scheme and Google handoff must receive live Frappe, browser and Flutter acceptance testing before release. The mobile facade deliberately does not expose privileged native REST or arbitrary document methods.

## Secure configuration (site_config / secret store, not frontend .env)

| Scope | Keys/configuration |
|---|---|
| Platform | `il_control_plane`, `il_owner_provisioned`, `il_owner_email`, `il_tenant_signing_keys` (tenant ID → unique secret) |
| Tenant | `il_tenant_id`, `il_control_plane_key`, canonical `host_name`, Frappe encryption key, normal DB/Redis/queue settings |
| Organization merchant | `il_subscription_payments_lk_mode`, `il_subscription_payments_lk_secret_key`, `il_subscription_payments_lk_webhook_secret` |
| Student merchant | Existing `il_payments_lk_mode`, `il_payments_lk_secret_key`, `il_payments_lk_webhook_secret`; validate existing INTEGRATIONS documentation against site configuration |
| SMS/push | `il_sms_adapter`, `il_push_adapter`; actual adapter-specific provider credentials only in secure server configuration |
| WhatsApp | Existing `il_whatsapp_token`, `il_whatsapp_phone_id`, `il_whatsapp_graph_version`, `il_whatsapp_templates`, `il_whatsapp_auth_template`; new `il_whatsapp_app_secret`, `il_whatsapp_verify_token` |
| Storage | `il_storage_backend` (default `frappe`), optional `il_storage_read_adapter`; no object-store keys bundled |
| Mobile/Google | `il_mobile_redirect_uris`, Frappe Social Login Key for Google; exact registered browser callback/redirect origins |
| Email/Calendar/YouTube | Frappe Email Account/Email Queue and existing OAuth client configuration; credentials not replaced |
| Existing AI | Existing server-only SOUL settings/provider key and review policy; monthly credits/feature allocation before provider calls |

No new frontend secret or real credential is supplied. Configure request/body limits and HTTPS at the trusted proxy; do not enable permissive CORS or disable CSRF globally.

## Verification and remaining release gates

Executed locally on Python 3.12.14 / Node 24.14.1:

- **PASSED:** 168 Python unittest cases, including 34 new RUN 1 regressions in `tests/test_run1_foundation.py`.
- **PASSED:** 53 frontend Node tests.
- **PASSED:** Vite production build using `node node_modules/vite/bin/vite.js build --configLoader native`, followed by `node scripts/copy-entry.mjs`. The normal config-bundling invocation was blocked by Windows parent-directory access; native loading completed without changing the app's build configuration.
- **PASSED:** Python syntax and JSON parsing across the shipped source/schema (final counts in completion report).
- **NOT RUN / ENVIRONMENT UNAVAILABLE:** Bench install/migrate, real MariaDB locking/rollback/deadlock behavior, Redis distributed locks, Frappe request/auth/CSRF/permissions, real browser/Flutter handoff, upstream LMS compatibility and provider sandbox/webhook acceptance. Unit mocks and thread-lock tests do not establish distributed transaction correctness.
- Initial test harness errors (missing Windows tzdata and old entitlement mocks) were corrected. No currently failing executable unit test is known.

Before RUN 2 deployment work: provision staging; pin Frappe/LMS; run migrations with a backup; reconcile duplicate/legacy billing/native-public-file findings; configure plans and signed-manifest transport; test quota races and payment replays with real databases; verify provider signatures against merchant sandbox; test Google/PKCE/CSRF/native lesson bypasses and tenant boundaries. Supply chosen SMS/push/storage providers and credentials as applicable.

RUN 2 still owns conversation/token/cost models, extraction/chunking/embeddings/vector storage, RAG, citations and advanced AI tools. RUN 3 owns full frontend wiring, release CI/CD, staging-to-production rollout, domain/DNS/SSL and complete mobile handoff. This run does not claim those are done.
