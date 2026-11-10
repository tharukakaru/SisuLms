# Platform owner release and acceptance — 10 November 2026

Production owner operations, dashboard, scoped invitation service and password-page deployments passed their server checks. The user confirmed billing invitation → email receipt → password setup → sign-in → billing dashboard end to end. Other acceptance items below retain their individual status.

## Changes
- Billing uses owner-only, read-only reports from explicitly configured public/Teen campus databases: provider plans and invoices, date filters and pagination. No student subscription records and no payment mutation.
- Provisioning shows institute names, website details, a clear setup checklist and progress notes. Marking ready requires explicit operator verification. It records setup; it does not create servers or websites.
- Owner invitations support the deployed Frappe password-reset API and use the configured outgoing sender. Only the primary owner can grant/revoke owner access.
- Audit history includes both hosted-site changes and account/owner actions.
- Readiness shows local health, outgoing mail queue counts and configured report sources. It does not equate configuration with external delivery or payment acceptance.
- Removed the crossed-out legacy Site policies explanation. Improved owner controls, mobile layout, empty pagination, floating notifications and the guide.
- Current shared plans, student bank-transfer workflows and gateway hold remain intact.

## Deployment
Run from the sisu-cybersource-20261030 working directory:

```powershell
scp "..\release-candidate\sisu-owner-operations.tgz" ".\scripts\deploy-owner-operations.py" ".\scripts\activate-owner-operations.py" ".\scripts\check-owner-operations.py" root@13.140.131.250:/tmp/
ssh root@13.140.131.250 "sudo -u sisu /home/sisu/frappe-bench/env/bin/python /tmp/deploy-owner-operations.py && sudo -u sisu /home/sisu/frappe-bench/env/bin/python /tmp/activate-owner-operations.py && supervisorctl restart frappe-bench-web:frappe-bench-frappe-web frappe-bench-workers: && sudo -u sisu /home/sisu/frappe-bench/env/bin/python /tmp/check-owner-operations.py"
```

Source conflicts stop deployment. Sources/UI and owner reporting configuration are backed up privately. Activation only configures an allowlist for read-only reporting. Production checks roll back their test setup changes and do not send messages or payments.

## Browser acceptance
Hard refresh the Platform owner website.
1. Organizations: create a designated test request, confirm the form resets, open Manage and check the correct institute. Use meaningful reasons for changes. Verify saved changes in the table and Audit log. Saving domain metadata does not configure DNS.
2. Plans: already user-confirmed. Verify the existing shared catalogue is still present; avoid changing live prices just to exercise a button.
3. Site policies: see real setup blockers. Do not mark delivery complete manually. A configured host must acknowledge the signed settings.
4. Provisioning: inspect a test institute; record In progress with a note. Ready must remain disabled until the verification checkbox is selected. Only mark a real site ready after the operator actually verifies it.
5. Billing: select public/Teen campus, filter dates, compare listed provider invoices to their source accounts. Amounts remain grouped by currency and status. Empty results are valid.
6. Commerce: verify received hosted-site reports or the honest empty state. It is not student bank-transfer revenue.
7. Admin access: delegated test owner can view but cannot invite/revoke. Primary owner may test with an authorized dedicated address. A queued email still needs inbox confirmation.
8. Audit log: confirm newly saved actions appear; pagination only when needed.
9. Readiness: run checks, inspect email queue errors/pending counts. Mail server acceptance does not prove inbox delivery.
10. Platform guide: verify clear explanations and mobile layout.

## Remaining launch dependencies
- Real email inbox delivery, DNS/HTTPS and remote policy acknowledgement require production verification/configuration.
- HNB/CyberSource activation/testing is still held pending the bank reply; no claim that cards, provider subscriptions or payouts have passed.
- Full programme learner completion/certificate browser acceptance should remain on the handover checklist.
- GitHub update follows production acceptance. Role-wise Figma UI work and final credential handover follow the user's agreed order.

## Local validation
867 backend tests, 115 frontend tests, production build and static checks passed. Mocked-API desktop/mobile browser checks cover navigation, billing filter submission, provisioning verification, delegated access visibility and readiness. These checks do not replace live browser acceptance.

## Confirmed follow-up and repository synchronization
- Billing invitation/sign-in browser flow passed on 10 November 2026.
- Scoped owner scheduling enables heartbeat and fresh access invitations only. General email, other owner scheduled jobs, public/Teen scheduling and payment holds remain intentionally restricted. This is not full launch readiness.
- New password setup page uses native Frappe token/password validation and displays errors; the exact cause of the earlier upstream page failure was not established.
- Retrieved and reviewed the live provision_verification.py dependency; its signature, freshness and tenant-binding tests pass. No additional local imports are missing.
