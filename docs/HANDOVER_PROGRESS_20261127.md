# SISU handover implementation — 27 November 2026

Branch: `feature/sisu-post-launch-refinements`. Production application, configuration, services and customer databases are unchanged. Git publication is to this feature branch only; no main merge, automatic deployment or company transfer.

## Implemented

- Reconciled live Google signup role selection, provider review/notifications and their regression tests, preserving local onboarding and usability edits.
- Recovered 52 files from the actual served marketing release, including current hero assets. Matching full portal assets were rebuilt from the candidate source.
- New institute first-login profile submission automatically uses the existing approval service after verified email, phone and profile checks. It continues immediately; teachers and previously pending/rejected profiles retain their existing workflows. Subscription payment is still required and paid/trial dates are not reset.
- Added manager-only institute removal requests/status/retries, immutable request IDs, pending-removal guards, a restricted root-owned hosting worker, exact tenant/database/routing validation, obligations checks, private backups, tenant quiescence, dedicated database/user deletion, archive retention and completion verification. Configuration is disabled by default and no worker has been installed on production.

## Checks

- 1,219 backend tests passed.
- 231 frontend tests passed.
- Production frontend build passed (large-chunk warning only).
- Final real disposable MariaDB/nginx test passed: dummy database/user deleted, HTTP 410 checked before deletion, unrelated database preserved, SQL restored with dummy institute and paid invoice, safe retry.
- Final private evidence: `/tmp/sisu-removal-disposable-7b228ha2/result.json`.
- Test archive SHA256: `bb591cfd6a9eee942e282dff154acc6331a5c6b59963bcd7ebc837fa761bc21c`.
- The disposable test uses a fixture control-plane bridge. It is not a full Frappe dashboard-to-worker integration test; that remains a required staging release gate.

## Changed file groups

- Approval and live reconciliation: `registration.py`, `profiles.py`, `provider_review.py`, `owner_people.py`, `portal_policy.py`, `portal_session.py`, `provider_onboarding.py`, signup/first-login Vue components and related tests.
- Removal: `tenant_retirement.py`, `removal_control.py`, `hosting_retirement.py`, `hosting_removal_adapter.py`, organization/provisioning/subscription controllers and DocType fields, billing/policy guards, owner UI, worker script and systemd/example config files.
- Recovery/build: `marketing/`, `institute_lms/public/portal/`, `institute_lms/www/campus.html`.
- Documentation: developer guide, production reconciliation report and removal-worker installation/recovery guide.

Existing unrelated operator scripts, exports and logs are excluded from the commit. No private credentials, databases or uploaded customer files are intended for Git publication.

## Handover and release gates

The repository candidate is prepared for review, not certified as deployed. Before any production release: test the migrated Frappe dashboard/worker bridge on an isolated tenant, review dedicated routing/inventory and root-owned installation, review migrations, back up/restore-check production, approve the exact release manifest and rollback plan. Shared nginx files and shared-campus institutes are refused by the removal worker. The absent historical provisioning registry is not recreated by guesswork. Financial and audit history remains in private backups/control-plane records.

See [Developer and Deployment Guide](CLIENT_DEVELOPER_GUIDE.md), [Removal Worker](INSTITUTE_REMOVAL_WORKER.md), and [Production Reconciliation](PRODUCTION_RECONCILIATION_20261127.md). Company repository transfer needs the target organization and separate approval. Do not deploy historical pinned installers against this candidate.
