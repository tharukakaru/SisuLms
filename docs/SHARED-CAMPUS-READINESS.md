# General SISU campus — implementation status

Target: www.sisuacademylk.com/campus, separate from the platform control plane and existing client sites.

The marketing website is staged, not published. Existing client databases remain separate. They must not be presented as sharing accounts with the new campus until an explicit account/membership migration or federation is implemented.

## Implementation and deployment scope

`campus_context.py` provides an opt-in server-side institute selection boundary. It accepts only active memberships for the authenticated user and rechecks them on every context resolution. Roles are read from membership records. Revoked memberships cannot continue using a selected institute. The feature defaults off and cannot run on a control-plane site. The full 708-test Python suite, frontend tests and production frontend build pass. These are automated checks, not browser acceptance.

**Do not set `il_shared_campus_enabled` on any live site yet.** This is one boundary, not completed multi-institute support.

Student joining now has a local, feature-gated endpoint and confirmation dialog. It uses verified account details, creates an institute-specific student number, handles repeat registration without duplicate membership, and offers an explicit institute switch. The switcher includes a general-campus option and reloads the application to discard the prior workspace state. Context-free institute discovery is now implemented locally with bounded search, pagination, loading/error/empty states and a registration action. Its explicit field allowlist returns only profile ID and display name for verified institutes with an active administrator. Registration notifications and the remaining onboarding flow are not complete.

## Required before enabling

- Choose/provision the dedicated public-campus site and its services; do not repurpose the client or Super Admin database.
- Audit every query and mutation for institute and provider ownership, including community, notifications, files, quizzes, programmes, financial records, jobs and native LMS APIs.
- Implement verified registration with a neutral account state before joining an institute. Institute registration must provision a distinct workspace without granting access to existing institutes.
- Implement student joining, institute-specific student IDs, teacher approval and membership switching. Context-free discovery must expose only explicitly published fields.
- Handle personal teacher work separately from institute-sponsored access and enforce active subscription entitlements.
- Implement the context picker, no-institute state, session refresh and safe navigation between personalized addresses. A hostname is not proof of membership.
- Implement optional personalized addresses for Gold/Platinum; blank values remain valid.
- Review migrations for existing site-local users, duplicate email identities and conflicting roles. Do not copy passwords or assume cross-site login works.
- Complete public OTP delivery, password reset, abuse limits and provider-failure tests. Current live SMS remains recipient-restricted and email queues remain suspended.
- Test at least two institutes with disjoint users and revoked memberships, including direct API/file URL access, before any public launch.
- Configure DNS/TLS and only then verify main-site CTAs against the actual public campus.

Neither these source changes nor passing mocked tests establish browser acceptance or production readiness.



## Membership revocation audit

The institute member listing is scoped to the selected institute and requires its Admin role. Member activation/deactivation uses the scoped lookup. Fixed shared-campus deactivation so an institute administrator changes only that membership, without disabling the global User or clearing sessions for other institutes. Shared-campus activation likewise cannot re-enable a platform-disabled User. Single-institute behavior is preserved. Four regression tests cover these paths. This is a partial audit; community, native LMS access and the other areas above remain pending.


Teacher affiliation removal now resolves classroom cleanup from the relationship's institute profile, not the active workspace. Cleanup filters explicitly include that institute and its Teacher memberships. Four regression tests cover leaving another workspace, foreign-admin rejection, another teacher's relationship and missing target setup. Teacher membership creation/deactivation hooks and native LMS authorization still need review.


Shared-campus teacher affiliation decisions now synchronize the target IL Member in the same transaction: approval creates/reuses a Teacher membership; leaving/removal deactivates it; rejection creates nothing. Conflicting member roles are rejected, existing classroom assignments are not silently restored, and global User roles/subscriptions are unchanged. Six regression tests cover this helper. Actual Frappe document hooks, subscription coverage and browser acceptance are still unverified; the shared-campus flag remains off.


Subscription guard audit: six exact context-free campus endpoints now reach their own feature/authentication guards without requiring a selected institute. Unknown methods and classroom access retain subscription checks. Four regression tests cover these paths. Institute sponsorship is still sandbox-only; coverage context resolution now uses the selected, authenticated teacher membership in shared mode rather than the personal subscription's original institute. This does not enable production coverage.


Six coverage-context regression tests verify selected-institute resolution, foreign-account rejection, role mismatch, revocation without fallback, preserved single-institute behavior and disabled coverage. The personal billing account is not reassigned. Production coverage remains disabled pending the broader authorization audit.


Native course reader: shared-campus free courses now pass scoped classroom/enrollment access, and unlinked native courses are denied through this reader. Five regression tests cover allowed, foreign, unenrolled, unlinked and legacy free access. Other native endpoints still require review.

New runtime blocker identified: saas.enforce_member resolves the selected institute during insert, so context-free student registration will fail despite mocked endpoint tests. A narrowly authorized target-institute provisioning context and real Frappe integration test are required before enabling registration; do not bypass this hook or change session selection to work around it.


The member-insert blocker above is now addressed in source: an internal ContextVar authorizes only the exact already-verified student document while its insert runs. The validation hook still runs, counts only the target institute, rejects unscoped or mutated documents and restores scope even after failures. No session selection or client-settable flags are used. Seven tests exercise the actual validation function with database doubles. The single-institute registration path has now passed the rollback-only Frappe test described below. Teacher approval hooks and cross-institute isolation still require real integration testing.



## Confirmed local sandbox integration result

User supplied successful output from `test-shared-campus-transaction.py` on the local `hnb-checkout.localhost` sandbox after installation of 11 reviewed backend files. This was a targeted sandbox payload, not deployment of the entire current repository or frontend. No corresponding production deployment has occurred.

Verified through real Frappe hooks:
- Student registration creates a membership without a selected institute.
- Repeating registration returns the same student number.
- Deactivated membership cannot resolve institute context.
- Rollback restores the original membership IDs, removes the temporary institute profile and removes the temporary administrator membership.

The test blocked commits, enqueue, email and HTTP delivery. It discarded 10 routine after-commit document/list refresh events. Shared mode was enabled only in the test process and remained OFF in saved configuration. No production changes, customer notifications or restarts occurred.

Not established by this result: authenticated browser/API guard-chain acceptance, cross-institute isolation, teacher sponsorship, SMS/email confirmation delivery, production readiness. Existing institute validation still enforces one institute per site. Do not bypass that constraint to claim a two-institute test passed; a reviewed shared-campus provisioning path is required first.


## Confirmed two-institute membership integration result

The user ran the reviewed two-file sandbox update and `test-shared-campus-transaction.py --two-institutes` successfully. Backup: `/home/tharukakaru/.sisu-secrets/shared-campus-source-20261101T212318617167Z`.

Observed through real Frappe/database execution:
- Temporary second institute created through the internal provisioning scope.
- Student membership inserted through normal hooks; repeat registration returned the same student number.
- Revoking institute A's membership denied A while institute B remained accessible.
- Revoking B then denied B.
- Temporary institute, profile and administrator membership disappeared after rollback; original membership IDs were restored.
- Twelve deferred document/list refresh signals were discarded. No delivery, config writes, service restarts or production changes occurred; saved shared mode remains OFF.

This supersedes the earlier statement that two-institute membership context was untested. It does not establish classroom/file isolation, complete request-guard-chain behavior, browser acceptance, teacher approval integration, subscription coverage or production launch readiness. The two-institute provisioning scope is internal only and does not constitute a public institute registration endpoint.

Shared identity audit: api.identity no longer upgrades System Manager users to institute Admin in shared-campus mode. It uses their active membership role and retains student authentication checks. Four regression tests pass; full Python suite now 718 tests. This identity change is local only and is not yet included in the previously installed sandbox payload. Direct generic/native System Manager bypasses elsewhere remain under review; this change alone does not remove all framework-level administrative powers.

Shared native guard audit: generic/unreviewed API requests no longer bypass the guard merely because no classroom is linked to an LMS course. The System Manager/Administrator early return is restricted to legacy single-institute mode. Reviewed native readers still call require_course and reject foreign progress identities. Seven regression tests added; full suite 725 tests passes. These changes remain local, not yet included in the installed sandbox payload. SAFE endpoints, direct files, and all institute_lms endpoint authorization still need review; this is not a blanket security certification.


## Confirmed classroom isolation integration result

User supplied successful output from the expanded two-institute rollback test. Actual Frappe/database calls verified that unenrolled students are denied classroom access, an enrolled student can resolve their own classroom, and another institute's free classroom and its file-permission reference are denied. API identity retained Student; generic member API and foreign-user file permission checks were denied. Institute revocation isolation continued to pass.

Rollback verified removal of the temporary classrooms, disabled teacher User and memberships, second institute, administrator membership and profile, with original membership IDs restored. Thirty-three deferred refresh events and one after-commit job were discarded without execution. This result does not test asynchronous jobs, physical file delivery, HTTP/browser authentication and CSRF, paid entitlements, or teacher sponsorship. Shared mode remains off and no production change has occurred.


## Confirmed institute coverage evaluator integration result

The user supplied a passing expanded rollback test using actual Frappe subscription and affiliation records. Pending affiliation was denied; active affiliation with an explicit unexpired institute trial grant was covered; expired grants and removed affiliations were denied. Coverage did not apply to the other institute. The coverage evaluator allowed the scoped classroom-list method and denied independent classroom creation and generic Frappe APIs.

This was a synthetic transaction-local grant with a disabled fixture teacher, not a payment, a permanent client entitlement, an authenticated teacher session, or an approval-endpoint test. Full teacher approval/login and subscription-guard-chain behavior remain pending. Thirty-five document refresh signals and one after-commit job were discarded, and fixture rollback checks passed. Production coverage and saved shared mode remain disabled.


## Confirmed teacher approval/removal function integration result

User supplied passing output from the expanded real-Frappe rollback test. A student actor could not approve the teacher request. A transaction-local institute-admin membership actor successfully called the approval function, which activated the teacher membership. The removal function deactivated that institute's teacher membership and classroom assignment, while the same teacher's other institute membership remained active. The institute coverage evaluator rejected the removed affiliation.

All preceding registration, classroom scoping, generic API guard, file-reference and revocation checks continued to pass. Fixture rollback checks passed. Forty-nine deferred document refresh signals and one after-commit job were discarded. These are real application-function/database tests, not HTTP requests or browser approval/login tests. The teacher identity stayed disabled and no permanent customer trial, role or payment was created. Saved shared mode is still off.


## Confirmed installed request-guard chain result

User supplied a fully passing two-institute rollback test including installed auth hooks in their configured order: the four required SISU hooks and the reviewed `lms.auth.authenticate` hook. With a synthetic Werkzeug request and no institute selected, discovery, registration details, institute choices and student registration passed all installed guards. No endpoint-blocking configuration or allowlist was weakened.

All previous registration, role, classroom/file-reference denial, teacher approval/removal, coverage evaluator and revocation checks passed in the same run. Rollback checks passed. Forty-nine refresh signals and one deferred job were discarded. This does not exercise network HTTP, cookies, CSRF validation, real downloads or browser rendering. It does not establish successful teacher-sponsored requests through the complete guard chain after login. Shared mode remains off in saved settings; no production changes occurred.

## Confirmed free-class and sponsored-teacher integration result

The user ran the reviewed api.py update and complete two-institute rollback test successfully. Backup: /home/tharukakaru/.sisu-secrets/shared-campus-source-20261101T215340659360Z.

Real Frappe execution confirmed enrolled free-class access without a paid grant, and denial for the unpaid paid-class variant. An institute-sponsored teacher with an expired personal subscription could list only assigned institute classrooms; independent and foreign classes were excluded and direct independent access was denied. Approval/removal, registration idempotency, request guards, revocation isolation and fixture rollback also passed.

Local validation: 737 Python tests and 89 frontend tests pass. Fifty-one deferred refresh signals and one after-commit job were suppressed in the integration test; asynchronous delivery was not exercised. Saved shared mode remains OFF. HTTP login/cookies/CSRF, physical downloads, browser approval flow and asynchronous jobs remain unverified. The port 5184 preview uses mocked data and is not an end-to-end backend test.

Browser automation discovery in this session found no node_repl tool required by the installed computer-use skill, and no browser automation tool. Do not represent the preview or source tests as browser acceptance.
