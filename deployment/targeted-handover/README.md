> Final status (27 November 2026): targeted application release deployed and verified on three live sites. Automatic institute deletion removed from scope by the client; root worker remains uninstalled. See docs/FINAL_HANDOVER_20261127.md. The preparation notes below are historical.

# Targeted handover candidate - 27 November 2026

This patch applies to the saved live-source export, not the feature branch or preview source. Do not merge the full feature branch into production to deploy this release.

Scope: automatic approval on a new institute profile after verified registration email and phone; owner removal request UI, root hosting worker, and retirement guards. Existing teacher/signup UI, marketing, login fixes and production configuration remain the live baseline.

The patch contains 25 source changes. `source-manifest.json` records normalized live-before and candidate-after hashes. Check current live hashes before installing. Build the frontend from the patched live baseline; never mix preview and production entry/chunk files.

Evidence: 19 focused tests passed on this narrowed source; frontend build passed. Targeted preview migration, source/dependency checks and HTTPS asset checks passed (operator output). Real disposable MariaDB/nginx removal passed previously, including restore and retry, but used a simulated control-plane bridge.

Outstanding: real Frappe dashboard-to-worker integration, reviewed production dedicated tenant inventory/routing and worker credentials, production backup/rollback validation. The root worker must remain disabled until these checks pass. Shared-campus institutes/shared nginx files are refused. No removal of customer data has been performed.

Production deployment has NOT been executed or verified. The user's authorization to deploy does not resolve these technical gaps. Historical production installers include a retired Teen site and must not be reused unchanged.
