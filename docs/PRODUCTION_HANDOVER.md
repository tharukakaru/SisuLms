# Production source handover — 14 November 2026

Branch: **mergetharukaa-prod**. The LMS files were exported directly from production. Marketing was updated to the release deployed and verified on 14 November at 02:24 UTC; its privacy page is retained from the export. `deployment/production-manifest.json` records their hashes, active marketing release, framework commits and runtime versions. `deployment/handoff-verification.json` records archive verification. Repository tests, scripts and documentation supplement the export and are not claimed to be deployed files.

## Post-export correction (not yet deployed)

The CI repair corrects `account_billing.daily()` to create a normal unpaid renewal invoice instead of referencing an undefined `start_paid` variable. It does not charge a card or extend access. Regression coverage checks that repeated runs create only one invoice and preserve the access expiry. Payment test fixtures were also updated for the exported gateway interface.

The production manifest remains the original deployment evidence. On this revision, the snapshot verifier is expected to report only `lms/institute_lms/account_billing.py: changed`. Commit `dcbe367` is the unchanged exported baseline. Deploy and validate the renewal correction separately before claiming this revision exactly matches the live server.

## Project layout

- `institute_lms/`: Frappe backend, DocTypes, campus entry and compiled assets.
- `frontend/`: editable Vue frontend and build configuration.
- `marketing/`: exact served website with shared catalogue and login integration.
- `deployment/`: snapshot manifest and verification evidence.

Clone `https://github.com/tharukakaru/SisuLms.git` using branch `mergetharukaa-prod`, then create a feature branch. Run `python scripts/verify-production-snapshot.py` to verify the baseline.

## Server and build information

Server: `13.140.131.250`. Bench: `/home/sisu/frappe-bench`. Application: `/home/sisu/frappe-bench/apps/institute_lms`. Marketing: `/var/www/sisu-marketing-releases/`; exact active release is in the manifest. Routing: `/etc/nginx/conf.d/sisu-main-public.conf`.

Sites are `sisuacademylk.com`, `platform.sisuacademylk.com`, `teen.sisuacademylk.com` and `staging.sisuacademylk.com`. The campus route is `/campus`.

Use Linux/WSL and a separate Frappe Bench/site for development. Match framework commits and runtime versions in the manifest. Install this repository as `institute_lms`; configure MariaDB, Redis and private site settings. Existing deployment runbooks and configuration templates are references, not installers to replay blindly.

Inside `frontend/`, use `npm ci`, `npm test` and `npm run build`. Builds update `institute_lms/public/portal` and the campus entry, intentionally changing snapshot hashes. Backend integration tests need Frappe. Do not rebuild the baseline just to compare it with production.

Marketing upstream is `Sisu-Academy/sisu-academy-platform`, main `69031d8`, develop `1a26cf5`, plus SISU integration. The export is already static and uses `/marketing/` asset paths; do not prefix them twice. Preserve LMS `/campus`, `/api`, `/assets` and authentication routing. The separate bookstore application is not included.

## Workflows and remaining work

Students use bank transfer and slip upload for tuition. Provider subscriptions belong to independent teachers and institute admins. Institute teachers see their institute plan read-only. Preserve institute approval and returning-account routing.

Website cards, comparison and calculator read `/api/method/institute_lms.plan_catalog.public_catalog`. Plan/trial buttons lead to the LMS login/signup landing page. Renewals remain customer-initiated, without automatic deductions.

The last completed-fixes release left card-required trials and new personal-workspace activation unfinished. Sandbox payment and live-session success do not prove saved-card verification, trial activation, live settlement or reminder delivery. Test these separately. This export changes no gateway, account or scheduler settings.

## Deployment and private backups

Review feature changes and test on staging. Back up database, configuration and uploads privately before schema changes. Build and deploy an isolated release with rollback available. Run migrations only when needed. Do not blindly pull over patched production files or replay historical patch installers.

Web service: `frappe-bench-web:frappe-bench-frappe-web`. Worker group: `frappe-bench-workers:`. Verify homepage, catalogue, signup/login, slip upload, provider billing and owner access after deployment.

This is application source, not a complete server restore. Customer databases, uploads, secrets, certificates, runtime configurations, nginx content and installed dependencies are excluded. Framework revisions and the previous routing hash are included; obtain private operational backups separately. Never commit credentials or customer data. Older repository documents describe earlier releases and must be read with this handover.

The same snapshot is also intended for `https://github.com/tharukakaru/Sisu.git` on `main`. Both repositories contain the full LMS application and served marketing website; private runtime data is excluded.
