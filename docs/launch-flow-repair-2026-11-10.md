# Production launch-flow repair

Based on production source 5de5f5f, not the undeployed merge 8c0d8f4. Includes the profile restoration patch and accepts its exact hashes.

Changes: compact approved-workspace selection, provider-only marketing signup, existing-account sign-in recovery, opt-in normal student password authentication, published LKR plan pricing, shared plan cards, explicit trial-to-paid invoice creation without payment activation, bank-details popup, preferred invoice selection and profile image fitting.

Validation: 881 Python tests, 116 frontend tests, production build. Mocked browser checks cover student bank details to prefilled slip form, Teacher/Admin plan selection to unpaid checkout, provider signup entry, profile photos/social links and navigation. Actual signup email/SMS, real authentication, upload/review and gateway acceptance are not claimed by these mocks.

Deployment: deploy-launch-flows.py; activate-launch-flows.py; restart web and workers; check-launch-flows.py; activate-launch-flows-website.py as root. Activation changes only il_four_plan_lkr_enabled and il_student_password_login_enabled for public/Teen; no gateway holds, queues, passwords or existing invoices are changed. Private backups are retained by the installers.

Existing accounts must sign in or reset their passwords; the duplicate-account signup guard stays intact. Student payments remain bank-slip only. Checkout requires an unpaid provider invoice and configured gateway availability. A demo or already-paid class may have no outstanding invoice; check output lists the named test student's recent invoice statuses.
