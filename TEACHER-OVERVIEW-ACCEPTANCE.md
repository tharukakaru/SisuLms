# Teacher entry and overview — 2026-11-05

## Public browser observed
- Public teacher SISU-TC-000003 selected its independent workspace using the deployed chooser.
- Study Room absent from teacher sidebar.
- Overview matches staging component layout; public values are 2 classrooms, 1 learner, LKR 100 labelled test collection.
- Today schedule filter and View full schedule navigation passed.
- Create personal class opens the editable form; cancelled without saving.
- Institute requests expands membership management; no request submitted.
- Apply dates refreshes collection data successfully.
- Plan & monthly invoice opens billing; public online payments remain unavailable.
- Bank slip reviews opens review screen with Pending (0), Paid LKR 100 and the existing test invoice.

## Deployed teacher overview
sisu-teacher-overview.tgz plus deploy-teacher-overview.py.
- Chooser stays within overview once a workspace is selected.
- Institute teacher presentation comes from server bootstrap workspace profile context, not selected login tile.
- Institute workspace omits personal subscription/wallet sidebar, personal class creation, financial report and bank review overview shortcuts; independent teachers retain them.
- Financial report failures no longer remove teaching overview.
- Teacher discovery does not offer student registration buttons.
- Role-appropriate report wording and teaching-options back link.

## Checks and limits
95 frontend tests passed including independent/institute navigation matrix. Changed Vue scripts/templates compiled; Python syntax checked.
Earlier intermediate full build passed. Final full build failed twice with host memory-allocation errors, not a reported source compilation error. Server deployment must build successfully; it backs up and restores on build failure.
check-public-teacher-overview.py exercises named independent test teacher through both request guards, rolls back, and does not send messages.
Independent bootstrap, teaching overview and metrics passed both server guards after the CLI check received an in-memory CSRF token. Institute teacher browser acceptance, membership submission/approval, paid-institute coverage and online payments are NOT confirmed. Existing institute coverage is gated to hnb-checkout.localhost in institute_coverage.enabled; this UI patch deliberately does not enable or bypass subscription entitlements.
Do not claim all teacher workflows or institute subscription coverage passed.

## Public teacher audit — 2026-11-05
Observed as SISU-TC-000003 in public browser:
- Overview loads two classes, one learner, LKR100 approved test collection.
- Profile null-social-links render exception reproduced in browser logs. Fixed by normalizing every editable social field. Deployment/retest pending.
- Provider tools Expenses, Operators, Content controls, Connections load. No access grants or settings changes submitted.
- Wallet bank reviews load; payout wallet absent, explicitly reported by UI. No payout requested.
- Free classroom opens. Attendance empty state, quiz editor and recording empty state load. Tute delivery correctly displays Gold/Platinum restriction. No assessment published this turn.
- Settings loaded; corrected fake example IDs and duplicate subject-only class selector labels.
- News publish form opens and cancels; no announcement sent.
- Institute discovery/profile opens; no membership request sent.
- Notifications visibly show pending/approved test-payment history with unread marks.
- Guide corrected outdated student subscription/invoice instructions.
- Independent workspace/help wording and payment report caption/plural corrected.

Prepared sisu-teacher-audit.tgz with six reviewed source files and conflict-checked build/restore deployment script. 97 frontend tests pass, including null/legacy social editing regression. Vue compiler and Python syntax checks pass. Full server build and live retest pending.

Prepared prepare-public-institute-teacher.py, dependent on prepare-public-test-teacher.py helpers: labelled test-only Teacher in existing SISUDEMO institute, new private assigned free classroom, no admin permissions, no messages, no payment configuration changes. Password entered privately. Does not prove institute coverage after personal trial expiry; existing institute_coverage site restriction still requires implementation/testing. Script not executed on server yet.

This is a navigation/control audit, NOT completion of every create/edit/upload/delete workflow or end-to-end teacher acceptance. Remaining: deployment retest, profile save/uploads with verified contact, assessment/material lifecycle, live media two-device check, institute role and subscription coverage, configured payout/external-service flows.


## Institute teacher public check — 2026-11-05
Confirmed SISU-TC-000004 in SISUDEMO: assigned classroom shown, no personal subscription/wallet/create action in overview; Teaching only denies classroom edit/delete. Saved labelled test lesson for 2026-11-06 16:00–16:30 Asia/Colombo and observed it in My schedule. Persistent test session retained.
Found personal upgrade and bank-management entry points in Provider tools/Class fees. Prepared sisu-institute-teacher-ui.tgz to hide these routes, direct bookmarks, classroom Payments tab and personal WhatsApp shortcut in institute teacher context. No backend permission changes. 98 frontend tests passed; both changed Vue SFCs compiled. Server deployment and post-deploy browser acceptance pending.
Institute-sponsored access after personal trial expiry remains unresolved: coverage feature currently restricted to hnb-checkout.localhost. Fresh test trial is not evidence of institute-paid coverage. No real payments or messages sent in this check.

## Independent teacher user acceptance — 2026-11-06
User reports Overview, My classrooms, My schedule, Teachers & institutes, Class fees,
News feed, My profile and notifications working. Keep these flows unchanged.
Subscription and wallet/payout gateway testing remains on hold pending support.
Reported issues: expense save/date-filter visibility and Settings Remove from class.
Prepared sisu-teacher-expenses-controls.tgz: Sri Lankan business-date validation,
show newly saved expense within register date range, scroll/focus confirmation form,
inline confirmation errors and correct removal success message.
Local Python syntax/date-boundary/amount checks and two Vue component compilations passed.
Exact live failure not yet reproduced with browser tools. Deployment and rollback-only
server check scripts prepared; do not claim public end-to-end acceptance yet.
Next role after these fixes: institute teacher user acceptance, then institute admin.


2026-11-06 institute teacher controls (prepared, not yet deployed):
- User accepts independent teacher fixes; institute teacher remaining reported defects addressed locally.
- Assigned teaching-only quiz access uses teaching rights on backend and quiz button presentation.
- Actual classroom modal handler tests cover announcement/session/material save, cancel, failure and standalone scheduling.
- New IL Classroom Handover retains assignment pending admin decision. Approval requires a different approved teacher; rejection retains current assignment. Programme module assignment is updated in the same transaction.
- Admin overview/team and teacher overview list pending requests. Membership stays active; class handover does not blacklist future affiliation.
- Sidebar already renders own saved social links, not institute profile socials.
- Institute plan projection reads current institute subscription, exposes only plan/state/features; no billing controls or other plan catalog.
- Local: 35 Python tests, 16 frontend tests, production build and package hash verification passed.
- Server: pending deploy-institute-teacher-controls.py, named fixture restoration and rollback-only check-public-institute-teacher-controls.py.
- Browser: pending user acceptance. No payment testing or credentials changed.

2026-11-06 deployment follow-up: user reports institute-teacher controls deployed,
workers restarted and fp20kd7lgd restored. Server passed teaching-only quiz creation,
own-profile projection and read-only institute plan. Handover admin checks stopped at
campus require_user because checker selected an ineligible admin. Demo seed creates a
disabled display admin. Checker revised to prefer enabled admins, otherwise temporarily
activate only the exact demo admin inside rollback-only transaction. Rerun pending;
admin approval/rejection and browser acceptance are NOT yet verified.

2026-11-06 confirmed acceptance and next role:
- Institute teacher: server rollback checks PASS for quiz creation, own-profile projection,
  institute plan, leave request retention/duplicates, teacher self-approval denial, admin
  rejection, replacement requirement, approval/access transfer and preserved membership.
- User explicitly confirms all institute-teacher browser checks work. Role accepted.
- Independent teacher accepted except subscription and wallet/payout payment integration
  and end-to-end testing, held until bank support replies. Do not retest accepted pages.
- Active phase: INSTITUTE ADMIN. User will test admin flows; fix reported defects, then
  platform/super admin, requested UI polish and remaining launch work.
- Demo admin activation was transaction-only and rolled back; do not present it as a
  usable enabled login or silently enable/change an account.
- Separate unresolved boundary: institute-sponsored coverage after personal trial expiry
  is not proven by the current active-trial teacher acceptance.

2026-11-06 release synchronization:
- User confirms institute-admin test account READY. Portal Admin routing, scoped SISUDEMO
  membership, institute profile and existing subscription access passed on server.
- Teacher-role source and compiled assets committed locally after deployed teacher
  packages and user browser acceptance. GitHub push pending; no payment activation.
- Release verification: 830 Python tests (UTF-8 mode), 104 frontend tests, static check
  of 609 Python sources and 125 JSON documents passed; production build previously passed.
- Institute-teacher functionality accepted; independent teacher functionality accepted
  except subscription and wallet/payout gateway integration/testing. Institute-sponsored
  access after personal trial expiry remains a separate unverified entitlement boundary.
- Current task continues with institute admin browser audit. No passwords recorded.

GitHub sync blocked: local commits 5499c7d (existing checkout display fix) and e0c1fdf
(accepted teacher workflows/assets/tests) are ready on mergetharuka. Git push could not
start the Windows credential helper; direct credential retrieval was unavailable.
Connected GitHub create-tree returned 403 Resource not accessible by integration.
Remote remains d093e39. User can run git push origin mergetharuka in their PowerShell.
No GitHub update or new deployment was performed in this synchronization turn.
