# SISU overview, classroom and settlement update — 16 October 2026

## What changed
- Private student motto and personal milestone date, with a calendar-day countdown. The preview uses Navodya Galagoda; real accounts retain their own names.
- Original Lottie education illustration, bundled locally. Pause button, reduced-motion preference, off-screen suspension and hidden-tab suspension. Manrope is bundled locally.
- Role feature cards on sign-in and registration. Searchable Platform guide for Student, Teacher, Institute Admin and Super Admin.
- Classroom type (General, Theory, Revision, Paper, Practical, Fast Track) and batch year, alongside grade and teaching medium. Filters and per-class active enrolment counts.
- Teaching-hour overview now measures completed scheduled time within the current calendar month. It is not measured live attendance.
- Provider invoices show class charges and student/LMS-ID enrolments. Printing uses a standalone iframe document, avoiding dashboard chrome and popup blockers. Legacy invoices with incomplete snapshots show a reconciliation notice rather than inventing rows.
- Wallet & payouts is visible to providers. Bank, branch, holder and account number are submitted to the existing encrypted, finance-reviewed destination flow.

## Accepted payout policy
1. The class owner is the beneficiary. Institute classes pay the institute, even when another teacher teaches them. Independent classes pay their owner teacher.
2. Maximum two completed payouts per calendar month for each beneficiary wallet, INCLUDING the final-week monthly settlement. Pending and Processing requests reserve slots, including older outstanding requests. Rejected requests release their reservation.
3. During the last seven calendar days, the daily scheduler queues one remaining-balance settlement if there is positive available LKR balance, an approved Local Bank method and a free slot. It is idempotent per wallet/month. A full two-slot allocation means the balance remains for the following month.
4. The monthly sweep includes positive balances below the existing voluntary-withdrawal minimum. Manual requests retain the existing minimum policy (USD 20 equivalent; LKR uses a valid, dated finance reference rate).
5. No scheduler, export, preview button or wallet endpoint transfers money. Finance executes a transfer through the bank, then records its unique confirmed bank reference. Pending funds are reserved; completion consumes the reservation.
6. SISU package/enrolment fees remain separate provider invoices; they are not deducted from tuition.

## Deployment steps for the developer
1. Back up the production database and private files. Deploy the source from this project, not preview-dist.
2. In the Bench environment, run: bench --site YOUR_SITE migrate
   This installs IL Learning Preference, class_kind and batch_year and updates scheduler hooks.
3. Build frontend production assets using npm ci and npm run build in frontend, then run the normal Bench asset/deployment restart procedure. Never deploy preview.html or its fictional data as the live portal.
4. Set the site's timezone to Asia/Colombo and keep the scheduler and workers running. The calendar month and final seven days use the site's server datetime.
5. Provision exactly one enabled LKR settlement wallet per class beneficiary using the existing Super Admin wallet service. Institute ownership and independent teacher ownership must match the classroom.
6. Have the provider submit bank details in Wallet & payouts. Finance reviews and approves them. Do not use preview bank records for live operations.
7. Keep direct-to-provider collection mode until a bank/gateway agreement and verified integration exist. Only after the platform merchant settlement route is approved, set il_class_collection_mode to platform for NEW invoices. Under a monthly provider package, this freezes the full tuition amount to the correct owner's wallet with zero platform deduction.
8. Previously issued invoices keep their frozen financial identity. Do not rewrite them to reroute historical money. Void/reissue unpaid invoices through an authorised process when necessary.
9. A verified gateway callback may credit the frozen wallet once. A manual bank slip already paid to the provider must NOT credit the wallet again.
10. Review the monthly queue in the tenant owner Payouts tab. Export is a generic review CSV, not an HNB-certified upload. Confirm bank completion before marking Completed. The separate control plane does not automatically aggregate tenant payout queues.

## HNB and live acceptance remain outstanding
HNB merchant documentation has not been supplied. The HNB checkout endpoint remains disabled. No API keys, bank file format, webhook signature algorithm or transfer endpoint was invented. Obtain the bank's merchant documentation, implement and test authenticated checkout/callbacks/refunds, verify collected-funds routing, and complete bank sandbox acceptance before enabling live online collection.

Backend unit tests run against controlled Frappe doubles, not a running MariaDB site. On staging, verify row-lock behaviour with two simultaneous requests, scheduler-versus-manual races, duplicate callbacks, cross-month completion, third-payout rejection, refund-related holds, bank-method ownership, tenant separation, and full rollback after a failure. Verify the new private-goal record cannot be read through another user's account. Check invoice PDF page breaks with a real browser print destination and long learner names.

## Preview
http://127.0.0.1:5182/preview.html?preview=1#dashboard
Use the preview toolbar to switch roles. Goals, sample requests and bank reviews are fictional session data. The displayed GCE A/L example is a personal test target, not an official examination date.


## Verification completed locally
344 backend unit tests and 103 frontend checks passed. Production and preview builds passed. Student countdown saving, 390-pixel mobile layout, teacher monthly-hour label, user guide, role welcome cards, fictional wallet reservation and the standalone invoice preview were checked in the browser. Dependency audit reported zero vulnerabilities after the Vue 3.5 patch update. Existing large-bundle build warnings remain. Live Frappe/SQL locking, real bank transfers and actual PDF pagination still require the staging checks above.


## Overview, branding and payment periods — 16 October 2026

- The student progress hero precedes the personal milestone/motto card. The profile setup banner is removed; profile/settings remain available.
- The app footer credits **Powered by Icorenic Pvt Ltd**. Teen Academy remains only the fictional institute in the preview.
- Original classroom Lottie: a student at a laptop, teacher presenting, clock and plant. The visible pause control is removed as requested. Operating-system reduced motion, offscreen and hidden-tab suspension remain supported. Editable generator: `frontend/scripts/generate-education-motion.py`.
- Teacher/institute collection reports default to the current month and accept inclusive custom dates. Totals, channel breakdown, chart and CSV use the same range. Collections use the verified-access record creation timestamp; teaching hours remain current calendar month.
- Student/provider class invoice history uses a server-paginated report, with complete period totals separated by currency. Its dates refer explicitly to invoice due dates, not bank settlement dates. Cancelled/failed invoices are excluded from outstanding totals.
- The new `institute_lms.payment_reports.history` endpoint scopes students to their own invoices and providers to permitted classrooms in their institute. Existing bank-slip approval and payment actions are preserved.
- Validation: 106 frontend tests and 346 backend unit tests passed. Preview and production builds passed (existing bundle-size warning). Desktop and 390px mobile checks: progress ordering, removed banner/pause control, custom date totals, empty periods and no page overflow.
- The preview uses fictional data. The live Frappe/MariaDB report queries still require staging validation after deploying the Python files; no live bank integration or settlement was tested here.

- Follow-up: exam countdown redesigned as a blush stationery card with locally bundled Caveat handwriting, separate day digits, encouragement and an editable personal motto/date. Existing countdown calculation is retained, including exam-day and past-date states. Phone overflow check passed.

- Final countdown revision: a compact lavender/purple UI card replaces the poster treatment. Students can remove it with the corner control or use Personalise my overview to enable/disable it. Removing it preserves the chosen date and motto. Visibility is saved per authenticated user (`IL Learning Preference.hide_countdown`) and in the local preview. Deployers must run the normal site migration (`bench --site SITE migrate`) to add this Check field before enabling the updated portal.
