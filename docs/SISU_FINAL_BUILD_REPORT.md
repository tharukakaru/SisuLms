> Historical pre-V2 document. Current source/status/test results: SISU_FINAL_VERIFICATION_AND_COMPLETION_REPORT.md and SISU_FINAL_COMPLETION_MATRIX.md.

# SISU final build report — 6 October 2026

## Release judgement

| Deliverable | Status | Meaning |
|---|---|---|
| Web/backend release | **PARTIAL** | Substantial new implementation and green local tests; live runtime validation and listed source work remain |
| Mobile release | **PARTIAL** | Existing app preserved; new connected views/auth adapter and offline preview; native workflow gaps remain |
| Web preview | **READY** | Built and browser-checked, fictional only |
| Flutter preview | **READY** | Separate entry point, web build and browser launch checked; Android blocked by SDK |
| Deployment guide | **READY** | Setup, migration, rollback, credentials and acceptance instructions included |
| Real providers | **NEED CREDENTIALS / NEED ACCEPTANCE** | No live merchant, OpenAI, messaging, storage or meeting acceptance performed |

This report does **not** claim a fully code-complete production system. Mock/preview success is not provider acceptance.

## Tests and builds actually executed

| Check | Command / scope | Final result |
|---|---|---|
| Backend | `python -X utf8 -B -m unittest discover -s tests` in web/backend root | **PASSED: 264**; unit/pure-rule and Frappe-double tests |
| Python undefined names | `python -m ruff check institute_lms --select F821` | **PASSED** |
| Python/schema syntax | AST parse 232 Python files; JSON parse/field-name checks 72 DocTypes | **PASSED**; not a Frappe migration |
| Frontend tests | `npm test` in frontend | **PASSED: 80** |
| Production Vue build | `npm run build` | **PASSED** including Frappe entry copy |
| Web preview build | `npm run build:preview` | **PASSED** |
| Flutter dependencies | `flutter pub get --offline` using existing cache | **PASSED** after SDK-cache/Pub metadata permission grants |
| Flutter analysis | `flutter analyze --no-pub` | **PASSED: no issues** |
| Flutter suite | `flutter test --no-pub --concurrency=1` | **PASSED: 65**; subsequent preview-only text adjustment also passed all 3 preview tests |
| Flutter preview build | `flutter build web --no-pub --target lib/main_preview.dart --no-web-resources-cdn` | **PASSED**; local CanvasKit assets, no CDN needed |
| Normal Flutter build | `flutter build web --no-pub --target lib/main.dart --no-web-resources-cdn --output build/production-web` | **PASSED** |
| Android debug APK | `flutter build apk --debug --no-pub --target lib/main_preview.dart` | **ENVIRONMENT BLOCKED: No Android SDK found** |
| AAB / iOS | Not executed | **NOT RUN**; Android toolchain / macOS-Xcode-signing required |
| Web browser | Existing Playwright + installed Chrome; four roles, 19 screens, 390px check | **PASSED**: zero JS errors, zero external requests; screenshots saved |
| Flutter browser | Local preview at 390px, accessibility semantics and screenshot | **PASSED**: zero JS errors, zero external requests; widget tests cover role/plan switching |
| Preview exclusion | Production Vue/Flutter compiled assets checked for new preview fixtures | **PASSED** |
| Python dependency consistency | `python -m pip check` | **PASSED** |
| SDK contract inspection | Installed LiveKit API 1.2.1 / boto3 1.43.108; constructor/protobuf fields and local fictional JWT | **PASSED local inspection only** |
| Real Frappe/MariaDB/Redis migration/concurrency | No Bench runtime available | **REQUIRES STAGING** |
| Real providers / Android authentication/media | No production/provider calls made | **REQUIRES PROVIDER ACCEPTANCE** |

Initial failures were fixed: Vite's bundled config loader hit sandbox ancestor access (native loader now used); older subscription preview expectations assumed expired meant no LMS; AI-accounting test doubles lacked the new allocation boundary; one Flutter view missed the Json import and braces. Final results above replace these initial failures.

Warnings: Vite reports a >500kB media workspace chunk and the preview adapter's deliberate static/dynamic import overlap. Flutter reports informational Wasm dry-run and icon tree-shaking messages. Two cached Dart packages have newer versions outside current constraints; the lockfile was retained. No exhaustive vulnerability audit or live load test is claimed.

## Implemented

- Server-resolved free Starter fallback; organization suspension/signed-policy expiry kept separate; internal historical CUSTOM data retained.
- Per-organization monthly Premium offers, immutable quote snapshot (including audited overrides), calendar-month renewal, verified-settlement receipt and signed policy outbox/acknowledgement.
- Individual/Shared AI allocation enforcement before provider work, personal and organization usage views, audited Admin allocation changes.
- Lecture product/order/access DocTypes, tenant/teacher ownership checks, pending checkout, signed payment identity checks, duplicate settlement protection, teacher wallet entry, purchase notification and receipt reference.
- Private S3-compatible video upload reservation and confirmation, short-lived playback boundary, purchased media retention safeguards. Existing Frappe storage remains default.
- Embedded web LiveKit room controls, server-only recording authority, verified recording metadata, protected recording playback and recording-to-lecture draft.
- Queued 1–100 MCQ paper generation in <=20-question batches, source/version checks, bounded credit reservation, duplicate validation, draft review and teacher JSON export.
- Web workspaces for subscription, lessons/purchases/library, live classes, credits/storage and queued papers. Primary brand #6C6AEE.
- Dedicated offline Flutter preview plus connected structured-data views; AppAuth-to-Sisu PKCE adapter with existing Google/approval/session policy. Legacy OAuth retained explicitly.
- Two local preview servers/launchers; fictional role, subscription, AI, payment, lesson, live and paper states; all originals preserved.

## Partially implemented / source work remaining

1. **Mobile full parity is not complete.** Embedded RTC camera/mic/screen-share/recording UI, protected lesson/recording player wiring, native lecture upload/editor, paper queue/review/publish/export forms, Admin allocation editing and organization checkout/receipt UI still need completion. New connected views expose real contracts without pretending these flows work.
2. **Financial metadata mirroring from every tenant to the control plane is not implemented.** Control-plane subscription receipts exist; student/class/lesson financial summaries remain tenant-local. No cross-site SQL or fake aggregated revenue was added.
3. **Lesson refunds/reversals are not automated.** Existing order/access fields support revoked/refunded states, but a verified provider refund/reversal workflow and finance reconciliation UI are still required before commercial lesson sales. Late/duplicate distinct charges require operator reconciliation.
4. **Private-media reconciliation remains operator-driven.** Incomplete uploads/ambiguous egress preserve reservations; there is no automatic remote deletion or orphan cleanup. Configure the same compatible private bucket for recording/playback, validate file types and bucket CORS. Full adaptive streaming/transcoding/CDN lifecycle is not implemented.
5. **Large paper generation is a bounded first implementation.** It generates MCQ batches from one authorized indexed source, not a complete configurable marks/type/template blueprint. A failed/ambiguous job enters Review; resumable safe-batch retry/recovery UI and PDF/DOCX template export remain unimplemented. Existing small generation stays available. Automatic video transcription is not implemented.
6. **Notifications reuse existing infrastructure but are not exhaustive.** Lecture purchase emits the existing payment-success event. All new live/receipt/low-credit lifecycle triggers and cross-site billing-contact notifications still need complete event coverage. Pricing requests currently create an audit record rather than a guaranteed owner message.
7. Receipts have authenticated data and web print output; a finalized commercial tax invoice layout/server PDF workflow still requires business rules and implementation.

## Safety, scope and preservation

No original release ZIP was overwritten. No existing source file was deleted. Existing Student/Teacher/Admin functionality, assets, navigation and Study Room audio remain in the copied projects. Generated bundles were rebuilt. No database migration, production deployment, DNS change, real payment, OpenAI call, SMS, WhatsApp, email, tenant provisioning or push registration was performed.

New controllers reject arbitrary DocType mutations; backend authorization remains in services. Preview role switches and mock plan checks exist only in preview graphs. New mobile production UI uses server capability responses. Secrets are configuration references/placeholders only; optional provider dependencies do not imply configured providers.

## Deliverables and exact documents

Folders: `SISU_FINAL_FULL_RELEASE`, `SISU_MOBILE_FINAL`. ZIPs: `SISU_FINAL_FULL_RELEASE.zip`, `SISU_MOBILE_FINAL.zip`, `SISU_FINAL_DOCUMENTATION.zip`. Web static preview is `preview-dist`; Flutter static preview is `preview-web`. APK/AAB: **not produced**.

Documents under each package's `docs/`:

- `SISU_WEB_PREVIEW_GUIDE.md`
- `SISU_MOBILE_PREVIEW_GUIDE.md`
- `SISU_MOBILE_BACKEND_HANDOFF.md`
- `SISU_MOBILE_BUILD_GUIDE.md`
- `SISU_FINAL_SETUP_DEPLOYMENT_AND_HANDOVER_GUIDE.md`
- `SISU_REAL_CREDENTIALS_CHECKLIST.md`
- `SISU_FINAL_ACCEPTANCE_CHECKLIST.md`
- `SISU_FINAL_CHANGELOG.md`
- `SISU_FINAL_BUILD_REPORT.md`

Before deployment: complete the remaining source work relevant to the launch scope, configure providers, migrate staging, test two-tenant authorization/concurrency, accept signed callbacks and mobile auth/media on devices, prove backup/restore, pin tested Frappe/LMS versions and obtain explicit deployment approval. Until then the overall web/backend and mobile release judgements remain **PARTIAL**.
