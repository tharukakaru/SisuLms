# Classroom quizzes — local source delivery

This feature is implemented in source only. **It cannot operate until a coordinated Frappe migration creates the two new DocTypes.** No migration, seeding, deployment, remote restart, credential change or request to the shared hosted preview database was performed for this change.

## Usage

Teachers with classroom management permission (owner or full-control assignment) and authorized institute administrators open a classroom → **Papers, assignments & quizzes**.

- **Upload paper** appears immediately before **Create paper** on one horizontal row, with **Create quiz** below. It opens a dedicated form for a required title, optional instructions and required document. Uploads are immediately shared as downloadable private classroom materials and shown in All / Manual Papers; they do not create a timed assignment. The original Create paper editor remains available for questions, answer-PDF submissions and marking.
- **Create paper** retains its existing workflow.
- **Create quiz** appears on the next row for authorized classroom managers. Enter a title, optional instructions and up to 50 questions, each with four options and one correct answer. Save incomplete drafts, preview all entered questions/keys without a server mutation, or publish complete quizzes. Preview can return to the editor without losing edits.
- Open a quiz to see its answer key and paginated student submissions. Each teacher result includes the actual question snapshot, submitted option and correctness. Published quizzes can be edited before the first submission. Once submitted, all quiz content is locked; create a new quiz for changes.

Eligible students see published quizzes under **All** or **Quizzes**. Start a quiz, answer every question, review selections, then submit. A submitted quiz shows earned marks, total and percentage. Each account has one submission per quiz, including if its membership is recreated. Students receive no answer key or per-question correctness, including in their result response.

## Source map

- `frontend/src/App.vue`, `classroomNavigation.js`: assessment tab and existing bookmark routing.
- `frontend/src/native/Papers.vue`: assessment buttons/categories, upload component integration; existing written work, marking, feedback and answer-PDF paths retained.
- `frontend/src/native/ClassroomQuizzes.vue`, `classroomQuizRules.js`: editor, preview, taking/review, results and frontend validation.
- `frontend/src/i18n.js`: quiz copy in the existing labels catalog, using the English fallback. Additional translated quiz catalogs are not supplied in this change.
- `institute_lms/classroom_quizzes.py`, `classroom_quiz_rules.py`: service endpoints, authorization, validation, grading and safe response projections.
- `institute_lms/institute_lms/doctype/il_classroom_quiz/`: quiz schema/controller.
- `institute_lms/institute_lms/doctype/il_classroom_quiz_submission/`: immutable result schema/controller with unique `attempt_key`.
- `tests/test_classroom_quizzes.py`, `frontend/tests/classroom-quizzes.test.mjs`, `classroom-quiz-workflow.test.mjs`, `classroom-navigation.test.mjs`: focused tests and updated navigation expectation.

The older `QuizStudio`/`LessonQuiz` UI is a demo lesson workflow, not a suitable persisted classroom assessment model. Existing `IL Paper` supports timed/written assessments and different validation; its schema and service were left unchanged.

## Authorization and integrity

Every quiz endpoint resolves the classroom through `accessible_room`, retaining institute identity, enrollment, provider/subscription access and workspace session checks. Existing request authentication hooks continue to run. Teacher reads, keys and mutations additionally require `teaching.rights(...).edit`. No permission exceptions or extra roles are added. Student draft reads fail closed.

DocTypes expose no generic role permissions. Controllers require the service flag, disallow deletion, and reject updates to existing submissions. Standard creation/modification/owner fields, version tracking, publication actor/time and submission timestamp provide the audit trail.

Saving and submitting serialize on the same quiz row. Post-lock reads use `for_update=True` to avoid stale repeatable-read snapshots. A locking submission lookup and unique SHA-256 quiz/user key provide idempotent retry and database uniqueness. The stored result contains the exact question snapshot and server-calculated score; the student projection contains only summary fields. Concurrency behavior still requires a real isolated MariaDB integration test.

## Migration and deployment handoff

Normal Frappe DocType synchronization creates `IL Classroom Quiz` and `IL Classroom Quiz Submission`, their link indexes and the unique attempt-key constraint. No existing records or schemas are transformed; no data patch or fixture is needed.

An authorized deployment operator must coordinate backup, deployment of these source files, the standard site migration, and frontend asset build. **Do not run migration on the current local Bench: it points to the shared hosted database.** Validate in an explicitly isolated test site first. The compiled portal assets were preserved; the validation build used a separate output directory. Until coordinated deployment, use of these quiz endpoints will fail because the tables are absent.

## Verification

- Frontend suite: 64 tests pass, including the real Vue quiz component driven through an in-memory renderer with mocked HTTP. Covers draft/publish validation, retained input, preview without requests, student answer review and duplicate-click suppression.
- Quiz backend: 17 pure/mocked tests pass. Covers 1–50 limits, four options, one correct answer, incomplete drafts, visibility, management access, cross-institute rejection, access-gate failures, answer-key projection, grading, unique constraint, idempotent duplicate handling and immutable submitted quizzes.
- Existing regression suites: 36 tests pass across paper rules, private material authorization, classroom API security and teaching permissions.
- Broader existing AI suite: 59 of 62 pass; three extraction tests cannot run successfully in system Python because `defusedxml` and `pypdf` are missing. Dependencies were not upgraded or changed.
- Production Vite build passes with the existing large-chunk warning. Output was isolated to preserve pre-existing compiled asset changes.
- Not run: live database integration, actual concurrent MariaDB submissions, browser visual/device checks, or real upload/login end-to-end tests. No isolated database was available and the shared preview was not used.

Before deployment, verify with two real student accounts and one full-control teacher: hidden drafts, enrollment revocation, provider suspension, expired subscription, cross-classroom requests, generic REST denial, simultaneous submit requests (exactly one stored result), edit-versus-submit locking, private PDF upload/marking regression, and mobile keyboard/layout behavior.

## Create quiz visibility correction

Previously, `Papers.vue` initialized `quizManage` to false and rendered the action only after `ClassroomQuizzes.load()` successfully fetched quiz records and emitted `can_manage`. `listing()` queried the quiz table before returning that permission. A missing table or any list-request failure therefore hid the action, even though the existing classroom permission allowed management. An empty successful list was not the cause. The Manual filter could additionally conceal the child component's error. There was no schema-readiness response in that implementation.

The action now uses existing classroom `permissions.edit` for visibility and a separate `classroom_quizzes.metadata` endpoint for readiness. Metadata reuses the same classroom authorization and checks DocType/table/required-column presence without writes or quiz record queries. The editor requires successful authorization and readiness. Missing schema produces a disabled action with a setup explanation; metadata errors produce a disabled action with an explicit retry control outside all filters. Zero quiz records have no effect on visibility. The live shared database was not inspected to infer which request failure occurred in the reported session.

Correction files: `frontend/src/native/Papers.vue`, `ClassroomQuizzes.vue`, new `quizActionState.js`, `institute_lms/classroom_quizzes.py`, `frontend/tests/quiz-action-state.test.mjs`, `classroom-quiz-workflow.test.mjs`, and `tests/test_classroom_quizzes.py`.

Correction validation: all 68 frontend tests and 20 pure/mocked quiz backend tests pass, including authorized zero-quiz/filter states, missing schema, metadata failure/retry and authorization rejection. Production Vite build passes with the large-chunk warning, using temporary output rather than replacing existing compiled assets. No database integration or browser/device checks were performed. This correction adds no schema changes; the two original quiz DocTypes still require coordinated migration if absent.
