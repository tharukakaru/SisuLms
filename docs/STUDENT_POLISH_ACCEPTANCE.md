# Student update — 2 November 2026

## Changes

- General dashboard requests followed free classes using the endpoint's required GET method.
- Account verification displays contact progress and the actual password requirement (12 characters), then enables Save when both contacts and matching passwords are valid.
- Classroom, provider directory and news empty states explain what to do next. Search has a smaller, padded placeholder.
- Student profile copy excludes teaching/social instructions. Students can upload profile and cover images and see their existing digital ID card. Education from signup is saved to the profile.
- Settings shows a read-only identity card, verification, appearance, email/calendar information and account controls, without repeating profile editing.
- General-campus email/calendar UI explains the institute requirement instead of calling an institute-only endpoint.
- Selected-institute news validates membership and filters followed providers to that institute. None retains all followed providers.
- General students can submit a tracked account-erasure request with uppercase CONFIRM. This is **not automatic database erasure**. Full erasure is still unfinished.

## Validation performed locally

779 Python tests, 89 frontend tests, production build passed. Mocked browser checks covered the established dashboard, exact GET method, empty classrooms, Settings without a duplicate profile form, Follow/free classes, five-minute retry countdown, short/mismatched password feedback, valid save and return to sign-in. Desktop and mobile views were exercised; Settings screenshot reviewed.

Mocked browser checks do not establish live Google callback, OTP delivery, actual profile-image persistence or database signup acceptance. The user previously confirmed receipt of live signup email and SMS codes. No new email or SMS was sent during this update.

## Live deployment

Upload `sisu-student-polish.tgz` and `scripts/deploy-student-polish.py`; run the installer as the sisu user. It rejects source conflicts, backs up source/assets and the public database, builds assets, retains previous assets, migrates only the public site's optional institute field on account requests and clears website caches. Restart the web process after success. Payment and WhatsApp configuration is not modified.

If migration fails, source may already be installed: inspect the private migration log before retrying. Database backups use bench's normal private backup location. No account data is automatically deleted or verification bypassed.

## Live acceptance still required

1. Google sign-in as the test student; no dashboard permission error.
2. Verify both contacts, enter a new password of at least 12 characters and matching confirmation, save, then sign in again.
3. Save required profile fields; upload profile and cover photos; reload and confirm persistence.
4. Confirm Settings contains the read-only card and no duplicate profile form.
5. With published demo providers present, Follow, register, switch between None and an institute; confirm classroom and news scope. An empty directory is not proof that verification is blocking discovery: profiles must exist and be published/verified.
6. On a disposable test account only, submit an erasure request and confirm its Pending status. It must not claim the account has been erased.

The demo institute seeding script is separate; its existence in GitHub does not confirm it has been run on the live site.
