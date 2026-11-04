# Public student acceptance — 5 November 2026

Evidence: logged-in public student browser, following public-student-connect deployment.

| Area | Observed result | Remaining check |
|---|---|---|
| Classrooms | Six followed demo cards load, no institute error | Full classroom entry blocked by omitted DemoLesson deployment |
| Class fees | Slip form and status tabs load, no institute error | No unpaid public invoice on this account; do not fabricate payment |
| Schedule | Sidebar visible; November/December navigation works | No public enrolled sessions available to join |
| Profile | Saved student ID/photo and private details load | New upload/save not repeated |
| Settings | Verified mobile, ID, reset and deletion controls load | No password change/deletion performed |
| Notifications | Unread indicator and dropdown visible | Notification contents need visual verification |
| Full classroom | Updated local demo entry was not deployed | Included in new 37-file release |
| Live media/chat/recordings | Previously user-tested on staging | Public live host/session and content required; not yet passed |
| Materials/assignments/quizzes | Previously user-tested on staging | Public classroom entry/content acceptance pending |

Prepared sisu-public-student-complete.tgz and matching deployment/check scripts. Includes omitted round-two/round-three components plus consolidated release and public bridge. Hash preflight rejects unknown server versions. Does not seed content, send messages, settle payments or change gateway settings. 812 backend and 93 frontend tests passed for current source; frontend build passed. This is not a claim of end-to-end public acceptance.

## Consolidated deployment confirmed
User supplied successful deployment output: all 37 source files match, and choices/classes/billing/schedule pass both guards with no institute selected.
Browser reloaded after deployment. Confirmed: followed news cards; classroom cards; updated DemoLesson View classroom button; Close lesson works; Overview institute selector renders None and correctly reports no memberships; saved exam countdown and motto load; provider directory and prefilled institute registration form load.
Full classroom entry attempted: server rejected because this public student has not joined the demo institute. No membership bypass or paid access granted. Registration confirmation pending to use existing name/email/verified phone for the demo institute. Public live session/recording/content and payment transaction acceptance remains pending.

## Public registration and full classroom browser check
User explicitly approved demo registration with existing account details. Registration succeeded: ST-SISUDEMO-00001. Switched into demo institute; overview selector shows the institute and student number. Entered free mathematics classroom 1f6qq49hvr through View classroom. Full classroom opened successfully. Sessions, Recordings, Materials, Papers/assignments/quizzes tabs are present. Live session list and assessment list load with empty states; materials empty. Public demo has no populated live session/recording/coursework for actual media/submission acceptance. No real payment approved, password changed, or account deleted. Delivery of registration messages not independently confirmed.

## Public practice content follow-up — 2026-11-05

Prepared locally, not yet executed on server:
- `scripts/seed-public-classroom-practice.py`: existing SISUDEMO free mathematics classroom only; private TXT handout, written assignment, two-question quiz, and existing SISU sample animation through protected recording playback. Disabled fixture identities remain disabled. No financial records or notifications.
- `scripts/test-public-bank-enrollment-transaction.py`: uncommittable public-site transaction covering automatic invoice, uploaded slip/Pending, forbidden student approval, provider approval/Awaiting key, foreign and expired key rejection, resend and one-time redemption. Requires existing registered test student. All test financial records and temporary identity changes roll back. Does not prove browser teacher authentication or SMS/email delivery.
- Unlocked registered demo cards now enter the classroom using “View classroom”; locked demo practice remains explicitly separate from paid enrollment.

Validation: Python syntax checks; 50 enrollment/commercial/quiz tests; 23 uploaded-paper tests; 93 frontend tests; production build passed. Server fixture execution, rollback API test result, and browser playback/download/submission acceptance remain pending. No claim that these new fixtures are already live.

### Follow-up after public deployment / seed preflight failure
Browser checked directly: updated View classroom button enters the full classroom; Materials, Recordings and Papers/quizzes load without visible errors but remain empty. Class fees loads the bank-slip form and status tabs; no payable class/invoice exists for this student. This is not a completed payment-flow acceptance.
The original seed stopped before writing content and prevented the chained bank test. Revised seed reports video configuration as non-secret booleans/missing field names and allows non-video fixtures to proceed when media configuration is incomplete. Precise stages and sanitized stack locations added. Revised scripts compile; awaiting server execution. Recording playback remains blocked/unverified, not passed.

### Public upload configuration blocker
Server seed failed in storage.before_write -> saas.quota -> saas.state at missing tenant check. Public private-video bucket/region/access key/secret, adapter and allowed hosts are also absent. No content or bank-test success claimed. Added read-only public/staging storage inspection and explicit seed allocation preflight. Seed operator upload now scopes metadata to the validated SISUDEMO institute without disabling quota hooks. Infrastructure settings still require inspection; no credentials or configuration changed locally or remotely.

### Prepared infrastructure correction
Public inspection confirmed no tenant policy, standalone allocation, private-video or recording-storage settings; staging has tenant policy and complete media settings. Added shared-campus support to account_storage.configured without turning on retired usage billing. Explicit positive allocation remains mandatory and tenant/control-plane boundaries remain unchanged. Six focused quota/profile-storage tests pass.
Prepared configure-public-learning-storage.py: public 5 GiB infrastructure ceiling, optional explicit --reuse-staging-media server-local copy of protected media settings, strict existing-value/source checks and private rollback backups. Requires public and staging LiveKit service identity to match before reusing recording storage. Payments and WhatsApp untouched. Script compiles; not run remotely yet. Updated future consolidated archive to include account_storage.py (38 source files).

### Storage configured; seed attachment-event correction
User server output confirms the 5 GiB allocation and protected media configuration were installed and processes restarted. Seed then rolled back at the handout attachment because its internal Frappe Comment realtime notification was rejected by the CLI suppression guard. Changed both seed and rollback test realtime handlers to suppress (not dispatch) all internal events; email/job guards remain enforced. Syntax and guard checks pass. Content playback, assessment submissions and bank-flow acceptance still await successful server execution.

## Public browser acceptance — 2026-11-05

Successful seed and rollback transaction output supplied by user. The handout, written assignment, quiz and protected sample animation are now saved in classroom 1f6qq49hvr.

Direct checks in the logged-in public student browser:
- Materials: Download saved sisu-demo-algebra.txt; inspected the downloaded file and confirmed the expected algebra practice content.
- Recordings: published sample animation loaded (readyState 4, 768px video, duration 5.166667 seconds), played and advanced to 3.9012 seconds without a video error. This verifies protected playback, not public live recording capture.
- Quiz: submitted the two correct demo answers through review/submit; displayed Quiz submitted, 2 / 2, 100%; list then offered View result.
- Assignment: started the timed demo paper, entered a labelled test explanation, submitted; displayed Submitted for teacher marking and Your submission - Submitted. Manual teacher grading remains separate.
- No red error appeared during these checks. Demo assessment submissions intentionally remain on the test student's account.

Server rollback test passed automatic LKR 100 invoice creation, uploaded slip Pending, denial of student self-approval, provider approval and student history, personal-key gate, rejection of other students/expired/used keys, resend and one-time redemption. Financial/test access records were rolled back. This does not establish public teacher-browser approval or SMS/email delivery, and no real bank transfer was performed.

Outstanding housekeeping: test reported temporary proof cleanup needs review for File ff14020fcb. Database rollback succeeded, but physical proof-file cleanup is not confirmed. Do not describe this warning as resolved.

## Teacher acceptance follow-up

Prepared prepare-public-test-teacher.py for the explicitly authorized public alias. Password is entered with getpass and must meet the existing 12-character minimum. Creates only an operator-approved test provider, its isolated workspace and teacher-owned free/paid test classrooms. Does not assert email/phone verification, send OTPs/messages, grant platform roles or alter gateway settings. Server execution and browser login/approval remain pending.

Rollback proof cleanup now runs after DB rollback, checks the exact per-run payload and private path, and refuses removal while File/Stored Object references remain. cleanup-public-test-proofs.py quarantines only unreferenced bank-proof TXT files matching the exact rollback-test body pattern; no permanent deletion. Existing server orphan cleanup not yet confirmed.

Validation: all three scripts parse; 5 public student routing tests and 3 shared storage tests pass; git diff --check passes. Direct SSH BatchMode access unavailable, so setup requires the operator's interactive terminal.
