# RUN 2 — Premium AI backend and RAG handoff

Implementation is complete for review, not production acceptance. Continue from this app; do not replace it with the original LMS archive. RUN 1 remains unchanged. RUN 3 has not started.

## Architecture and schema

Frappe/MariaDB remains the system of record, with one site/database per organization. Redis/Frappe jobs perform ingestion. Each classroom has a separate OpenAI hosted vector store, registered in the local site's database. No shared tenant knowledge store, database migration to another platform, local vector full scan, or Assistants API was added.

New internal DocTypes:

| DocType | Purpose |
|---|---|
| IL AI Conversation | Owner, institute, classroom, title, lifecycle and retention |
| IL AI Message | Conversation content, citations and provider metadata |
| IL AI Usage | Idempotent request, reservation, real token usage, estimated cost, outcome and reconciliation |
| IL Knowledge Index | Site/classroom-local provider store and provisioning state |
| IL Knowledge Document | Protected source, hash/revision, version, ingestion state and provider file |
| IL Knowledge Chunk | Normalized local text, section and source hashes for citation verification |

These DocTypes have no generic client REST permissions. Service flags guard controller writes/deletion; authorized backend methods own access. Standard Frappe creation/modified fields supply timestamps. `IL SOUL Settings` gains provider policy, rates, credit costs, limits, hosted-retrieval review and retention settings. Its existing encrypted API key remains authoritative. `IL Paper.ai_request_key` prevents duplicate generated drafts.

`patches/run2.py`, `patches.txt` and `setup.after_install` add non-destructive indexes and unique conversation/request/role and document/ordinal constraints. Frappe schema synchronization creates the new DocTypes and fields. **No Frappe migration was executed here.** Back up and test installation and upgrade on an isolated Frappe 17/LMS staging site first. No existing records are bulk-indexed or sent to a provider during migration.

## Feature status

“Implemented” below means backend code with local unit/mocked-provider coverage; it does not mean live provider acceptance.

| Feature | Status and boundary |
|---|---|
| Provider | Implemented: Responses API, strict JSON outputs, moderation, configurable model/timeouts/output limits, request traces; no automatic retries |
| Course Q&A / learning assistant | Implemented: authorized retrieval, grounded response, sources, modes and bounded conversation history |
| Conversations | Implemented: own create/list/read/continue/archive/delete scheduling; no teacher/admin access to student private conversations |
| Summaries / notes | Implemented: bounded authorized source text, versioned private result caching; oversized course inputs fail clearly |
| Flashcards | Implemented: validated question/answer/source JSON, private draft |
| Practice/questions | Implemented: validated MCQ, True/False and short-answer drafts |
| Quiz generation | Existing `papers.generate` now uses the shared provider/accounting path; explicit teacher review/publish and answer-key controls retained |
| Assignment feedback | Implemented for authorized teacher access to existing supported PDF paper submissions; returns feedback drafts and never changes grades |
| Semantic search | Implemented: classroom-scoped provider retrieval, current-source validation and verified excerpts |
| Recommendations / practice needs | Implemented deterministically from actual graded objective-question evidence; insufficient data is reported, not inferred |
| Teacher assistant | Implemented lesson-plan, revision, explanation and content drafts with teacher and underlying feature gates |
| Admin insights | Implemented deterministic course/assessment/attendance/usage aggregates and optional accounted LLM explanation; minimum cohort of five students |
| Usage | Implemented per-user/site/feature/month credits and provider-reported tokens; configurable estimated model cost |
| Retention | Implemented conversation/message lifecycle, cached-result expiry, source invalidation and provider cleanup; audit/financial records retained |
| Frontend | No new AI screens; RUN 3 owns UI wiring and E2E acceptance |

## Permission model

All AI operations use RUN 1's centralized `saas.require` feature resolver and subscription state. STARTER is denied; PREMIUM AI and CUSTOM receive only resolved features and configured allowance. Course AI additionally requires an actual active tenant membership, current classroom relationship, existing enrollment/payment content access and course lifecycle access. The System Manager convenience identity and platform control-plane site do not grant course-AI access.

Teacher operations use existing assigned/owned classroom authorization. Institute Admin remains tenant-local. Conversation ownership is separate from classroom administration. Archive/delete scheduling can remain available after subscription expiry through one explicit privacy endpoint; it returns no private learning content.

Retrieval checks permissions before provider work, restricts search to current authorized document IDs, validates returned provider file IDs against local records, and checks sources again before returning cached/generated answers. Source edits/deletion immediately invalidate local access. Provider deletion's eventual consistency cannot authorize stale content. Citations reference SISU material/document IDs, title, classroom and verified section; unverified provider excerpts are discarded. Missing evidence yields an explicit unsupported-answer response.

Student access preserves existing SOUL opt-in/review safeguards. Hosted retrieval additionally requires `IL SOUL Settings.hosted_retrieval_reviewed` and, for students, the server-side site setting `il_ai_hosted_student_reviewed`. **Hosted files/vector stores persist provider-side; `store=false` for Responses does not make hosted retrieval zero-data-retention.** Operators must review that distinction before enabling it. No credentials or policy approvals were invented.

## Retrieval and ingestion

`knowledge.ingest` accepts existing `IL Material`, `IL Session` or mapped `Course Lesson` sources, not arbitrary URLs or another course's uploads. It reads protected files through the existing storage layer, hashes/version-checks them and queues a deduplicated background job. Unchanged versions are reused; changed/removed sources are locally disabled. Staff can deactivate documents or explicitly reset an expired/broken index.

Extraction supports text PDFs, DOCX, PPTX and UTF-8 TXT, plus existing lesson/session text. DOC/PPT are conversion-required; scanned PDFs without usable text are not represented as successfully indexed. No OCR, YouTube download, macros or remote document fetching. TXT is also accepted by the existing material upload contract; existing view-only preview requirements remain.

The worker normalizes/chunks text, stores source sections locally, uploads normalized text to the course store and polls indexing state. Server-held provider IDs are references, never authorization. The `OpenAIRetrieval` adapter can be replaced without changing Frappe's source-of-truth models. Hosted embeddings are provider-managed; the configuration does not pretend a selectable embedding model is available.

Conservative limits: 10 MB source, 200 PDF pages/slides, 400,000 extracted characters, 300 chunks/document, at most 100 enabled documents/classroom, eight search results, approximately 18,000 characters of context. Request/model/output bounds apply separately. Larger inputs fail explicitly. Exact normalized excerpt verification favors access/citation integrity over recall.

Provider behavior was checked against official documentation: [retrieval](https://developers.openai.com/api/docs/guides/retrieval), [vector-store search](https://developers.openai.com/api/reference/typescript/resources/vector_stores/methods/search), and [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs). The Files purpose string `assistants` is used for hosted vector-store ingestion; no deprecated Assistants API endpoints or threads are used.

## Usage, cost and failure behavior

Each provider operation requires entitlement before work. `ai_accounting.execute` locks the RUN 1 subscription, reserves configurable monthly `ai_credits` through its usage ledger and commits an idempotency marker before external work. Keys include site, user, feature and caller request ID; changed input under the same ID is rejected. Completed retries return cached results after current authorization/source checks.

Credits are configurable flat request units (default one, bounded 1–100 per feature), not a claim about token or currency equivalence. Real input/cached/output/total tokens are recorded when the provider reports them. Estimated cost uses configured rates per million tokens for the actual returned model and a recorded rate snapshot. Missing rates/usage stay unknown. Hosted storage/search charges are not estimated by this token-cost model.

Failures before any provider work release the reservation through an immutable compensating usage entry. Ambiguous external outcomes retain credits and enter Review; no blind retry or duplicate debit. Owner-only `ai_accounting.reconcile` requires a reason and external reconciliation after a ten-minute minimum age. Worker/process crashes and unconfirmed external creates can require manual provider-resource reconciliation. Request locks, durable records and unique keys are implemented, but distributed behavior still needs real Redis/MariaDB tests.

Rate controls: six requests/user/minute, configurable user/site daily caps (defaults 50/500), monthly plan allowance, bounded prompt/history/output and ingestion deduplication. Existing SOUL safeguards remain. Source-version/model/user-scoped caches avoid repeated generation charges. Callers should always retain stable request IDs; legacy SOUL calls without one receive a generated ID and cannot safely replay an unknown request.

## API handoff

Use `/api/method/institute_lms.<module>.<method>` with the existing authenticated Frappe mobile/web session contract. Mutations are POST and preserve CSRF/session requirements. No shared privileged API key or generic AI DocType REST access is introduced.

| Module | Methods |
|---|---|
| `ai` | `status`, `usage`, `create_conversation`, `conversations`, `conversation`, `archive_conversation` |
| `ai` | `course_question`, `chat`, `summary`, `notes`, `flashcards`, `questions`, `search` |
| `ai` | `teacher_assistant`, `assignment_feedback`, `recommendations`, `admin_insights` |
| `knowledge` | `ingest`, `documents`, `deactivate`, `reset_index` |
| `ai_provider` | `configure` (owner only; existing `soul.configure` remains the key configuration endpoint) |
| `ai_accounting` | `reconcile` (owner only) |
| Existing | `soul.chat`, `soul.test_connection`, `papers.generate` use shared accounting/provider infrastructure |

Generation/search calls use a stable 8–160 character `request_id` containing letters, digits, underscore, colon or hyphen. Source/document IDs are SISU IDs. Q&A requires explicit consent. Generated teacher/course content is a draft until existing review/publish actions. RUN 3 should surface quota, indexing, unsupported format, insufficient evidence, review-required and provider-unavailable states instead of treating them as successful empty responses.

## Configuration and dependencies

No new secret configuration system or frontend secret. Configure the existing encrypted OpenAI API key and enabled/model settings through existing owner controls. New settings are configurable through `ai_provider.configure`: moderation model, timeout, output bound, feature credit units, model rate metadata/currency, hosted retrieval review, daily limits, document limit and retention days. Tenant feature flags and monthly allowance remain in RUN 1 subscriptions/overrides. Zero allowance does not imply unlimited AI.

Added runtime requirements: `pypdf>=6.19.0,<7` and `defusedxml>=0.7.1,<1`; tested with 6.19.0 and 0.7.1. DOCX/PPTX use bounded standard-library ZIP handling and defused XML. No large extraction/vector framework added. Audit/lint tools were installed only in the local verification environment, not as application dependencies.

Deployment still needs the Frappe/LMS runtime, MariaDB, Redis, long workers, scheduler, migrations, configured tenant subscriptions, a real OpenAI project/key with required model/vector permissions, network egress and provider data-retention review. No actual provider acceptance, production migration or deployment occurred.

## Retention and operational limits

Existing `retention.sweep` invokes AI retention; the scheduler also polls/cleans knowledge jobs. Conversations default to archival after 90 days of inactivity and later content purge, or explicit user deletion scheduling. Usage result caches expire after the configured detail period; token/credit/audit metadata remains. Disabled source chunks and provider files are removed only through cleanup handling; no financial or assessment-history deletion.

Hosted stores expire after 30 days of provider inactivity. An expired/unavailable store fails closed; staff must reset/reindex explicitly. Cleanup stops after bounded failures and requires operator attention; credentials must remain available for remote deletion. No promise of instantaneous provider erasure. Ingestion billing/unknown file creation can need reconciliation using request records/provider traces.

Recommendations cover existing objective assessment evidence, not an invented topic taxonomy or unreliable progress signal. Admin statistics are scoped and bounded; cohort suppression limits disclosure but is not a full statistical privacy guarantee. Assignment assistance covers the existing PDF submission workflow, not every possible external assignment format. Course-wide generation is deliberately bounded. No platform-wide cross-database analytics or private-content aggregation was added.

## RUN 3 and acceptance blockers

Wire Vue/mobile screens to these APIs; show citations, indexing states, credit use, drafts and actionable failures. Preserve explicit publish/review and student consent. Add browser/mobile session/CSRF and accessibility tests. Validate schema install/upgrade, transaction isolation, concurrent reservations and worker recovery on real Frappe 17/MariaDB/Redis. Perform live Responses/moderation/vector ingestion/search/deletion acceptance using a configured test project and verify returned citations and provider billing metadata. Confirm retention/privacy policy, model-rate configuration, scheduler operation and backups before release. No RUN 3, DNS, deployment or live merchant work is included.
