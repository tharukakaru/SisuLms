# Classroom paper uploads

## Behavior and local verification

In a classroom managed by the current teacher, open **Papers, assignments & quizzes**. **Upload paper** and **Create paper** share the first row; **Create quiz** remains beneath. Choose Upload paper, enter a title and optional instructions, select a file, then submit. Transfer progress and processing feedback are displayed. Controls are disabled during upload; retries reuse a request key. Success returns to Manual Papers and refreshes the uploaded-paper list.

An eligible enrolled student sees the uploaded title, instructions, file type and size in All / Manual Papers. PDF, plain text and supported images offer inline previews. Every uploaded paper offers an authorized download. Office documents require a compatible application to open after downloading. No quiz questions, timed attempts, answer submissions or grading are created by this workflow; use Create paper for those existing features.

Supported formats: PDF, DOC/DOCX, XLS/XLSX, PPT/PPTX, UTF-8 TXT, PNG, JPG/JPEG and WEBP. The existing 10 MB per-file limit is retained. Images are verified using the existing Pillow dependency and limited to 20 megapixels. OpenXML containers are checked for document type, traversal, encryption, oversized contents and VBA projects. HTML, SVG, executable and macro-enabled Office extensions are rejected. Legacy Office formats retain the existing OLE-header validation; this is not an antivirus scanner.

Run real teacher/student verification only on an explicitly isolated development site. The current local Bench uses a shared hosted database: an actual upload would write to it, so no real upload was performed during implementation. Check uploads and preview/download at desktop and mobile widths, then revoke enrollment and verify both endpoint and direct-private-URL denial. Confirm unrelated timed papers, written assignments and quizzes still work. No database integration or browser/device verification was performed here.

## Storage and authorization

No new DocTypes or fields are introduced. Uploaded papers use existing `IL Material` records with `kind=Document`, `download_policy=Downloadable` and private `File` records attached to their classroom. A `paper-upload-` record-name prefix distinguishes uploaded papers without repurposing instructions or schema fields. Deterministic names bind classroom, uploader and request ID, with a classroom-row lock providing idempotent retry. Earlier uploads made through the assignment editor are retained unchanged and are not reclassified.

`materials.upload_paper` checks `accessible_room` and existing `teaching.require(..., 'edit')`, derives institute/classroom from the authorized room, and reuses the material upload's private storage, rate limit, size checks and storage hooks. The frontend retains the existing storage-quota check. `materials.paper_listing` applies the classroom access gate, institute filter and material expiry policy. Viewing/downloading reuse `materials.content`, `checked_file`, and the existing private-file guard. No public file URLs are returned in the list.

General material uploads retain their existing permitted formats. Excel/image acceptance and inline text/image previews are limited to the uploaded-paper workflow. Existing PDF viewer and view-only Office-preview behavior remain intact. New form copy is in the existing labels catalog with the platform's English fallback.

## Changed files

- `frontend/src/native/Papers.vue`: two-row actions, dedicated upload form, private document list.
- `frontend/src/native/PaperUploadForm.vue`: validated form, disabled controls, progress and errors.
- `frontend/src/native/paperUpload.js`, `paperUploadRules.js`: upload transport, retry key, quota/client validation.
- `frontend/src/materials/MaterialViewer.vue`: safe text/image preview alongside the existing PDF viewer.
- `frontend/src/i18n.js`: upload labels.
- `institute_lms/materials.py`: shared upload storage helper, upload/list endpoints and authorized inline responses.
- `institute_lms/material_contract.py`: narrowly scoped Excel/image validation using existing dependencies.
- `tests/test_uploaded_papers.py`, `frontend/tests/paper-upload.test.mjs`: focused validation/access/transport tests.
- `docs/CLASSROOM_QUIZZES.md`, this handoff: updated usage and deployment information.

## Validation and deployment

- 71 frontend tests pass, including upload validation, request scope, CSRF, progress and stable retry identity.
- Uploaded-paper test module: 21 tests pass (including inherited/private-file regression cases). Image verification was rerun successfully using an existing Python environment with Pillow; no dependency installation was needed.
- Existing material, quiz and paper-rule suites: 8 + 20 + 9 tests pass.
- Production Vite build passes with the existing large-chunk warning. Build output is isolated and removed afterward, preserving existing compiled assets.
- Real database/concurrent transaction integration, actual uploads, and browser/mobile visual checks were not run.

**No migration is required for this upload change.** No migrations, database permission changes, shared database writes, deployment, remote restarts or dependency upgrades were performed. Deploy source/assets through the existing coordinated release process. Previously introduced quiz DocTypes have their own migration requirement; that requirement is unchanged and independent of paper uploads.

## Provisioning failure: “SaaS tenant must be provisioned before use”

The exact origin is `institute_lms/saas.py:state`: it raises this error when the effective configuration of the site serving the request has no nonempty `il_tenant_id`. This is a site-configuration lookup, not an `IL Institute` lookup. An institute such as INVTEST, classroom IT, or an existing teacher membership cannot replace a registry-issued tenant ID.

The new upload trace is `paperUpload.uploadPaperDocument` → `release.workspace` HTTP preflight → `api.identity` (institute/member) → `saas.resolved` → `saas.state` → missing `frappe.conf.il_tenant_id`. The multipart file request is not sent if this preflight fails. The older `materials/client.js:uploadDocument` makes the same `release.workspace` preflight; there is no different tenant inferred or supplied by the new upload.

Skipping that preflight would not fix legitimate provisioning: `materials.upload_paper` uses `accessible_room` plus `teaching.require(..., 'edit')`, then the same `store_upload` / Frappe `save_file` path as `materials.upload`. The registered `storage.before_write` and `storage.file_saved` hooks enforce `saas.quota('storage_bytes', ...)`, which also requires `saas.state(lock=True)`. Paper answer-PDF uploads use `save_file` as well. These guards remain unchanged.

Classroom reads and paper authoring can work because institute/membership resolution and account/provider feature policy are separate from infrastructure storage allocation. `saas.require` uses `commercial.feature_policy` (account billing) where available; storage quotas still require tenant-local provisioning. Existing classroom access is therefore not evidence that new file storage is configured.

Required operator review (not executed): identify the actual local Frappe site serving the browser Host and confirm its effective `il_tenant_id` matches the authorized registry identity for the database it connects to. An SSH database tunnel does not copy the remote site's configuration into the local site's configuration. Do not use `INVTEST`, `IT`, a generated identity, or another site's identity as a substitute. The matched tenant must also have its legitimately provisioned `IL Subscription` and storage allocation/policy. The reported error establishes only the missing effective tenant setting; it does **not** establish that the registry entry or subscription row is absent. Those were not inspected on the shared database.

No runtime-source or UI behavior was changed for this investigation because the traced path uses the established context and changing it would bypass the required storage guard. Added regression coverage: `tests/test_upload_provisioning.py` (4 passing), the provisioning-failure case in `frontend/tests/paper-upload.test.mjs` (4 passing upload tests total), plus existing uploaded-paper and material suites (21 and 8 passing). Tests use mocks and an existing Python interpreter; no site initialization, shared database read/write, provisioning, trial reset, configuration change, migration or deployment occurred. Uploads remain blocked until the legitimate serving-site configuration is corrected by the responsible operator.
