# Flutter integration contract — RUN 3

## Host and identity

Each organization has one canonical HTTPS Frappe site and isolated database, e.g. `https://academy-a.sisu.example`. The institute code identifies an organization; it is not a password, tenant selector header or authorization token. There is no public global discovery API. Obtain the canonical host from a trusted invitation/configured organization directory; reject HTTP, arbitrary redirects and unexpected host changes. A custom domain must be operator-mapped to that same site. The dedicated control-plane billing host has separate accounts/sessions and does not serve private academic content.

Every request below is `/api/method/institute_lms.<module>.<method>`. Successful JSON is wrapped as `{"message": result}`. Do not use arbitrary `/api/resource` access. Mobile tokens are scoped to SISU methods; upstream native Frappe/LMS endpoints and `cmd` dispatch are rejected. Use the protected material/submission APIs on the canonical tenant host.

## Authentication / PKCE

1. Generate a cryptographically random PKCE verifier (43–128 permitted characters), `challenge=base64url(SHA256(verifier))` without padding (43 characters), random state (24–128 safe characters), and an installation device ID (8–120 letters/digits/underscore/hyphen). Keep verifier/state transient and bind them to the initiating host.
2. Open the **system browser**, not an embedded password collector, at GET `mobile_auth.authorize?challenge=...&state=...&redirect_uri=...`. The redirect URI must exactly match `il_mobile_redirect_uris`, with no query/fragment. Configure a verified app/universal link where possible. The server directs an unauthenticated browser through Google and displays the signed-in identity and an explicit approval form. Students must retain the Google-authenticated policy. Other users can establish their permitted browser session before approval.
3. Browser approval POST `mobile_auth.approve` is CSRF-protected. The app callback contains a single-use code and state. Reject wrong state, uninitiated callbacks or wrong host. Code expires after 120 seconds.
4. POST `mobile_auth.exchange` **without browser cookies**, JSON `{code,verifier,redirect_uri,device_id}`. Receive `{access_token,token_type:"Sisu",expires_at,site}`. Verify `site` is the expected canonical site.
5. Use `Authorization: Sisu <token>` on subsequent SISU API requests. Store the token in Android Keystore/iOS Keychain-backed secure storage, keyed by tenant host and account. Do not log tokens, OTPs, authorization codes or sensitive responses. Do not mix cookies and mobile authorization. Tokens expire after seven days; there is no refresh-token endpoint—repeat the browser flow.
6. POST `mobile_auth.logout` `{}` using the current token revokes that mobile session. An authenticated browser may revoke an owned session by its identifier. Clear local credentials and cached private content on logout/tenant change. Do not pretend a local logout succeeded server-side if offline; retry revocation when possible.

Browser Vue clients use same-origin cookies and the CSRF token returned by GET `portal_session.current`. Flutter's token path uses Frappe's auth hook; verify actual Frappe 17 CSRF/auth middleware behavior in staging. Never globally disable CSRF or introduce a shared API key to work around integration failures.

## Core endpoints

Unless noted, use JSON POST (read-only methods without method restrictions also accept GET). Mutations must be POST. IDs are server-issued opaque strings; always handle ownership/role rejection.

| Area | Methods / arguments / result |
|---|---|
| Session | GET `mobile_api.current` → `{api_version:1,session,subscription}`; GET `portal_session.current` → authenticated identity/role/member. `saas.status` remains reachable for expired subscriptions |
| Profile | `profiles` and `private_contact` methods listed in the generated signature index below; `private_contact.get_details`, `private_contact.save_details({data})`; do not infer privileged fields from UI |
| Classes | `mobile_api.classes({page})` / `api.classrooms({page,search})` → 24 class rows including permissions/access reason; `api.classroom_detail({name,page})` → room, access, sessions, materials, feedback, announcements |
| Enrollment | `mobile_api.enrollments({page})` → own active rows, expiry/lifecycle; staff `api.enrollments({classroom})` and existing authorized enrollment APIs. Enrollment does not itself establish paid access |
| Lessons | `mobile_api.lesson({course,chapter,lesson})` applies SISU/native course access before retrieval; no direct bypass to native paid content |
| Schedule | `api.schedule({starts_on,ends_on,page})`; data is tenant/role-scoped |
| Materials | POST multipart `materials.upload` with file, classroom, purpose (staff); GET `materials.content?material=<id>&action=view` or `download` streams protected bytes. Downloads can be denied by policy. No arbitrary file URLs or provider IDs |
| Papers | `papers.listing({classroom,page})`, `detail({name})`, `start({name})` → attempt/questions/deadline/server_time, `submit({attempt,answers})`; respect server time/deadline and do not expose staff answer keys |
| Submissions | `papers.submissions({paper,page})`, staff `mark({attempt,score,feedback})`; multipart `upload_answer` with attempt/file; GET `answer_file?attempt=<id>` uses ownership checks |
| Plans / storage | `saas.status` → resolved features/limits/state/availability; `release.workspace` → subscription, storage, backend, admin-only detailed usage/billing URL; `usage.summary` requires Institute Admin |
| Student payments | `api.invoices`, existing `payments_lk.checkout` and signed webhook flow; inspect exact signature index. Use returned hosted checkout URL after strict provider-host validation. Refresh invoices from the server after return |
| Organization payments | **Control-plane host/session only**: `release.billing` returns only authorized organizations/plans/payment attempts; `subscription_payments.quote({tenant,plan})`, `checkout({quote})`, `status({attempt})`. Tenant tokens cannot be reused there |
| Notifications | `notification_service.inbox({page,unread})`, `mark_read({name})`; `release.unread` returns total count; `release.channels` returns configuration/entitlement booleans and preferences; `save_preferences({settings:{channels,events}})` preserves existing event overrides |
| Device tokens | `devices.register({device_id,token,platform})`, platform `android`/`ios`/`web` → `{device}`; `devices.revoke({device})`. Tokens belong to the authenticated user; registration is not delivery acceptance |
| OTP | `release.otp_status`; `mobile_verification.request_code({phone})` for SMS; `private_contact.request_whatsapp_code({phone})`; `mobile_verification.verify({code,channel,challenge})`. E.164 phone, 60-second resend cooldown, 600-second expiry, five attempts. Persist neither code nor plaintext OTP |

## AI / RAG

`ai.status` returns resolved AI flags, account/provider availability, hosted retrieval status and usage `{period,tenant_used,tenant_limit,tenant_remaining,user_credits,user_tokens,reset,credit_basis}`. `ai.usage({tenant:false})` returns own bounded request metadata; tenant=true is Institute Admin only. Backend enforcement applies even if the UI exposes a tool.

| Method | Body / behavior |
|---|---|
| `ai.create_conversation` | `{classroom,title}` → `{name}` |
| `ai.conversations` / `ai.conversation` | `{page}` / `{name,page}`; owner only; 30 conversations / 50 messages per page |
| `ai.archive_conversation` | `{name,delete:false}` archives; delete=true schedules private content deletion, not financial-record deletion |
| `ai.course_question` | `{classroom,question,request_id,conversation:null,consent:true,mode:"question"}`; modes question/explain/simplify/examples |
| `ai.chat` | `{conversation,question,request_id,consent:true,mode}` |
| `ai.summary`, `notes`, `flashcards`, `questions` | `{classroom,document:null,instruction,request_id}`; generated drafts, supported sources only |
| `ai.search` | `{classroom,query,request_id}` → `{results:[source+excerpt+relevance]}` |
| `ai.recommendations` | `{classroom}` → actual assessment evidence, or insufficient evidence; Student self only |
| `ai.teacher_assistant` | `{classroom,task,document,instruction,request_id}`; authorized teacher; task lesson_plan/revision/explanation/summary/notes/flashcards/questions/quiz |
| `papers.generate` | `{classroom,topic,count,document,request_id}` → saved official quiz **draft**, followed by explicit review and `papers.publish({name,reviewed:true})` |
| `ai.assignment_feedback` | `{attempt,request_id}` → `{draft_feedback,attempt,requires_teacher_review:true}`; never automatically saves grades |
| `ai.admin_insights` | `{classroom,explain:false}` deterministic aggregates; explain=true plus request_id uses credits; small-cohort privacy suppression applies |
| `release.learning_sources` | `{classroom}` → ready, currently authorized source metadata, no provider IDs |
| Staff knowledge | `knowledge.documents({classroom})`, `ingest({classroom,source_type,source_name})`, `deactivate({document})`, `reset_index({classroom,reason})`; reset needs deliberate UI confirmation |

Retain the same stable 8–160 character `request_id` for a retry of the same input; do not create a new ID after a provider timeout. Allowed characters: letters, digits, underscore, colon, hyphen. Ambiguous requests may require owner reconciliation. Failed external work can retain reserved credits. Conversation history and source contexts are bounded server-side.

Example response inside Frappe's `message` envelope:

```json
{"answer":"Explanation grounded in the material.","supported":true,"citations":["S1"],"sources":[{"id":"S1","document":"<knowledge-document>","version":1,"source_type":"IL Material","material":"<material-id>","classroom":"<classroom-id>","title":"Lesson notes","section":"page 2"}],"draft":true}
```

Only render returned source references; do not invent pages/links. `supported:false` means insufficient course evidence. Render content as text, not executable HTML. Source opening still calls the protected SISU material API. Never show vector/file-store provider IDs or treat them as permissions. Flashcards return `cards:[{front,back,source}]`; questions return `questions:[{kind,prompt,options,answer,marks,source}]`. These are private practice/drafts, not permission to publish official assessments.

## Request and error example

```http
POST /api/method/institute_lms.ai.course_question
Host: academy-a.sisu.example
Authorization: Sisu <per-user-token-from-secure-storage>
Content-Type: application/json

{"classroom":"<authorized-id>","question":"Explain this lesson","request_id":"<stable-uuid>","consent":true,"mode":"simplify"}
```

Handle non-JSON gateway/network errors separately. Frappe errors may contain `exc_type`, `exc`, and nested JSON `_server_messages`; extract a plain-text message, never display stack traces or raw HTML. 401 means reauthenticate; 403 can mean membership/payment/subscription/feature refusal; validation commonly uses 417. Do not rely solely on English message matching for security. Show server quota/provider/indexing errors, allow safe refresh, and never fabricate successful payment/indexing/OTP results. Payment states are created/pending/succeeded/failed/cancelled; unknown means processing/review. Only server `succeeded` is paid. Index states include Queued/Extracting/Indexing/Ready/Unsupported/Failed/Review/Disabled/Deleting/Deleted.

## Required staging checks

Use two organizations and two users/course groups; test tenant switches, token revocation/expiry, Google student policy, CSRF/browser approval, wrong state/verifier/redirect, protected file streaming, unpaid native-course denial, cross-course RAG denial, conversation privacy, quota concurrency, provider failures, payment replay and returned-but-unpaid checkout. Local unit tests do not certify Flutter or the Frappe 17 middleware.

## Source-derived method signature index

This index is generated from whitelisted source methods for the relevant modules. It is not an authorization grant: role, membership, plan, provider and object checks still apply. `allow_guest` methods such as signed webhooks are not mobile write APIs. Provider callbacks should only be used in their documented flows.

| Method | Arguments | HTTP | Guest declaration |
|---|---|---|---|
| `mobile_auth.authorize` | `challenge, state, redirect_uri` | GET | True |
| `mobile_auth.approve` | `challenge, state, redirect_uri` | POST | False |
| `mobile_auth.exchange` | `code, verifier, redirect_uri, device_id` | POST | True |
| `mobile_auth.logout` | `session=None` | POST | False |
| `mobile_api.current` | `` | GET,POST | False |
| `mobile_api.classes` | `page=0` | GET,POST | False |
| `mobile_api.enrollments` | `page=0` | GET,POST | False |
| `mobile_api.lesson` | `course, chapter, lesson` | GET,POST | False |
| `portal_session.current` | `` | GET | True |
| `portal_session.overview` | `` | GET,POST | False |
| `profiles.me` | `` | GET,POST | False |
| `profiles.save_profile` | `data` | POST | False |
| `profiles.pending` | `page=0` | GET,POST | False |
| `profiles.review` | `profile, decision, reason, workspace=None` | POST | False |
| `profiles.search` | `query='', page=0` | GET,POST | False |
| `profiles.upload_image` | `kind` | POST | False |
| `profiles.relate` | `profile, kind` | POST | False |
| `profiles.change_relationship` | `relationship, status, reason=''` | POST | False |
| `profiles.relationships` | `profile` | GET,POST | False |
| `profiles.publish_update` | `headline, body, url=''` | POST | False |
| `profiles.followed_updates` | `page=0` | GET,POST | False |
| `private_contact.get_details` | `` | POST | False |
| `private_contact.save_details` | `data` | POST | False |
| `private_contact.request_whatsapp_code` | `phone` | POST | False |
| `api.bootstrap` | `` | GET,POST | False |
| `api.classrooms` | `page: int=0, search: str='', deleted: int=0` | GET,POST | False |
| `api.set_classroom_deleted` | `name: str, deleted: int` | POST | False |
| `api.classroom_detail` | `name: str, page: int=0` | GET,POST | False |
| `api.save_classroom` | `data: dict \| str` | POST | False |
| `api.save_session` | `data: dict \| str` | POST | False |
| `api.schedule` | `page: int=0, starts_on: str \| None=None, ends_on: str \| None=None` | GET,POST | False |
| `api.add_material` | `data: dict \| str` | POST | False |
| `api.post_announcement` | `data: dict \| str` | POST | False |
| `api.post_feedback` | `session: str, body: str` | POST | False |
| `api.news` | `page: int=0` | GET,POST | False |
| `api.publish_news` | `data: dict \| str` | POST | False |
| `api.members` | `page: int=0, role: str \| None=None, search: str \| None=None` | GET,POST | False |
| `api.add_member` | `data: dict \| str` | POST | False |
| `api.set_member_active` | `member_id: str, active: int` | POST | False |
| `api.teachers` | `search: str=''` | GET,POST | False |
| `api.notification_preferences` | `phone: str, opted_in: int, language: str='en'` | POST | False |
| `api.enroll` | `data: dict \| str` | POST | False |
| `api.enrollments` | `classroom: str, page: int=0` | GET,POST | False |
| `api.set_access` | `enrollment: str, override: str, reason: str, grace_until: str \| None=None` | POST | False |
| `api.invoices` | `page: int=0` | GET,POST | False |
| `api.notifications` | `page: int=0` | GET,POST | False |
| `api.dashboard_summary` | `` | GET,POST | False |
| `api.save_branding` | `data: dict \| str` | POST | False |
| `teaching.overview` | `` | GET,POST | False |
| `teaching.membership` | `name, status` | POST | False |
| `teaching.leave_class` | `classroom` | POST | False |
| `teaching.programmes` | `` | GET,POST | False |
| `teaching.save_programme` | `data` | POST | False |
| `teaching.enroll_programme` | `programme` | POST | False |
| `teaching.month_invoice` | `classroom, month` | POST | False |
| `operations.mark_attendance` | `session, student, status, note=''` | POST | False |
| `operations.join_session` | `session` | POST | False |
| `operations.attendance` | `classroom, session=None, page=0` | GET,POST | False |
| `operations.attendance_csv` | `classroom, session=None, page=0` | GET | False |
| `operations.create_ticket` | `subject, category, body` | POST | False |
| `operations.tickets` | `page=0` | GET,POST | False |
| `operations.thread` | `ticket, page=0` | GET,POST | False |
| `operations.reply` | `ticket, body, status=None` | POST | False |
| `papers.listing` | `classroom=None, page=0` | GET,POST | False |
| `papers.draft` | `data` | POST | False |
| `papers.detail` | `name` | GET,POST | False |
| `papers.publish` | `name, reviewed=False` | POST | False |
| `papers.archive` | `name` | POST | False |
| `papers.start` | `name` | POST | False |
| `papers.submit` | `attempt, answers` | POST | False |
| `papers.submissions` | `paper, page=0` | GET,POST | False |
| `papers.mark` | `attempt, score, feedback` | POST | False |
| `papers.upload_answer` | `attempt` | POST | False |
| `papers.answer_file` | `attempt` | GET | False |
| `papers.generate` | `classroom, topic, count=5, document=None, request_id=None` | POST | False |
| `materials.upload` | `classroom, purpose='original'` | POST | False |
| `materials.content` | `material, action='view'` | GET | False |
| `payments_lk.notify` | `**kwargs` | POST | True |
| `subscription_payments.quote` | `tenant, plan` | POST | False |
| `subscription_payments.checkout` | `quote` | POST | False |
| `subscription_payments.notify` | `**kwargs` | POST | True |
| `subscription_payments.status` | `attempt` | GET,POST | False |
| `saas.status` | `` | GET,POST | False |
| `saas.apply_manifest` | `payload, signature` | POST | True |
| `usage.summary` | `` | GET,POST | False |
| `notification_service.save_preferences` | `settings` | POST | False |
| `notification_service.inbox` | `page=0, unread=False` | GET,POST | False |
| `notification_service.mark_read` | `name` | POST | False |
| `notification_service.whatsapp_webhook` | `**kwargs` | GET,POST | True |
| `devices.register` | `device_id, token, platform` | POST | False |
| `devices.revoke` | `device` | POST | False |
| `ai.status` | `` | GET,POST | False |
| `ai.usage` | `tenant=False` | GET,POST | False |
| `ai.create_conversation` | `classroom, title='Learning conversation'` | POST | False |
| `ai.conversations` | `page=0` | GET,POST | False |
| `ai.conversation` | `name, page=0` | GET,POST | False |
| `ai.archive_conversation` | `name, delete=False` | POST | False |
| `ai.summary` | `classroom, document=None, instruction='', request_id=None` | POST | False |
| `ai.notes` | `classroom, document=None, instruction='', request_id=None` | POST | False |
| `ai.flashcards` | `classroom, document=None, instruction='', request_id=None` | POST | False |
| `ai.questions` | `classroom, document=None, instruction='', request_id=None` | POST | False |
| `ai.teacher_assistant` | `classroom, task='lesson_plan', document=None, instruction='', request_id=None` | POST | False |
| `ai.course_question` | `classroom, question, request_id, conversation=None, consent=False, mode='question'` | POST | False |
| `ai.chat` | `conversation, question, request_id, consent=False, mode='question'` | POST | False |
| `ai.search` | `classroom, query, request_id` | POST | False |
| `ai.assignment_feedback` | `attempt, request_id` | POST | False |
| `ai.recommendations` | `classroom` | GET,POST | False |
| `ai.admin_insights` | `classroom, explain=False, request_id=None` | POST | False |
| `knowledge.ingest` | `classroom, source_type, source_name` | POST | False |
| `knowledge.deactivate` | `document` | POST | False |
| `knowledge.documents` | `classroom` | GET,POST | False |
| `knowledge.reset_index` | `classroom, reason` | POST | False |
| `release.workspace` | `` | GET,POST | False |
| `release.billing` | `` | GET,POST | False |
| `release.control_room` | `page=0` | GET,POST | False |
| `release.custom_price` | `tenant, amount_minor, period, reason` | POST | False |
| `release.channels` | `` | GET,POST | False |
| `release.otp_status` | `` | GET,POST | False |
| `release.unread` | `` | GET,POST | False |
| `release.learning_sources` | `classroom` | GET,POST | False |
| `contact.status` | `` | POST | False |
| `contact.request_verification` | `email` | POST | False |
| `contact.verify` | `code` | POST | False |
| `contact.preferences` | `email_opt_in` | POST | False |
| `calendar_sync.connect` | `` | POST | False |
| `calendar_sync.callback` | `state=None, code=None, error=None` | GET | False |
| `calendar_sync.disconnect` | `` | POST | False |
| `youtube.connect` | `` | POST | False |
| `youtube.callback` | `state: str, code: str \| None=None, error: str \| None=None` | GET | False |
| `youtube.schedule_broadcast` | `session: str, privacy: str='unlisted', made_for_kids: bool \| None=None` | POST | False |
| `youtube.sync_broadcast` | `session: str` | POST | False |
| `youtube.transition_broadcast` | `session: str, status: str` | POST | False |
| `youtube.live_chat` | `session: str` | POST | False |
