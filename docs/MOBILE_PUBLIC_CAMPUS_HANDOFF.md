# Mobile developer handoff — public shared campus (2026-11-02)

Start here. This document supersedes the isolated-site assumptions in MOBILE_API_HANDOFF.md for the public deployment. Read that document for the existing PKCE implementation, then verify the shared-campus limitations below before implementing navigation.

## Hosts and release status

- Public website: https://www.sisuacademylk.com/
- Public LMS: https://www.sisuacademylk.com/campus
- Public API base: https://www.sisuacademylk.com/api/method/
- Owner administration: https://platform.sisuacademylk.com/campus (separate database and session).
- Source branch: mergetharuka. GitHub source publication does not deploy to the server.
- Payments paused; WhatsApp unconfigured. Never present a working checkout or WhatsApp action based solely on a package feature.
- Owner registration database mutations passed a real rollback test. Public signup persistence passed synthetic-proof sandbox tests. Email/SMS standalone test delivery was confirmed, but full public browser signup/Google callback and role acceptance remain incomplete.
- Demo seed script is prepared, NOT confirmed run. It creates labelled fictional public content with a 30-day demo-only entitlement, disabled fixture identities, and no automatic student enrollment.

## Authentication and transport

Success envelope: `{"message": <result>}`. Always inspect HTTP status plus `exc`/`exc_type`; errors may contain `_server_messages` (JSON-encoded array of JSON strings). Strip HTML before display. Never show raw traceback, OTP, tokens, or provider credentials.

Browser requests use the site session cookie and `X-Frappe-CSRF-Token` for authenticated POST. `portal_session.current` returns the session CSRF token. Do not copy cookies between the public and platform domains. Native clients must use the existing system-browser PKCE flow, not an embedded Google password collector. See mobile_auth.py and the generated endpoint index for exact methods/arguments. `mobile_auth.exchange` returns `{access_token,token_type:"Sisu",expires_at,site}`; send `Authorization: Sisu <access_token>` (not Bearer), never mix it with browser cookies, and keep tokens in OS secure storage and bind them to the issuing host. The native shared-campus selection/session behavior still needs a real-device acceptance test; do not assume legacy mobile_api.current subscription handling supports a student with no institute.

Never ship a Frappe administrator API key. Never add client-selected roles, verification flags or institute headers to bypass server checks.

## Signup contract (all methods below prefixed institute_lms.)

1. GET `portal_policy.public` -> `{privacy_policy_url,privacy_policy_version,provider_applications_enabled,google_available,self_signup_enabled}`.
2. POST `registration.self_start`, JSON `{data:{kind,first_name,last_name,email,phone,username,country,timezone,privacy_accepted:true,privacy_policy_version,...}}` -> `{challenge:"opaque-token"}`. Sends email code. Phone is E.164, e.g. +94 followed by nine digits. Username: 3–30 lowercase letters/digits/underscore, starting with a letter.
   - Student: `kind:"Student"`, required `grade`.
   - Teacher: `kind:"Individual Teacher"`, required `subject`.
   - Institute: `kind:"Institute"`, required `organization`, `job`, `backup_name`, `backup_email` (different from account email).
   - Optional strings: `website` (HTTPS), `qualifications`, `bio`.
   - Use current policy version; never silently accept policy on behalf of users.
3. POST `registration.self_verify` `{token:challenge,channel:"email",code:"six digits"}` -> `{verified:true}`.
4. POST `registration.self_phone` `{token:challenge}` -> `{sent:true}`. Requests SMS; a successful request is not evidence of handset delivery.
5. POST `registration.self_verify` `{token:challenge,channel:"phone",code:"six digits"}` -> `{verified:true}`.
6. POST `registration.self_complete` `{token:challenge,password,confirmation}` -> `{created:true,message:"Your account is ready. Sign in to your SISU space."}`. Password 12–128 characters. Both proofs required. Return to login; Google-created signup must end the signup session before ordinary login.

Codes expire after ten minutes and allow five verification attempts. Signup challenge expires after 30 minutes. Respect the server's top-level `retry_after_seconds` and display MM:SS; don't reset the countdown on rerender or retry automatically. Signup rate-limit window is five minutes, with a separate 60-second resend cooldown. A timeout/uncertain SMS response is NOT permission for an automatic resend.

POST `portal_policy.google_start` `{signup:1}` -> `{url}` for signup, `{signup:0}` for login. Open returned authorization URL using the supported browser flow. The callback is server-managed. Google alone does not prove phone ownership or grant provider privileges.

## Session and routing

GET `portal_session.current`:
- Guest: `{authenticated:false}`.
- Public account without selected institute: `{authenticated:true,role:"Campus",shared_campus:true,member:null,onboarding_kind:"Student"|"Teacher"|"Institute",user,csrf_token}`.
- Selected member: role is `Student`, `Teacher` or `Admin`, with `member` and shared_campus.
- Owner: role `Super Admin`, `control_plane:true` on platform site.

GET `registration.account_status` reports actual verification status. Students land on the established dashboard and complete required verification. Providers remain behind setup/payment or institute-approval gates. A pending Teacher profile is NOT permission to teach. A local test account does not imply a live account exists.

## Discovery, following and enrollment

- GET `campus_join.directory` `{query:"",page:0}` -> `{institutes:[{name,display_name}],has_more}`. No selected institute required.
- GET `campus_join.details` -> `{first_name,last_name,email,phone,phone_verified}` for a verified student.
- POST `campus_join.register_student` `{profile:"provider-profile-id",language:"en"}` -> `{registered:true,created,student_number,institute,institute_title,message}`. Requires verified student/phone. Idempotent repeat returns the same membership ID. Registration does not enroll in classes.
- POST `campus_join.register_teacher` `{profile}` -> analogous registration result with `institute:null`; only independent teachers qualify.
- GET `campus_context.choices` -> `{institutes:[...],selected:null|institute-id}`.
- POST `campus_context.select` `{institute}` -> `{selected,role,reload_required:true}`. POST `campus_context.clear` `{}` -> `{selected:null,reload_required:true}`. Reload session and institute data; clear cached previous-institute content.
- GET `profiles.follow_status` `{profiles:JSON.stringify([ids])}` -> `[{name,profile}]` for active follows. At most 24 profile IDs.
- GET `profiles.followed_free_classes` `{page:0}` -> public cards `[{name,title,subject,cover_image,provider,provider_name,provider_kind}]`. Following is not an access grant.
- Selected-institute catalogue `catalog.detail` `{profile,page}` -> `{profile,classes,teachers,class_count,teacher_count,has_more}`.
- POST `catalog.join_class` `{classroom}` enrolls current student subject to server policy. Consult source response and then reload detail; never infer paid access from enrollment.
- `api.classroom_detail` `{name,page}` provides authorized detail; protected materials must use `materials.content`, not direct file URLs.

For exact parameter defaults, allowed HTTP methods and source locations across ALL whitelisted endpoints, see MOBILE_ENDPOINT_INDEX.md. Unspecified whitelist methods are marked as framework-default; use the existing client call and confirm with integration tests. It is an index, not a claim every endpoint has passed live acceptance.

## Test identities and outstanding acceptance

- platform: tharukakarunarathne60@gmail.com and gro4celk@gmail.com both enabled delegated owners, neither primary. Google configured, actual device login test still required.
- public: sisu.student.test@gmail.com exists; last inspection showed no profile or verification. Finish its Google signup normally.
- public teacher: sisu.student.test+teacher@gmail.com absent at last inspection. create-public-test-teacher.py uses real codes/password entry; earlier lowercase confirmation cancelled before delivery. Do not assume created until success output.
- Public demo deployment: run scripts/seed-public-demo-content.py as sisu; then verify new-student discovery, follow, institute registration, selection, free enrollment and paid-class denial. No real paid grants or automatic enrollments.
- Test on Android/iOS: Google callback, PKCE/state mismatch/replay/expiry, logout/revocation, missing/expired OTP, 05:00 countdown, duplicate registration, no-institute student, pending teacher, approved teacher, pending institute, revoked membership, cross-institute file denial, disabled payments.

## Configuration to share with the mobile developer

Share repository access, public/staging base URLs, approved test credentials through a private password manager, Android package/application ID, iOS bundle ID, signing certificate SHA fingerprints, and agreed callback/app-link URLs. If native Google/Firebase integration is selected, provide platform-specific OAuth CLIENT IDs and the relevant Firebase client configuration; restrict client API keys and configure app verification appropriately. Existing web OAuth alone is not proof native callbacks are configured.

Do NOT share server SSH/root access, database passwords, Frappe encryption keys, SMTP passwords, Notify.lk tokens, Google client secrets/service-account keys, LiveKit signing secrets, payment secrets, or WhatsApp tokens for inclusion in the app. These belong on the backend. Any needed backend access should be separately scoped. Do not put passwords or production service credentials in GitHub.

## Student demo and password reset update (2026-11-02)

Deployment: `scripts/deploy-student-round2.py` installs the reviewed archive and seeds clearly labelled fictional providers/classes/news. Payments and WhatsApp stay disabled. Demo identities cannot sign in. Following a provider reveals its published cards; following an institute also includes its active teachers. Registration remains separate and creates the normal student membership/number. The practice key `SISU-DEMO` unlocks only seeded practice content for seven days, not real paid classes or private materials.

All methods below use `/api/method/institute_lms.<module>.<method>` and Frappe's `{"message": ...}` response envelope. Authenticated browser requests use the session cookie and CSRF header for POST. Never embed service credentials in a mobile app.

| Method | Request | Response message |
|---|---|---|
| GET profiles.followed_classes | page=0 | Array of published class cards with name, title, fee, fee_mode, provider, demo and demo_unlocked where applicable |
| POST demo_learning.open_practice | classroom, enrollment_key (locked demo only) | Demo lesson content and notice; requires a verified student following the provider |
| POST password_reset.start | none | token, email, expires_in (600 seconds) |
| GET password_reset.status | token | verified, expires_in |
| POST password_reset.confirm | token, proof from email fragment | verified: true |
| POST password_reset.finish | token, password, confirmation | changed: true, sign_in_required: true |

Password reset is a website-session flow on shared campus: start/status/finish are bound to the same signed-in user and session. The email confirmation page can be opened in another tab. The proof expires in ten minutes, is single-use for changing the password, and is never a replacement login token. Successful reset invalidates sessions and queues security email and SMS where verified delivery details exist. Mobile clients should open this website flow until a separately reviewed native reset flow exists.

Personal profile images use the existing profiles.upload_image endpoint. Shared-campus profile save/upload does not require institute membership. Existing file type, size and owner checks remain enforced.

Validation: 790 backend tests and 89 frontend tests passed, plus mocked-browser follow, registration, practice unlock, profile upload/save and password-reset checks. These are not evidence of live email/SMS delivery or persisted live uploads. After deployment, check those using the authorized test account, then check institute switching and registration on the live demo provider.


## Student follow, notification and bank-key update (2026-11-03)

- GET registration.account_unread -> {count}; GET account_notifications includes read. POST registration.read_account_notice {name} marks only the current user's own account receipt. Other workspace notifications keep their existing inbox/read endpoints.
- Institute/provider registration now follows that provider. campus_context.choices returns institute-specific student numbers; select/clear remain membership-validated. Selected-institute provider discovery and news are scoped to that institute.
- GET class_keys.bank_details {classroom} -> {instructions,recipient,fee,classroom}. POST class_keys.save_bank_details {classroom,instructions} is restricted to the recipient (institute administrator or teacher owning the class). These are tuition instructions, separate from platform subscription payments.
- Public shared-campus bank approval now creates IL Paid Access with status Awaiting key, not Active. A random key is sent through the existing account receipt email/SMS jobs. POST class_keys.redeem {classroom,key} requires the same student, institute, paid invoice and unexpired access period. Redemption is row-locked, changes access to Active and clears the stored key hash. Existing active grants are preserved. Non-shared sites retain the previous approval behavior.
- commercial.upload_proof accepts PDF, PNG, JPEG, DOC, DOCX and UTF-8 TXT up to 5 MB. Private proof ownership, duplicate checks and attachment downloads remain enforced. Executables and arbitrary file types are not accepted.
- demo_learning.enter_classroom {classroom,enrollment_key} allows registered students into the actual seeded demo institute classroom using temporary demo access. SISU-DEMO remains a shared practice key, not a production enrollment key or proof of payment. Independent demo preview cards remain previews unless the student has the required workspace membership.
- configure-public-livekit.py verifies and copies the existing staging LiveKit settings to the public site without creating rooms. prepare-demo-classroom-host.py requires the named test teacher to already be enabled and verified before assigning demo institute rooms. These scripts do not establish a successful live media test.

Validation: 795 backend tests, frontend unit checks, mocked browser notification/selector and bank-details/key redemption checks. Production migration, real approval receipts, teacher hosting and live video still require server execution and two-account acceptance. The independent teacher's public registration alone does not yet provide a standalone billing workspace; do not claim that path is end-to-end verified.


## Live classroom update — 2026-11-04 (deployment pending)

Teacher and student joining, camera, microphone, screen sharing, recording and teacher playback were confirmed manually on staging. The following patch adds student media permissions, session chat and fixes reviewed recording publication; its two-device browser acceptance remains pending.

All calls require the authenticated site's session and normal CSRF header for POST. API results are wrapped in `message`. These endpoints do not accept client-provided roles or author identities.

- POST `institute_lms.live_classes.join`, body `{"name":"LIVE_ROOM_ID"}`: returns `url`, short-lived `token`, `expires_in`, `name`, `can_control`, `can_publish`, `host_identity`, `recording_status`. Connect using the LiveKit SDK. Start camera/microphone off; require an explicit user action to activate them. Enrolled students may publish camera/microphone, but cannot screen-share or administer/record the room through their token. Hosts can screen-share. Never log tokens.
- GET `institute_lms.live_classes.chat?name=LIVE_ROOM_ID`: returns `{"messages":[{"id":"...","author":"Display name","host":false,"text":"Hello","sent_at":1790000000.0}]}`. Poll every three seconds only while connected. Render text as plain text.
- POST `institute_lms.live_classes.chat`, body `{"name":"LIVE_ROOM_ID","text":"Hello"}`: same response. Maximum 1000 characters, one message per participant per two seconds. Server assigns name/host label after classroom authorization. Last 100 messages retained temporarily in cache for two hours after the latest message; no permanent transcript. Ended sessions reject chat access.
- POST `institute_lms.live_classes.publish_recording`, body `{"name":"LIVE_ROOM_ID","reviewed":true}`: returns `{"published":true}`. Only the controlling teacher may publish a Ready recording. Ask for review confirmation first.
- POST `institute_lms.live_classes.recording`, body `{"name":"LIVE_ROOM_ID"}`: returns protected `url`, `expires_in`, `title`. Student playback requires classroom access and publication. Never expose storage credentials. Unpublished recordings are teacher drafts; no lecture-product creation is required.


## Student acceptance and enrollment update — 2026-11-05

Branch: `mergetharuka`. The user confirmed staging student classroom, material/assignment/quiz/notice flows, live participation and recording playback. The user also confirmed the bank-slip flow: upload, teacher review, approval visible to student, personal key redemption, and classroom access. These are user-reported browser results, not production delivery certification. Public and staging paid-access schema repair both reported PASS. Public SMS delivery remains blocked by exhausted credits; Cybersource production checkout and WhatsApp remain disabled. Teacher classroom image serving remains deferred/unverified on public.

Manual tuition is independent of Cybersource. Student UI hides invoice generation; invoice IDs remain server-owned accounting references. Class-fee navigation preselects the classroom and its existing unpaid invoice, displays the fixed amount and provider bank instructions, and accepts the reference/date/proof. Approval alone grants Awaiting key, not Active access.

- GET `institute_lms.class_keys.key_status?classroom=ID` -> `{"payment_approved":true,"key_valid_for_seconds":900}`.
- POST `institute_lms.class_keys.resend` with `{"classroom":"ID"}` -> `{"queued":true,"expires_in_seconds":900,"retry_after_seconds":60}`. Requires the signed-in student's paid invoice and Awaiting key access. Rotates the stored hash, invalidating the previous key. No new charge. Throttled to one resend per minute.
- POST `institute_lms.class_keys.redeem` with `{"classroom":"ID","key":"PERSONAL_KEY"}` -> `{"enrolled":true}`. Key is student/class-bound, single-use, and expires after 15 minutes. Expiry does not undo the approved payment. Errors use the normal Frappe error envelope.
- GET `institute_lms.class_keys.classroom_bank_settings` with optional classroom -> `instructions`, `editable`, `owner_type`. Teacher-owned classes use their owner account; institute-owned classes use the institute account. Only that independent owner or institute admin may modify instructions. Create/edit accepts optional `bank_instructions` in the classroom data; saves transactionally with the classroom.
- GET `institute_lms.registration.account_notifications` now also returns `email_content` for the current user's SISU receipts. Render as plain text, never executable HTML. Staging enrollment keys are delivered in-app only by the account receipt queue; public queues email/SMS too. Do not log key contents.

Full local validation: 807 Python tests (`python -X utf8 -m unittest discover -s tests`), 93 frontend tests (`npm test`), production Vite build. Public deployment requires the consolidated release output and read-only public check; no claim that all role testing is complete.
