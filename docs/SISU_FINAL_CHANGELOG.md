> Historical pre-V2 document. Current source/status/test results: SISU_FINAL_VERIFICATION_AND_COMPLETION_REPORT.md and SISU_FINAL_COMPLETION_MATRIX.md.

# Final changelog

Separate working copies were used. Original ZIPs and baseline projects were not overwritten. No existing source file was deleted for cleanup. Generated asset bundles were rebuilt. Study Room music/audio, existing app navigation, models and services are preserved.

## Main changes

- Free Starter fallback, per-organization Premium monthly offers, immutable settlement receipts and signed policy-delivery outbox.
- Individual/Shared AI accounting and role-resolved capability facade.
- Lecture products/orders/access, hosted checkout, private media reservations/upload adapter, protected playback and retention safeguards.
- Embedded web LiveKit adapter, teacher recording controls, verified readiness and recording-to-lecture draft.
- Bounded queued paper generation using existing AI usage and IL Paper review flow.
- New web workspaces and #6C6AEE primary theme; separate fictional web/Flutter previews.
- Flutter connected data views and SISU AppAuth parameter adapter; existing OAuth explicitly preserved.

## Schema

New: IL AI Allocation, IL Premium Receipt, IL Policy Delivery, IL Lecture Product, IL Lecture Order, IL Lecture Access, IL Live Room, IL Paper Generation Job. Extended: IL Subscription (base policy/mode), IL Price Assignment (commercial plan/effective/version), IL Stored Object (media_state, storage_version). Patch: institute_lms.patches.final_build. No production migration was run.

## Web source inventory

### Added

- `FINAL_RELEASE_README.md`
- `Start-Final-Web-Preview.ps1`
- `deploy/final-control-config.example.json`
- `deploy/final-tenant-config.example.json`
- `docs/SISU_FINAL_ACCEPTANCE_CHECKLIST.md`
- `docs/SISU_FINAL_BUILD_REPORT.md`
- `docs/SISU_FINAL_CHANGELOG.md`
- `docs/SISU_FINAL_SETUP_DEPLOYMENT_AND_HANDOVER_GUIDE.md`
- `docs/SISU_MOBILE_BACKEND_HANDOFF.md`
- `docs/SISU_MOBILE_BUILD_GUIDE.md`
- `docs/SISU_MOBILE_PREVIEW_GUIDE.md`
- `docs/SISU_REAL_CREDENTIALS_CHECKLIST.md`
- `docs/SISU_WEB_PREVIEW_GUIDE.md`
- `docs/preview-screenshots/Admin-credits.png`
- `docs/preview-screenshots/Student-lessons.png`
- `docs/preview-screenshots/Student-phone-lessons.png`
- `docs/preview-screenshots/Super Admin-control.png`
- `docs/preview-screenshots/Teacher-library.png`
- `frontend/src/brand.css`
- `frontend/src/native/FinalSubscription.vue`
- `frontend/src/native/LiveRoom.vue`
- `frontend/src/native/ProductWorkspace.vue`
- `frontend/src/native/capabilities.js`
- `frontend/src/preview/final.js`
- `frontend/tests/final-preview.test.mjs`
- `institute_lms/ai_credits.py`
- `institute_lms/billing_bridge.py`
- `institute_lms/full_api.py`
- `institute_lms/full_rules.py`
- `institute_lms/institute_lms/doctype/il_ai_allocation/__init__.py`
- `institute_lms/institute_lms/doctype/il_ai_allocation/il_ai_allocation.json`
- `institute_lms/institute_lms/doctype/il_ai_allocation/il_ai_allocation.py`
- `institute_lms/institute_lms/doctype/il_lecture_access/__init__.py`
- `institute_lms/institute_lms/doctype/il_lecture_access/il_lecture_access.json`
- `institute_lms/institute_lms/doctype/il_lecture_access/il_lecture_access.py`
- `institute_lms/institute_lms/doctype/il_lecture_order/__init__.py`
- `institute_lms/institute_lms/doctype/il_lecture_order/il_lecture_order.json`
- `institute_lms/institute_lms/doctype/il_lecture_order/il_lecture_order.py`
- `institute_lms/institute_lms/doctype/il_lecture_product/__init__.py`
- `institute_lms/institute_lms/doctype/il_lecture_product/il_lecture_product.json`
- `institute_lms/institute_lms/doctype/il_lecture_product/il_lecture_product.py`
- `institute_lms/institute_lms/doctype/il_live_room/__init__.py`
- `institute_lms/institute_lms/doctype/il_live_room/il_live_room.json`
- `institute_lms/institute_lms/doctype/il_live_room/il_live_room.py`
- `institute_lms/institute_lms/doctype/il_paper_generation_job/__init__.py`
- `institute_lms/institute_lms/doctype/il_paper_generation_job/il_paper_generation_job.json`
- `institute_lms/institute_lms/doctype/il_paper_generation_job/il_paper_generation_job.py`
- `institute_lms/institute_lms/doctype/il_policy_delivery/__init__.py`
- `institute_lms/institute_lms/doctype/il_policy_delivery/il_policy_delivery.json`
- `institute_lms/institute_lms/doctype/il_policy_delivery/il_policy_delivery.py`
- `institute_lms/institute_lms/doctype/il_premium_receipt/__init__.py`
- `institute_lms/institute_lms/doctype/il_premium_receipt/il_premium_receipt.json`
- `institute_lms/institute_lms/doctype/il_premium_receipt/il_premium_receipt.py`
- `institute_lms/lectures.py`
- `institute_lms/live_classes.py`
- `institute_lms/live_provider.py`
- `institute_lms/paper_generator.py`
- `institute_lms/patches/final_build.py`
- `institute_lms/policy_delivery.py`
- `institute_lms/premium.py`
- `institute_lms/private_media.py`
- `tests/test_final_product.py`
- `tests/test_final_services.py`

### Modified

- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.vue`
- `frontend/src/native/AIWorkspace.vue`
- `frontend/src/native/ControlPlane.vue`
- `frontend/src/native/PortalRoot.vue`
- `frontend/src/preview/PreviewShell.vue`
- `frontend/src/preview/ScenarioPanel.vue`
- `frontend/src/preview/release.js`
- `frontend/src/style.css`
- `frontend/tests/preview-release.test.mjs`
- `institute_lms/ai_accounting.py`
- `institute_lms/hooks.py`
- `institute_lms/institute_lms/doctype/il_price_assignment/il_price_assignment.json`
- `institute_lms/institute_lms/doctype/il_stored_object/il_stored_object.json`
- `institute_lms/institute_lms/doctype/il_subscription/il_subscription.json`
- `institute_lms/mobile_auth.py`
- `institute_lms/patches.txt`
- `institute_lms/payments_lk.py`
- `institute_lms/platform.py`
- `institute_lms/provisioning.py`
- `institute_lms/release.py`
- `institute_lms/retention.py`
- `institute_lms/saas.py`
- `institute_lms/saas_rules.py`
- `institute_lms/setup.py`
- `institute_lms/subscription_payments.py`
- `institute_lms/usage.py`
- `institute_lms/www/campus.html`
- `pyproject.toml`
- `tests/test_run2_ai.py`

### Removed

None.

## Mobile source inventory

### Added

- `FINAL_RELEASE_README.md`
- `Start-Mobile-Preview.ps1`
- `docs/SISU_FINAL_ACCEPTANCE_CHECKLIST.md`
- `docs/SISU_FINAL_BUILD_REPORT.md`
- `docs/SISU_FINAL_CHANGELOG.md`
- `docs/SISU_FINAL_SETUP_DEPLOYMENT_AND_HANDOVER_GUIDE.md`
- `docs/SISU_MOBILE_BACKEND_HANDOFF.md`
- `docs/SISU_MOBILE_BUILD_GUIDE.md`
- `docs/SISU_MOBILE_PREVIEW_GUIDE.md`
- `docs/SISU_REAL_CREDENTIALS_CHECKLIST.md`
- `docs/SISU_WEB_PREVIEW_GUIDE.md`
- `docs/preview-screenshots/flutter-preview-phone.png`
- `lib/main_preview.dart`
- `lib/parity/final_workspace.dart`
- `lib/preview/final_preview.dart`
- `scripts/serve-mobile-preview.mjs`
- `test/final_preview_test.dart`

### Modified

- `lib/auth.dart`
- `lib/parity/hub.dart`
- `lib/theme.dart`

### Removed

None.
