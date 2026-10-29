# SISU final verification and completion pass V2

## Outcome

V2 extends the previous packaged release in separate working copies. The original archives and releases are unchanged. Backend remains Frappe/Python, MariaDB, Redis; one organization per site/database. Vue and Flutter share the same backend. Existing navigation, authentication, screens, assets and Study Room music were preserved. No production migration, deployment, DNS operation, provider request or real financial transaction was performed.

**This is a tested implementation candidate, not a production acceptance certificate.** See the completion matrix for feature-level boundaries. Historical RUN/release reports remain for traceability, but their older test counts and missing-work lists do not describe V2.

## What was incomplete before

Native mobile checkout/receipts, lesson editor/upload/player, allocation editing, embedded RTC and paper review/publish/export were missing or only data views. Internal verified refunds, minimized tenant commerce transport, several lifecycle notifications, safe media cleanup and mixed-type/resumable paper jobs were incomplete. The mobile preview was a developer harness rather than a presentation app.

## What was completed now

- Native Flutter product screens reuse the existing service/role/navigation patterns. Hosted payments refresh server authority after return/resume; no client activation. Payments return to a fixed tenant page linking to `sisu.payments://return`; Android app_links handles refresh only, while existing AppAuth keeps its separate OAuth redirect.
- Backend-authorized protected video, streamed presigned uploads, teacher publication/archive, billing history and shareable/printable HTML receipts.
- Actual LiveKit client integration, teacher screen-share/recording controls, student camera/mic permissions only where granted, participants, reconnect and periodic authorized recording-state refresh. Failed status/authorization refresh disconnects the client.
- Mixed paper blueprints and marks, durable per-batch accounting/results, no blind retry of unknown provider outcomes, source/entitlement revalidation, editable drafts, explicit review publication, archive and safe HTML export. JSON teacher export remains available.
- Full-refund state/adapter contract, idempotent ledger reversal and original-order access revocation. Negative available wallet balances are intentional when already-paid-out earnings must be recovered.
- Signed minimized commerce event reporting and signed subscription notices over existing tenant policy delivery, with acknowledgement/retry and stale-ack race protection.
- Operator-initiated protected media reconciliation/cleanup; no prefix/bucket purge, no deletion of sold/referenced/held or confirmed Ready uploads. Quota remains reserved on uncertain deletion/provider outcomes.
- Separate phone-width presentation Flutter preview; developer harness retained. Static preview assets are packaged; no credentials needed.

## Defects fixed

Editor detail now returns authorized private metadata instead of trying to edit a public list row. Allowance APIs/UI show effective individual limits instead of the organization balance as personal allocation. Flutter receipt export shares a real escaped HTML file. Premium focus/resume refresh and terminal polling handling were tightened. Teacher/admin role naming in AI navigation was aligned. Student LiveKit grants explicitly exclude screen-sharing and room recording/admin powers. Recordings require teacher review before student playback. Policy delivery no longer clears a newer pending revision on an older acknowledgement. Large existing-data patches are bounded. Inactive enrollments no longer receive newly added class events. New cleanup states have matching Select options.

## Schema and migration

New service-managed DocTypes: **IL Lecture Refund**, **IL Commerce Event**, **IL Subscription Notice**. No arbitrary REST mutation permissions are granted. Unique refund order/request identity and event keys provide durable duplicate protection.

Extended IL Paper Generation Job: blueprint, template_metadata, batch_results. Extended IL Live Room: recording_published and Removed recording state. IL Stored Object gains Removed media state. `institute_lms.patches.release_v2` adds indexes for commerce scheduling, notices, refunds, paper jobs and stored-object lookup; it is registered in patches.txt and fresh-install/provisioning initialization. Existing final-build/run1 migrations use bounded/keyset processing. Nothing was manually altered in a real database.

## Commands and actual verification in this turn

Run commands inside the indicated project folder. The Windows environment invoked the existing venv Python and Flutter SDK snapshot because tool binaries are outside PATH; the equivalent commands below reproduce the checks.

| Check | Command | Actual final result |
|---|---|---|
| Backend suite | `python -X utf8 -B -m unittest discover -s tests` | **PASSED: 286 tests**; local unit/regression tests with Frappe/provider doubles |
| Schema/syntax | `python scripts/verify-static.py` | **PASSED: 272 Python sources, 89 JSON documents**; not a database migration |
| Undefined names | `python -m ruff check institute_lms --select F821,F822` | **PASSED** |
| Python dependency consistency | `python -m pip check` | **PASSED** |
| Frontend install | `npm ci --offline --ignore-scripts --no-audit --no-fund --cache ../../../npm-cache` | **PASSED** from lockfile/cache; online attempt encountered connection reset |
| Vue tests | `npm test` in frontend | **PASSED: 85 tests** |
| Production Vue | `npm run build` | **PASSED** |
| Web preview | `npm run build:preview` | **PASSED** |
| Flutter dependencies | `flutter pub get --offline` | **PASSED** |
| Flutter analysis | `flutter analyze --no-pub` | **PASSED: no issues** |
| Flutter suite | `flutter test --no-pub` | **PASSED: 80 tests** |
| Production Flutter web | `flutter build web --no-pub --target lib/main.dart --no-web-resources-cdn --output build/production-web` | **PASSED**; rebuilt independently from preview |
| Developer Flutter web | `flutter build web --no-pub --target lib/main_preview.dart --no-web-resources-cdn --output preview-web` | **PASSED**; static developer preview included |
| Presentation Flutter web | `flutter build web --no-pub --target lib/main_presentation.dart --no-web-resources-cdn --output presentation-web` | **PASSED**; static phone presentation preview included |
| Android APK | `flutter build apk --debug --no-pub --target lib/main_presentation.dart` | **ANDROID ARTIFACT NOT PRODUCED — TOOLCHAIN UNAVAILABLE**; No Android SDK found |
| AAB / iOS | Not run | Android SDK absent; this project has no iOS runner, and no macOS/Xcode/signing environment |
| Browser previews | Playwright + installed Chrome, local servers only, external requests intercepted | Web: four roles/19 screens and narrow width. Mobile: six role-plan navigation checks. JSON evidence and screenshots accompany release |
| Real Frappe / MariaDB / Redis | Not available | **REQUIRES STAGING**: migration, row-lock races, hooks, jobs and transport must be accepted there |
| Real providers / mobile devices | Not called | **REQUIRES PROVIDER ACCEPTANCE** |

Added backend regressions cover blueprint validation/batch size; verified refund identity, original-order access revocation, wallet reversal, replay; tenant/teacher restrictions; recording review; exact-version cleanup, partial-delete/truncation refusal; safe paper export; signed notice field restriction; real installed SDK JWT grant shape using fictional local signing data. Flutter tests cover new receipt escaping, native screen/service wiring, plan mapping, preview role/plan states, narrow/text-scale layout and preserved baseline behavior. Frontend tests include finance/receipt/preview contracts. No tests were removed to make the suite pass; obsolete three-plan customer UI expectations were updated to the approved two-plan product.

Initial failures were fixed rather than hidden: an older customer comparison test expected CUSTOM, an exact-deletion test needed an explicit empty SDK success result, Dart lint required braces/import cleanup, and preview fixtures needed optional empty collections. Final evidence supersedes interim results.

Warnings remain: Vue workspace bundle exceeds 500 kB; intentional preview import overlap; Flutter Wasm dry-run/plugin support notices. No comprehensive online vulnerability audit, load test, device E2E or provider acceptance is claimed.

## Remaining external work and genuine scope limitations

1. Provision/stage Linux Bench, compatible pinned Frappe/LMS revisions, separate tenant/control databases, Redis/workers, HTTPS and provider callback routing. Prove migration/restore and two-tenant authorization.
2. Configure separate Payments.lk merchants/HMAC keys, OpenAI settings, LiveKit/egress, versioned private media, SMTP, Google and selected SMS/WhatsApp/push providers. Test each sandbox then production under an approved rollout.
3. **Refund vendor adapter is an integration code boundary**: deployment must implement/configure a provider-supported request/refetch callable. Internal accounting is implemented; no concrete Payments.lk refund API is invented.
4. **SMS/push concrete adapters and native push SDK remain provider-specific integration work** when no provider is selected. Their absence fails clearly; no delivery success is fabricated.
5. **iOS runner/entitlements/screen-share extension are absent** and need platform engineering on macOS. Android source is prepared but compilation/device permissions/signing were not verified because the SDK is unavailable.
6. No adaptive streaming/transcoding/DRM, automatic audio/video transcription, visual print-template designer, DOCX export or legal tax-invoice engine. Current supported path is protected file playback and safe HTML/browser-print PDF. Paper generation uses one authorized indexed document per job.
7. Pricing requests are durable audited requests; a dedicated Platform Owner push/inbox workflow is not implemented. Offers and payment notices are delivered through the new signed notice path.
8. Cleanup is deliberately operator initiated. Ambiguous jobs retain quota; held/sold/Ready content is not automatically purged. Broad legacy-media orphan discovery and automated replacement cleanup are not claimed.

## Exact deployment gate

Backup DB/files/encryption keys → restore rehearsal → install pinned dependencies (`.[live,media]` where enabled) → staging `bench --site <site> migrate` → verify V2 DocTypes/indexes/hooks → build Vue → restart web/workers/scheduler → health/readiness → signed policy ack and commerce replay test → provider acceptance → real Android/mobile auth/media/payment tests → security/permission/concurrency checks → owner approval → tenant-by-tenant rollout. Stop on failed migration/ack/provider verification. Rollback requires compatible database/files backup plus matching code, not just a Git checkout.

The files inventory is in SISU_V2_FILE_CHANGES.md; packaged files and SHA-256 values are in PACKAGE_MANIFEST.json. No APK/AAB is included.


## Final browser / artifact evidence

`docs/verification-v2/` contains this turn's captured test/build outputs and browser JSON. Web paper interaction exercised four mixed-type questions, draft save, explicit confirmation, publish and HTML download. The initial tablet walkthrough revealed header overflow; the header now wraps and the check was repeated. Flutter deep walkthrough opened actual Lesson Store, Lecture Library, Paper Generator, AI Credit Management and Subscription components; tested expired/exhausted/shared/pending/renewal-failed presets and returning to the chooser; developer preview also launched. No external requests or JavaScript errors were observed in these checks. Screenshots were taken and representative phone UI inspected. This is fictional preview evidence, not production/provider E2E.

Static secret-pattern scan found no private-key/live-key patterns in distributable source/assets, and selected fictional preview strings were absent from production Vue/Flutter JavaScript bundles. This is a limited sanity check, not an exhaustive security certification. Python undefined-name checks and pip consistency passed. No actual credentials are included or printed.
