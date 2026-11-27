# SISU | Final technical handover

## 27 November 2026 - Verified live release

The targeted live-baseline release is deployed. The operator supplied successful resume-check output confirming the installed files, three site schemas, HTTPS campus pages and frontend assets, an unchanged public catalogue, and running web/workers. No migrations were repeated by verification.

## Delivered scope

Automatic approval for a new institute profile after verified registration email and phone is deployed. Existing pending/rejected profiles are not bulk-approved. Subscription payment requirements remain. The targeted release preserves live marketing and teacher/signup flows rather than promoting the full preview site.

## Automatic deletion excluded

The client explicitly removed automatic institute deletion from the required scope. The privileged root deletion worker is not installed or enabled. The deployed owner removal-request interface remains present, but requests do not perform automatic hosting/database deletion. It must not be represented to operators as an operational automated deletion feature.

## Verification evidence

Release: targeted-live-baseline-20261127, 80 installed files. The narrowed source passed 19 focused tests and a frontend build. Preview installation checks passed before production. Final production verification passed on staging.sisuacademylk.com, sisuacademylk.com and platform.sisuacademylk.com. These checks are not an exhaustive test of every user workflow.

## Git status

Application/deployment changes were pushed to feature/sisu-post-launch-refinements in github.com/tharukakaru/SisuLms through 7d1db07. This final document revision is a subsequent local commit until pushed. No main-branch merge or repository ownership transfer is claimed.

# Operations and recovery

## Production and preview

Production Bench: /home/sisu/frappe-bench. Separate preview Bench: /home/sisu/frappe-invoice-test. Do not copy preview databases or configuration to live. The retired Teen hostname is excluded from the targeted three-site installer.

## Private backup and logs

Production backup directory: /home/sisu/.sisu-secrets/merged-production-20261127T003413695757Z. Deployment log: deployment.log in that directory. Verification log: recovery.log. These remain private on the server; credentials and customer data are not included in this handover.

## Deployed frontend

Verified entry assets: index-BdiWZj3s.js and index-CaGFgTIz.css. Keep matching entry and chunk files together. Before a future release, compare live source hashes against its manifest and preserve current source, databases, uploads and configuration.

## Recovery guidance

An SSH disconnect does not establish deployment failure. Inspect the process, private log and service state before retrying. Use matching release verification only after the installer has exited. Never rerun a historical four-site installer or automatically restore a database after migrations; that could discard newer customer or financial data.

## Client acceptance and ownership

The agreed deployment scope is complete based on the recorded deployment verification. Routine business workflow acceptance remains the client/operator responsibility. Automatic database deletion is excluded by client instruction, not an outstanding delivery obligation. Future enablement would require separate real Frappe integration testing and a reviewed dedicated tenant inventory.

## Documentation location

The repository deployment/targeted-handover directory contains the live-baseline patch and source-hash manifest. Historical documents describe earlier candidate states; this dated final handover supersedes their not-deployed status for this release.
