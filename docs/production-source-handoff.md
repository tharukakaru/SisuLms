# Production source baseline — 10 November 2026

Branch: mergetharuka-prod. Parent: 79c2eb3 on mergetharuka.

## Evidence and scope

The operator compared 749 application files on the production server: 740 matched the local candidate, nine differed. The nine exact server versions were reviewed and imported, together with brand.svg and the flag-icon MIT licence. Their differences cover the separate four-plan billing flag, signed commercial plan propagation/validation, mobile sessions bound to validated institute membership, and policy delivery readiness guards. This reconciliation changes the repository, not the running server.

The branch also includes the deployed desktop visual refinement, supplied demo imagery, teacher institute-request setup and removal of the public owner-login shortcut. Role identifiers and backend approval checks were not changed by those UI releases. The separate owner sign-in remains https://platform.sisuacademylk.com/login?redirect-to=/campus.

`releases/production-source-2026-11-10.json` records normalized text SHA-256 hashes for the 751 application files covered by reconciliation. This is application-source parity, not a full server snapshot. Runtime settings, database contents, uploads, external service credentials, DNS, Nginx configuration, the separate marketing website, and retained old frontend chunks are outside that comparison.

## Development and release workflow

1. Review this branch in a pull request into main. Fetch current main and resolve any conflicts deliberately; do not force-push or overwrite another developer's changes.
2. Branch new work from main. Run the existing release-checks workflow and staging/browser acceptance before production deployment.
3. Deploy an exact reviewed commit with a database/config/upload backup. Install compatible dependencies, run required Frappe migrations, build frontend assets, clear caches and restart services using the maintained deployment procedure for that release.
4. Preserve older hashed frontend assets during replacement so open browser tabs continue loading. Git stores the current generated build; the live server may retain older chunks intentionally.
5. Record the deployed commit and repeat application-source comparison. Prefer code-to-server deployment rather than unrecorded server edits.

Do not run old scripts/deploy-full-server-release.py blindly: it is a pinned historical release with archive hashes and site assumptions. UI patch installers also require their matching archive and before/after hashes. The original patch manifests are retained under docs/releases for audit; the first UI patch has since been superseded for PortalRoot.vue by the public-login cleanup. Rebuild from this branch for a new complete release instead of replaying all historical patches.

## Runtime setup and data

Use the existing configuration examples and activation scripts as references, reviewed for the destination environment. Shared plan catalogue configuration, owner reporting and scoped owner-invitation delivery were activated separately from source deployment. Secrets belong in protected site/server configuration, never Git. Public/Teen scheduling and general mail queues have previously been held; audit actual settings before enabling any jobs or notifications.

The demo presentation script previews by default and applies only exact named test fixtures with --apply and a private backup. It is not a migration for real customers. Login passwords are set privately and are not in this repository. Database names, approved memberships, enrolments and live bank details are not reproduced by cloning Git.

## Validation and remaining acceptance

Local reconciliation: 879 Python tests pass. Frontend tests and build are run separately with results reported in the handoff. Mock-browser checks cover sign-in, role navigation and the focused teacher request UI; they do not prove live external-service delivery.

The user reported successful production public-login cleanup and earlier UI checks. Bank-dependent subscription/wallet/payout acceptance remains pending. Teacher automatic-login routing and institute approval delivery require production evidence; this source baseline does not claim to complete those changes. Hosted-site provisioning and policy delivery still require configured remote infrastructure.

Temporary diagnostics, test result logs, local preview harnesses and downloaded server archives are intentionally excluded. Production configuration and uploaded customer files require a separate secure operational handover.
