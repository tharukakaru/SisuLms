# Local integration status — 2026-11-01

Fetched origin/main 2f3559a, origin/dev a74913d and origin/sisu-merge-induni f8d868f. Applied the partner source diff relative to origin/main to the existing working tree, preserving the current signup and payment changes. This is source integration, not a Git merge commit or push. Generated portal assets were rebuilt locally.

Verification: 644 Python tests, 87 frontend tests and Vite build passed. One isolated affiliation test needed an explicit coverage stub; coverage revocation has separate tests. Partner quiz DocTypes were added to the sandbox deployment reload list.

Explicit institute trial coverage is supported only by a server-side grant bound to the subscription and expiry; it does not mark invoices paid. No client grant or account has been created. Current institute coverage remains sandbox-only and limited to the audited core API allowlist; full tenant teaching workflows still require completion and runtime testing.

Outstanding: server SSH username/key location/public domain, website ZIP, resolution of same-email institute-admin/Super-Admin routing, tenant provisioning and time-limited Platinum grant, domain provisioning, student institute membership/switching, full live acceptance, secret review, Git commit/push and server deployment. Keep payments paused. Do not represent this as launch-ready.
