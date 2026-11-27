# Institute plan management — 27 November 2026

Based on the verified live main snapshot 04c66c8. Adds institute search and Manage plan under Organizations, plus Manage plan under People & connections > Subscription. Dedicated organizations retain their existing management workflow and gain server-side search.

Only Primary/Administrator owner managers can change shared-campus institute plans. The configured reporting-campus boundary, verified profile, enabled account, active Admin membership and exact subscription workspace are checked. Concurrent/stale edits and scheduled cancellations are refused. Trial/paid-through dates remain unchanged. Paid accounts schedule a next plan; other accounts change immediately. Existing unpaid-offer/payment-attempt safeguards and provider synchronization are reused. Changes record the requesting owner and reason.

Validation: 12 new Python safeguard tests pass; frontend production build passes. Frontend suite: 218 pass, one pre-existing marketing-signup source assertion fails (test and inputs unchanged from baseline). No real subscription was changed during local tests. Full browser/worker integration must be verified after installation using an authorized institute change.

Installer verifies the archive digest, current source hashes and required assets; backs up replaced files, clears site caches and restarts web/workers. No migrations or subscription changes occur during deployment. Failed health checks restore prior files. Existing assets remain available for open browser tabs. Never force a Git push if main has advanced.

After deployment: hard-refresh Organizations, search Teen Academy on sisuacademylk.com, choose Manage plan, verify current Gold and unchanged dates. A plan change requires a reason and confirmation; do not change a real account simply to test the button.
