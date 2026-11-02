# Main/dev merge review

Baseline: main `2f3559acf2c7080a2f392c8fb387a69723bdf793` (also the local origin/main ref).
Incoming: dev `a74913d802ec1e48dc60e6b70ee01a86efcd2a37` (the existing MERGE_HEAD).
No remote fetch was performed. No commit, push, deployment, migration or shared database access was performed.

## Source conflict resolutions

| File | Main behavior retained | Dev feature integrated |
| --- | --- | --- |
| `frontend/src/App.vue` | Dedicated StudentClassrooms view, provider filtering, existing classroom creation and current modal/payment flows | Separate internal creation action, shared-form mode and endpoint; quiz tab label and language |
| `frontend/src/materials/MaterialViewer.vue` | Ordinary PNG/JPEG previews, PDF rendering limits, download policy, image URL cleanup and stale-request guard | Uploaded-paper TXT/WebP previews; asynchronous text decoding also checks the request generation |
| `institute_lms/material_contract.py` | CSV/XLS/XLSX and image support, archive checks, image verification including SyntaxError handling, existing view-only companion rules | Paper-specific WebP validation and inline types |
| `institute_lms/materials.py` | Private classroom-bound storage, PDF/image inline selection, companion validation, access/expiry/download checks, watermarking and view accounting | Paper upload/listing, idempotency and text/WebP reads through the same authorized content path |

Generated conflicts were replaced by a Vite build of the combined source and the normal campus entry-copy script.

## Clean-merge review

- `api.py`, `teaching.py`, and the new internal-classroom helper retain main's shared save flow and public-provider checks. **Approved behavior change:** the user explicitly selected dev's behavior for all existing unlinked institute classrooms. Unpublished unlinked rooms stay internal on ordinary edits; assigned teachers must retain institute affiliation where directory profiles exist. Publishing still uses the original public-provider authorization path.
- `Papers.vue` retains main's manual draft/review/publish, timed attempts, answer uploads and review flows, with quiz and uploaded-document sections added. No AI entitlement was enabled.
- New quiz services use existing classroom access and teacher rights, keep answer keys manager-only, validate on the server, serialize edit/submission operations and retain immutable submissions. New DocType definitions are included but were not migrated.
- Paper uploads use the existing File storage hooks, quota checks, private reader and view billing. Main's account-storage implementation in `release.py`, `saas.py` and `account_storage.py` is unchanged. Dev's legacy-only test setup was adapted and an account-storage regression added.
- `Programmes.vue` retains enrollment, invoice messaging, classroom-open events and duration fields; the module list becomes a focus-managed modal. Main's dedicated student classroom navigation is retained; the programme popup is in the existing Programmes component, not added to StudentClassrooms cards.
- Navigation aliases and English fallback translations were reviewed alongside the renamed assessment tab. Quiz and paper helpers, schemas and tests were reviewed with their callers.
- Dev's assertion that ordinary XLS uploads must fail was corrected to preserve main's supported upload formats.

## Verification

- Frontend: 82 tests passed, including three new tests covering ordinary image previews, paper-only text/WebP previews, download policy, URL cleanup and cancellation during text decoding.
- Production build passed; Vite reports a large-chunk warning. The two generated HTML entries match and their referenced entry assets exist.
- Read-only static validation passed: 378 Python sources and 112 JSON documents.
- Isolated quiz tests: 20 passed. Internal-classroom tests: 8 passed. Upload provisioning tests: 5 passed.
- Full Python suite: 465 tests ran; 34 errors and 1 skip. Every reported error was a missing dependency (`regex`, `requests`, `PIL`, `reportlab`, `pypdf`, `defusedxml` or `livekit`); this is not a passing backend regression run. An earlier run also exposed the two upload-provisioning test-double incompatibilities described above, which are fixed and now pass.
- Dependency installation into a temporary directory failed/repeatedly lost network connections. The final stalled download was stopped. No application dependencies or lockfiles were changed. Ruff and dependency-advisory checks were not completed.
- Final staged diff passed `git diff --cached --check`; no unresolved index entries, conflict markers in changed source/documents, or unstaged application edits remain.

## Unverified areas

No live Frappe/site/browser acceptance tests were run. Real SQL locking, File hooks and replacement storage adapters, actual provider payments, PDF watermark rendering and quiz schema installation still need an isolated integration environment. The quiz UI checks schema readiness; schema definitions alone do not install database tables. No database migration was run.
