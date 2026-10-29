# SISU package expansion — 17 October 2026

Source and preview changes are saved in this build. No production service was deployed, no credentials were read, and no provider calls, payments or messages were sent.

## Implemented in this update
- Universal Study Room entitlement. News Feed remains Gold/Platinum; lower-tier dashboard news shortcut hidden.
- Provider tools: expense entry in integer minor units, idempotent submission, date filters, CSV export, void reasons.
- Dedicated expense operator accounts: existing enabled users only, Gold 2 / Platinum 5 seats, provider scope, revoke access, server-side seat checks after downgrade. No payment/payout/academic access granted.
- Classroom reviews: enrolled learners only, one review per learner, edits, teacher replies and moderated hide/restore with reasons.
- Configurable lifetime document/protected-video play limits and 15-minute inactive browser-session leases. Direct private material URLs are denied to students so they must use the authorised viewer.
- Platinum PDF delivery watermarks (student ID/date); original PDF stays unchanged. ReportLab is a new runtime dependency.
- Vimeo classroom embedding with validated host and preserved unlisted hash. Third-party media links remain subject to the provider's privacy and copying limitations.
- Payment-slip assistance: PDF text evidence, duplicate-reference flag and optional local PNG/JPEG OCR via a server-configured Tesseract executable. No automatic bank approval. Scanned PDFs still need manual review.
- Protected Zoom scheduling from an existing saved lesson; provider-specific OAuth credentials, waiting room, passcode, no join before host. Pending intent is committed before creation; ambiguous outcomes require reconciliation, never blind retries. Host start URLs are not exposed.
- Platinum provider-workspace name/accent and institute campus branding. Full marketing website, transactional email and native app white labelling are not complete.
- Pricing DOCX/PDF and public website feature matrix updated. No smart-card system added.

## Installation and staging requirements
1. Back up the Frappe site database/files. Install updated app dependencies (including ReportLab; existing media/live extras where used).
2. Run `bench --site YOUR_SITE migrate` to create IL Workspace Record. Run `bench build --app institute_lms` or the included frontend production build and restart the site. Do not skip migration.
3. Configure `il_zoom_server` as a mapping from provider-account name to account_id/client_id/client_secret/host_user. Keep secrets in server site configuration, never the browser or documents. Grant only required meeting-write scopes. Test using the intended host account.
4. For image OCR, install trusted Tesseract on the server and set `il_slip_ocr_executable` to its absolute executable path. English numeric bank-slip text is the current recognition target; OCR is inconclusive evidence, never confirmation of a bank credit.
5. Configure existing private video storage, bucket versioning, allowed hosts and provider adapter. Configure WhatsApp templates/consent, payment sandbox, DNS and HTTPS through existing deployment flows.
6. On staging verify actual Frappe sessions, operator login/revocation, provider isolation, concurrent-session limits, PDF private routes/watermarks, paid access expiry and video grants. Run a real sandbox Zoom creation/reconciliation test with approved credentials.

## Validation
- 370 Python tests passed, including new expense/plan rules, authorization boundaries, watermark preservation, OCR command boundaries and Zoom adapter tests with mocked provider responses.
- 125 frontend tests passed, including new expense, seat limit, review and content-control workflows.
- Production LMS, isolated preview and public website builds pass (existing bundle size warnings remain).
- Browser: institute expense saved and total updated; content settings saved; Silver student Study Room opens and News Feed navigation is absent. No browser console errors during these checks.
- Four-page pricing document rendered through Microsoft Word (bundled LibreOffice unavailable), inspected page by page.

## Remaining production / product limits
This Windows preview is not a running Frappe server. Database migrations and live integration checks remain unperformed. Native Android/iOS/Huawei store availability and full website/email/mobile white labelling remain unverified or unfinished; they must not be marketed as launched. Browser media cannot be guaranteed uncopyable. Older QA reports describe earlier builds; this report records only the package expansion.

Reference: https://www.klass.lk/pricing, reviewed 17 October 2026. SISU keeps its own enrolment-based billing definition, prices and social-learning features.
