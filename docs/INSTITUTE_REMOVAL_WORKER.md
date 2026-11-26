# Institute removal worker

Implemented candidate, 27 November 2026. Not installed or enabled in production.

The manager-only dashboard request contains a confirmed code/hostname, reason and server-generated request ID. A separate root-owned systemd worker polls private Frappe methods through local Bench CLI. Nothing in the HTTP API accepts executable names, filesystem paths, database names or shell commands. Manager authority is rechecked on retry. The worker serializes runs with an OS lock and keeps a request-bound private journal.

The root-owned inventory is mandatory. Only separately hosted sites with dedicated database users/databases and dedicated nginx files are eligible. Public, platform and staging hosts are protected. Shared-campus organizations are not candidates. Shared nginx files such as the current `sisu-new-tenants.conf` are intentionally refused; an operator must split dedicated routing under an independently reviewed change before enabling removal for such a tenant. Custom domains also require operator review. There is no generic whole-server cleanup operation.

## Sequence and retention

1. Recheck request, manager, disabled organization, payments and exact inventory identity.
2. Compare site config database endpoint/name/user/tenant binding. Refuse shared identities across configured sites and database principals with unrelated grants.
3. Refuse unresolved invoices, payouts, refunds, payment attempts and nonzero wallet balances.
4. Save original routing/config/grants, return HTTP 410 for the tenant, pause its scheduler, revoke its dedicated database privileges and close its connections. Other services stay running.
5. Dump SQL and archive uploads/config, checksum all artifacts and verify readable archive contents. Completed financial/audit records remain in the private SQL backup.
6. Drop only the inventoried database and dedicated user; move its site directory into its private recovery archive.
7. Verify database/user absence, retired routing and archived site. Retire the control-plane organization, subscription and provisioning jobs without deleting their history. Release code/hostname fields only at this step.

Private backups are retained, not destroyed. Thus “remove institute” deletes active hosting/database, not every retained audit or recovery copy. Set the company's backup retention policy separately. The existing legacy provisioning registry was absent during inspection; the current worker updates control-plane reservations, and does not invent a legacy registry. If a separate provisioning registry is introduced, integrate it before enabling the worker for those tenants.

## Operator installation (approval required; not executed)

Install **reviewed committed copies** of the worker script and its three package files under `/opt/sisu-hosting-worker`, owned by root and not writable by the web/app user. Do not run the root service from the sisu-writable application directory. Layout:

```
/opt/sisu-hosting-worker/hosting-removal-worker.py
/opt/sisu-hosting-worker/institute_lms/__init__.py
/opt/sisu-hosting-worker/institute_lms/hosting_retirement.py
/opt/sisu-hosting-worker/institute_lms/hosting_removal_adapter.py
```

Install `deployment/removal-worker.example.json` privately as `/etc/sisu/removal-worker.json` (root:root, 0600). Leave disabled until inventory is reviewed. Add each eligible organization under `tenants`, with:

```
hostname, code, database, database_user, database_user_host,
database_host, database_port, mysql_defaults_file, nginx_file, nginx_sha256
```

Use the exact server values, never guesses. `mysql_defaults_file` is a separate root-owned 0600 MariaDB client file containing an explicit host, port and privileged credentials; no credential values belong in Git, command arguments or logs. Root backup directory must be 0700. The dedicated nginx file must contain only that exact server_name, no aliases or other sites. The inventory hash binds the reviewed original routing.

Deploy the Frappe bridge/DocType fields through the approved app release and migration. Install the service/timer units only after staging integration and privilege testing. Service sandbox paths may need an operator-reviewed adjustment for the site's nginx error-log location. Enabling the timer is a production configuration change and requires explicit approval. The template is disabled by default.

## Retry and recovery

The dashboard exposes status, progress and a retry for failed requests. Retry preserves the request ID and backups, revalidates manager authority and continues the journal. A worker crash before status update leaves the private journal authoritative. Do not clear request IDs or edit journal stages to force progress.

A pre-deletion failure can leave the tenant in maintenance/HTTP 410 with revoked grants. It deliberately does not reopen a possibly inconsistent tenant automatically. Inspect the private artifacts and failure stage; either repair the cause and retry or perform reviewed restoration of original grants/config/routing. After database deletion, restore the verified SQL/uploads/config into an isolated environment before any approved recovery. Do not reset other sites or shared service groups.

## Test evidence and limits

User-run isolated test passed on 27 November: real disposable MariaDB 11.8 database dropped, its dedicated user removed, separate nginx site returned 410, unrelated database preserved, SQL backup restored with institute and paid invoice records intact, and retry was safe. Evidence: `/tmp/sisu-removal-disposable-7b228ha2/result.json` on the server. The random disposable container was removed by the test; backups/evidence remain private.

This test used a **fixture control-plane bridge**, not a full Frappe dashboard integration. Before enabling production: exercise the migrated dashboard request/manager checks and worker completion against a disposable Frappe tenant, validate root-owned installation/sandbox behavior, test revoked manager and interrupted operations, and review actual tenant inventory. Unit tests and an adapter integration test are not a substitute for that release gate.
