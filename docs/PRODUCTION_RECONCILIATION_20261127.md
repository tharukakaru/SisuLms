# Production reconciliation status — 27 November 2026

No production files changed. Live changes have been recovered locally; Git publication status is recorded in the final handover report. Snapshot is separate from unfinished feature work.

Archive SHA256: `99cb9339e51db9037724dfe460fdb59ed902815e6f580243a2c8b6d82d815160`.

Selected snapshot: 1,874 files; 1,081 comparisons differ only in line endings. Content differences include compiled assets and must not be treated as 207 independent missing fixes.

## Findings

- Password recovery transport, campus redirect and strength API guard exist locally; the inspected differences are whitespace/set ordering.
- Live Google signup role selection and associated tests have been merged using the shared `1a56f7c` base, preserving local onboarding changes.
- Live `provider_review.py`, owner_people review and profile notification additions are recovered. The requested first-login institute automatic approval was added on top of that service.
- Local workspace completion and approval-notice changes must be merged alongside those live changes, not overwritten.
- Marketing HTML/app.js and book-cover assets differ. The app snapshot has not been proven to be the active nginx marketing root.
- Generated live entry/assets differ from local assets. Keep complete matching bundles; do not mix HTML from one build with chunks from another.

## Source difference inventory

| File | Current comparison |
| --- | --- |
| `marketing/app.js` | differs |
| `marketing/contact/index.html` | differs |
| `marketing/institutes/index.html` | differs |
| `marketing/students/index.html` | differs |
| `marketing/teachers/index.html` | differs |
| `marketing/index.html` | differs |
| `frontend/tests/teacher-institute-profile.test.mjs` | differs |
| `frontend/tests/signup-role-layout.test.mjs` | missing locally |
| `frontend/tests/teacher-entry-flow.test.mjs` | differs |
| `frontend/tests/signup-verification-popup.test.mjs` | differs |
| `frontend/src/native/VerifiedSignup.vue` | differs |
| `frontend/src/native/RegistrationFlow.vue` | differs |
| `frontend/src/native/PortalRoot.vue` | differs |
| `frontend/src/native/ControlPlane.vue` | differs |
| `frontend/src/native/TeacherInstitutes.vue` | differs |
| `frontend/src/native/OwnerOverview.vue` | differs |
| `frontend/src/native/ProviderFirstLogin.vue` | differs |
| `tests/test_run3_release.py` | differs |
| `tests/test_run1_foundation.py` | differs |
| `tests/test_shared_native_guard.py` | differs |
| `tests/test_google_signup_role.py` | missing locally |
| `tests/test_owner_billing_invitation.py` | differs |
| `tests/test_site_policies.py` | differs |
| `institute_lms/billing_transport.py` | differs |
| `institute_lms/policy_delivery.py` | differs |
| `institute_lms/public/login-presentation.js` | differs |
| `institute_lms/subscription_payments.py` | differs |
| `institute_lms/registration.py` | differs |
| `institute_lms/provider_review.py` | missing locally |
| `institute_lms/billing_bridge.py` | differs |
| `institute_lms/teaching.py` | differs |
| `institute_lms/subscription_notices.py` | differs |
| `institute_lms/owner_people.py` | differs |
| `institute_lms/profiles.py` | differs |
| `institute_lms/site_policies.py` | differs |
| `institute_lms/onboarding_navigation.py` | differs |
| `institute_lms/platform.py` | differs |
| `institute_lms/www/campus.html` | differs |
| `institute_lms/institute_lms/doctype/il_organization/il_organization.py` | differs |
| `institute_lms/institute_lms/doctype/il_organization/il_organization.json` | differs |
| `institute_lms/institute_lms/doctype/il_provisioning_job/il_provisioning_job.py` | differs |
| `institute_lms/institute_lms/doctype/il_provisioning_job/il_provisioning_job.json` | differs |
| `institute_lms/institute_lms/doctype/il_subscription/il_subscription.py` | differs |
| `institute_lms/institute_lms/doctype/il_policy_delivery/il_policy_delivery.json` | differs |
| `institute_lms/release.py` | differs |
| `institute_lms/portal_session.py` | differs |
| `institute_lms/portal_policy.py` | differs |
| `institute_lms/premium.py` | differs |
| `institute_lms/commerce_events.py` | differs |
| `institute_lms/native_access.py` | differs |

Full file/hash inventory and per-file patches are in the separate local `work/sisu-production-20261127-035743` snapshot. They are review artifacts, not release inputs. The initial signature scan found no private-key/API-prefix matches; a complete secret review is still required before commit.

## Acceptance gates

Google role routing and provider-review sources/tests are reconciled on the existing feature branch. The table above records the original comparison, not remaining missing files. Production-added tests pass with local tests. Browser/Frappe staging verification and a new release manifest remain required before any production deployment. Current unit-test success is not evidence that this branch reproduces live behavior.

## Verified marketing recovery

The actual nginx-served release was exported separately and inspected: 134 selected files, 52 differing/missing repository files, and 40 differences from the app snapshot. The 52 files were recovered into local `marketing/` after confirming it had no uncommitted changes. Local-only files were retained for review. No production write occurred. Archive/hash evidence is in `work/sisu-production-20261127-035743/marketing-comparison.json`. Initial private-key/token signature scan found no matches; full pre-commit review is still required.
