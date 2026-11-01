# Signup sandbox update — 1 November 2026

## Confirmed live evidence
Student email OTP, SMS OTP, registration, password login and Student dashboard were confirmed by the tester. Brevo delivered its original SMTP test; Notify delivered signup OTP. Firebase browser background notification was shown. These do not establish provider signup, password reset, Google OAuth or payment success.

## Current screenshot diagnosis
The submitted teacher phone begins +76 rather than +94. The sandbox compares canonical numbers exactly with its authorized test phone. For Sri Lanka, remove the initial local zero and prepend +94 (0761234567 becomes +94761234567). Do not infer missing digits. The screenshots also show the old unstyled Google button, so the UI repair has not been confirmed deployed or loaded. Google requires both the 8001 callback registration and encrypted Frappe credential configuration.

## Prepared changes
Spaced email/Google buttons, visible styled Google signup, retained role selection, required-field errors that scroll into view, and stage feedback. Trusted Google session details prefill first/last name and email; users complete all other required details and both contact checks. Save returns to login. Provider access uses a blurred noninteractive workspace shell behind billing; no protected dashboard data is loaded behind the overlay.

Teachers can select up to five verified institute profiles in the current directory, choosing New application or Existing teacher confirmation. Pending/active totals are capped server-side and duplicate requests are reused. Institute review shows a separate confirmation section. Existing institute ownership and teacher profile-verification checks remain enforced. Confirmation queues a restricted transactional notice. Requests do not bypass payment or class permissions.

Welcome notices include role, login email and sandbox URL, never passwords. Payment activation notices originate from persisted Paid invoice transitions and include plan/expiry and feature information. SMS links users to email/Billing for the complete information. Daily expiry event keys distinguish the last ten calendar days. Active-student notices distinguish the five-day estimate from the final invoice. An outbox deduplicates events; email and SMS each reserve Review before sending. Uncertain sends are not automatically retried. Only configured sandbox users and phone can receive messages. Workers deliver new notices after transaction commit. The scheduler remains paused; manual --notices can exercise allowed events without enabling general jobs.

## Deployment/testing
Run scripts/deploy-signup-completion-sandbox.py from the sandbox bench. It checks source versions and test contacts, backs up privately, reloads only the two relevant DocTypes, builds assets and enables restricted sandbox notice creation. Restart the sandbox bench/workers and hard-refresh the page. Run existing role checks and native password-reset test. Run --notices only for authorized welcome/reminder tests; inspect inbox, SMS and outbox Review statuses. Browser OAuth, teacher/institute confirmation, notice delivery and payment settlement require live acceptance testing.

## Remaining decisions and blockers
The current architecture isolates one institute per Frappe site. A verified cross-site directory and scoped membership protocol are still required to list independent institutions globally. No invented institute entries were added. Confirmed policy: institute-confirmed teachers use the institute's active paid plan for assigned institute classes; independent teaching still requires personal access. Sandbox coverage checks active membership, verified institute profile, paid expiry and suspension on the server. Only explicitly scoped core classroom APIs are covered so far; other teaching modules remain denied until audited. Full institute dashboard acceptance is not yet verified. Provider profile review has not been bypassed. The five-day usage document remains an estimate because usage can continue until period end; a final invoice earlier requires a different billing cutoff rule.

CyberSource support activation was previously pending for case 002760691. Existing Sessions API implementation does not prove merchant activation or settlement. Still required: activation confirmation, sandbox merchant credentials/profile, successful and failed/cancelled payment tests, amount/currency/signature/replay checks against the deployed gateway, and verified paid access unlock. Production deployment and real customer sends remain unauthorized.

Coverage verification: 587 Python tests and 64 frontend tests passed; frontend production build passed. These are local checks, not live deployment or payment acceptance tests.
