# SISU developer and production operations guide

Prepared 27 November 2026. Release status: **local candidate, not approved for production**.

This guide supersedes the operational assumptions in the 14 November handover. That handover's runtime manifest and four-site list are historical. In particular, do not assume the Teen site still exists. No production deployment, service restart, database deletion, GitHub push or ownership transfer was performed while preparing this guide.

## Architecture and ownership

The Vue campus application is served at `/campus`; Frappe provides authentication, APIs, document permissions and tenant data. The institute_lms app runs alongside Frappe, LMS and payments in a Linux Bench. MariaDB stores site-specific databases. Redis supports caching and background queues. Supervisor manages web and worker processes. nginx terminates/routes web traffic. The public marketing website has a separate nginx document root and release lifecycle.

The control-plane site manages separately hosted organizations. The shared public campus is not a disposable tenant. Institution approval, public-profile review, workspace provisioning and verified subscription payment are separate decisions. Never treat approval as payment settlement.

| Location | Purpose |
| --- | --- |
| `institute_lms/` | Python services, DocTypes, permissions and hooks |
| `frontend/src/native/` | Vue role dashboards, signup and onboarding |
| `frontend/tests/`, `tests/` | Frontend and backend regression tests |
| `institute_lms/public/portal/` | Compiled campus assets |
| `institute_lms/www/campus.html` | Campus entry referencing compiled assets |
| `marketing/` | Marketing source copy; current served-root parity is unverified |
| `scripts/` | Operator tools, including historical release-specific installers |
| `deployment/` | Historical release evidence; not current authoritative live state |

Known hosting paths: `/home/sisu/frappe-bench`, its `env/`, `apps/institute_lms/` and `sites/`. Current nginx marketing root/alias: `/var/www/sisu-marketing-releases/shabri-49bbcdf-20261119`, in `/etc/nginx/conf.d/sisu-main-public.conf` (27 November inventory). Private operational backups: `/home/sisu/.sisu-secrets/`. A separate preview Bench was `/home/sisu/frappe-invoice-test` with site `invoice-test.local`. Confirm these before operating; direct SSH authentication was unavailable during this audit.

## Versions and prerequisites

Local frontend declares Vue 3.5.44 and Vite 6.4.6. Read `frontend/package-lock.json` for exact installed dependency resolution. Python project metadata requires Python >=3.11 and Frappe >=17 development release, <18. These are constraints, not proof that every supported version works.

Read-only server output supplied on 27 November confirms Python 3.14.6, Node 24.15.0 and Bench 5.31.0. Web, socketio, scheduler and both workers were RUNNING. It lists public, staging and platform site directories, plus `staging.sisuacademylk.com.failed-empty-backup`; this backup directory is not an approved site. Teen was absent from that inventory. Older evidence showed MariaDB 11.8 containers and nginx 1.24.0; their current versions still require verification. Current framework revisions from the supplied read-only inventory are Frappe `980bdb0aa497ef787679353e0dbc16fd7cefbb36`, LMS `389d8a2720bfbd4b2e0de3f0f3c15d4cf0485d1e`, payments `e0de51e4040e3e07766b9d63315239114e935b00`. Do not substitute the host's `python3` for the Bench Python when installing app dependencies. Frappe previously required `pyotp~=2.9.0`; an upgrade to 2.11.2 broke `pip check`. Do not blindly upgrade dependencies.

Read-only Linux inventory (run on the server):

```sh
cd /home/sisu/frappe-bench
env/bin/python --version
env/bin/python -m pip check
node --version
/usr/local/bin/bench --version
sudo supervisorctl status
find sites -mindepth 2 -maxdepth 2 -name site_config.json -printf '%h\n'
git -C apps/frappe rev-parse HEAD
git -C apps/lms rev-parse HEAD
nginx -v
```

The live institute_lms directory is not a Git checkout. Do not initialize Git there. Inspect nginx configuration privately to determine the active marketing root; do not paste complete configuration or site_config.json into tickets or chats.

## Local development

Clone the company repository once ownership transfer is approved. Until then the source remote is `https://github.com/tharukakaru/SisuLms.git`. Continue current work on `feature/sisu-post-launch-refinements`. Preserve its existing unfinished removal changes and compiled assets.

Windows PowerShell, from the repository root:

```powershell
git status --short
py -m venv .venv
.\.venv\Scripts\python.exe -m unittest discover -s tests
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend test
$env:SISU_FRAPPE_URL = 'http://127.0.0.1:8000'
npm.cmd --prefix frontend run dev
```

The frontend uses port 5178. Point SISU_FRAPPE_URL to a disposable development Bench, never production. Native Windows is suitable for frontend work and the repository's isolated Python unit tests. Use WSL2/Linux for an actual Frappe Bench and integration tests.

Linux, from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m unittest discover -s tests
npm --prefix frontend ci
npm --prefix frontend test
SISU_FRAPPE_URL=http://127.0.0.1:8000 npm --prefix frontend run dev
```

Provision a separate development Bench using the verified production Frappe/LMS/payments revisions, Python version and compatible MariaDB/Redis versions. Install this app into that Bench and create a disposable site. Exact framework provisioning commands remain gated on current revision inventory; do not use an unpinned `bench init` against a development branch and assume compatibility. Keep email muted and real payments/SMS disabled in test sites. Never use production database credentials or upload data in local development.

Build from `frontend/`:

```sh
npm ci
npm test
npm run build
```

The standard build updates portal assets and copies the entry to `www/campus.html`. Review both together. An isolated compile check, without modifying existing generated assets, is:

```sh
node node_modules/vite/bin/vite.js build --configLoader native --outDir ../../handover-build-check
```

## Git review and company transfer

Use small feature branches, explicit file staging, descriptive commits and PR review. Run backend/frontend tests, build, `git diff --check` and a credential scan before committing. Do not `git add .` in the current dirty workspace. Do not include exported production archives, databases, upload files, private handovers or local logs. Keep the verified production baseline separate from unfinished features.

Before transfer: choose the company organization and repository name; confirm organization admin access; inventory collaborators, branch protections, test workflows, webhooks, deploy keys, secrets and integrations. Back up Git refs. Transfer using GitHub's repository transfer workflow only after explicit approval. Verify access and protections after transfer and update local origin URLs. Do not force-push. Existing test workflows may remain; do not add GitHub-to-production deployment automation.

## Credentials and configuration

Give developers individual SSH keys and least-privilege accounts; avoid shared root passwords. Transfer secrets using the company's password manager, not Git or documentation. Inventory SSH keys, database credentials, Frappe encryption keys, SMTP, OAuth, CAPTCHA, payment credentials and DNS/certificate ownership. Preserve encryption keys when restoring sites. Coordinate credential rotation and revocation of departed access separately from deployment.

Site configuration, gateway flags, OAuth domains, scheduler settings and queued email guards are runtime state. A code deployment must not silently enable features or change these. Never print full site configuration or reset-password URLs into logs.

## Manual release procedure

**No deployable package is approved by this audit.** Historical installers such as `deploy-production-merged.py` and `deploy-full-server-release.py` contain fixed hashes and outdated site lists. Do not replay them for this candidate. A release must have a newly reviewed manifest of exact files/hashes, additions/deletions, affected current sites, dependency requirements and migration list. Test that same package in an isolated environment first.

1. Reconcile live hotfixes and active marketing files into the reviewed baseline. Merge only finished features. Identify a commit and build once; keep the complete asset dependency closure.
2. Check `pip check`, disk space, current services and site inventory. Record existing maintenance/scheduler states. Stage the release without modifying active paths.
3. Obtain deployment approval and maintenance window. Save prior source, nginx routing and runtime configuration privately, plus per-site database/upload backups.
4. Apply only the manifest's reviewed files with correct sisu ownership. Preserve unrelated assets and all runtime directories. Do not use a broad `rsync --delete`, overwrite site configuration, or pull into the live app.
5. If schema/hooks require migration, migrate the reviewed affected sites under maintenance with workers appropriately quiesced. On failure, retain maintenance and follow the recovery plan; do not announce success or repeatedly rerun migrations blindly.
6. Restart approved services, restore the original intended maintenance/scheduler states, run smoke tests, and record the deployed manifest and backup location.

The following are existing-architecture operator commands, **not an instruction to execute now**. Set SITE to one confirmed affected site, repeat deliberately for the reviewed list:

```sh
cd /home/sisu/frappe-bench
SITE=sisuacademylk.com
sudo -H -u sisu /usr/local/bin/bench --site "$SITE" backup --with-files
sudo -H -u sisu /usr/local/bin/bench --site "$SITE" set-maintenance-mode on
# Apply the separately reviewed release manifest here; no generic copier is approved.
sudo -H -u sisu /usr/local/bin/bench --site "$SITE" migrate
sudo -H -u sisu /usr/local/bin/bench --site "$SITE" clear-cache
sudo supervisorctl restart frappe-bench-web:frappe-bench-frappe-web frappe-bench-workers:
sudo -H -u sisu /usr/local/bin/bench --site "$SITE" set-maintenance-mode off
sudo supervisorctl status
```

Backups must be verified, copied outside the site being changed, checksummed and retained securely off-server. Validate SQL gzip and file tar integrity; perform a restore drill in isolation. A successful backup command alone does not prove recoverability. Protect configuration backups because they contain secrets.

## Marketing deployment

The 27 November nginx inventory identifies `/var/www/sisu-marketing-releases/shabri-49bbcdf-20261119`; record the surrounding location rules before changing it. Export and compare the actual served root separately from `apps/institute_lms/marketing`. Prepare a versioned release directory; verify all HTML/JS/CSS/image references and auth links. Preserve `/campus`, `/api`, `/assets`, `/login` and password reset routing. After explicit approval, change only the reviewed marketing target, run `nginx -t`, then reload nginx. Retain the previous target for rollback. Exact target-switch commands are intentionally blocked until the exact location rules and target-switch patch are reviewed; the app archive does not establish that path.

## Institutes and removal

New eligible legacy institute registrations reuse approval after email verification. On first profile submission, a new institute with verified registration email and phone now reuses the existing provider approval service, creates its workspace and continues immediately. Existing pending/rejected profiles and teachers keep their review workflows. Existing pending applications are not batch-approved. Required profile/phone checks still govern workspace creation; subscription payment remains separate; institute first-onboarding approval is now automatic, while later identity re-review stays manual. Verify both legacy and Google signup paths in isolation.

Hosted creation uses the existing provisioning specification and operator tooling (`scripts/provision-organization.py`); confirm tenant/code/hostname uniqueness, approved apps and dedicated database ownership. Never create two jobs for the same request.

**Removal is implemented as a candidate and is not enabled in production.** Dashboard requests and guards exist. `hosting_retirement.py` now models backup, quiesce, decommission, absence verification and registry completion with retry journaling. Its tests use fake adapters. The restricted Bench/MariaDB/nginx adapter, root-owned polling worker and systemd templates now exist. Real disposable database/website removal, backup restore and retry tests passed with a fixture control-plane bridge. See [INSTITUTE_REMOVAL_WORKER.md](INSTITUTE_REMOVAL_WORKER.md) for inventory, installation and the required full Frappe staging gate. The historical provisioning registry is absent; no ownership is inferred from it. Never reuse hardcoded Teen cleanup scripts.

## Smoke tests and monitoring

Check public homepage, campus and catalogue; fresh/incognito login; password reset delivery, reset submission and `/campus` redirect; Google signup role preservation; teacher and institute onboarding; student navigation; owner permissions/sidebar; public-profile review; subscription status and existing gateway configuration. Do not submit real payments for a smoke test. Validate disabled roles cannot invoke manager APIs. Confirm workers, scheduler and email queue state without flushing unrelated pending emails.

```sh
curl --fail --silent --show-error -o /dev/null https://www.sisuacademylk.com/campus
curl --fail --silent --show-error -o /dev/null https://www.sisuacademylk.com/api/method/institute_lms.plan_catalog.public_catalog
sudo supervisorctl status
```

An HTTP 200 or loaded asset is not a successful workflow test. Protected owner entry may legitimately require authentication. Raw Frappe ping and translation APIs may be denied by the site's API guard. Investigate the actual failing request rather than weakening permissions globally.

502: inspect upstream web status/logs. 503: inspect maintenance state. 405 on password submission: inspect exact POST route and nginx handling. Email queued but not sent: inspect database suspension, muted-email flag, scheduler and SMTP separately; do not flush every email. Unclickable campus: inspect modal/top-layer state and asset-version consistency. Do not disable security guards to suppress errors.

## Rollback and recovery

Record current source and asset hashes before changes. A code-only rollback restores the prior complete source/entry/assets and caches; it does not reverse migrations. Database restoration requires a separately approved recovery plan covering writes since backup and upload consistency. Restore into an isolated site first. Never restore an old database over new customer activity merely to fix a UI issue.

For marketing, revert the recorded routing target and validate nginx before reload. For a failed app deployment, keep the affected maintenance boundary until old code/schema compatibility is established. Retain private logs and do not expose them through the website. Review `bench restore --help` on the installed version before any restore; supply credentials privately.

## Handover acceptance checklist

- [ ] Current runtime/framework revision and active-site inventory recorded.
- [x] Actual served marketing root exported and compared.
- [x] Production-only Google signup and provider-review changes reconciled locally and covered by regression tests.
- [ ] Automatic institute approval passes real isolated workflow tests.
- [x] Real removal adapter/consumer implemented; disposable MariaDB/nginx restore/decommission test passed.
- [ ] Full Frappe dashboard-to-worker staging integration and production worker installation approved.
- [ ] Candidate dependency, migration and file manifest reviewed.
- [ ] Backup restore drill and rollback ownership confirmed.
- [ ] Security scan/review complete, secrets transferred privately.
- [ ] Company organization access, repository transfer and branch protections verified.
- [ ] Deployment expressly approved and performed manually.
- [ ] Client smoke tests pass and final release evidence is recorded.

## Verified marketing recovery

The actual nginx-served release was exported separately and inspected: 134 selected files, 52 differing/missing repository files, and 40 differences from the app snapshot. The 52 files were recovered into local `marketing/` after confirming it had no uncommitted changes. Local-only files were retained for review. No production write occurred. Archive/hash evidence is in `work/sisu-production-20261127-035743/marketing-comparison.json`. Initial private-key/token signature scan found no matches; full pre-commit review is still required.
