# Source-derived SISU API and schema index

Generated from the preserved release source. Whitelisted does not mean public: each method retains its own auth/permission checks. Standard Frappe methods are outside this custom-app index.

## Whitelisted custom methods

| Method | Signature | Source line |
|---|---|---|
| `accounts.account_controls` | `` | `institute_lms/accounts.py:7` |
| `accounts.account_action` | `data` | `institute_lms/accounts.py:17` |
| `ai.status` | `` | `institute_lms/ai.py:13` |
| `ai.usage` | `tenant=False` | `institute_lms/ai.py:29` |
| `ai.create_conversation` | `classroom, title='Learning conversation'` | `institute_lms/ai.py:39` |
| `ai.conversations` | `page=0` | `institute_lms/ai.py:46` |
| `ai.conversation` | `name, page=0` | `institute_lms/ai.py:57` |
| `ai.archive_conversation` | `name, delete=False` | `institute_lms/ai.py:68` |
| `ai.summary` | `classroom, document=None, instruction='', request_id=None` | `institute_lms/ai.py:123` |
| `ai.notes` | `classroom, document=None, instruction='', request_id=None` | `institute_lms/ai.py:125` |
| `ai.flashcards` | `classroom, document=None, instruction='', request_id=None` | `institute_lms/ai.py:127` |
| `ai.questions` | `classroom, document=None, instruction='', request_id=None` | `institute_lms/ai.py:129` |
| `ai.teacher_assistant` | `classroom, task='lesson_plan', document=None, instruction='', request_id=None` | `institute_lms/ai.py:132` |
| `ai.course_question` | `classroom, question, request_id, conversation=None, consent=False, mode='question'` | `institute_lms/ai.py:138` |
| `ai.chat` | `conversation, question, request_id, consent=False, mode='question'` | `institute_lms/ai.py:183` |
| `ai.search` | `classroom, query, request_id` | `institute_lms/ai.py:188` |
| `ai.assignment_feedback` | `attempt, request_id` | `institute_lms/ai.py:200` |
| `ai.recommendations` | `classroom` | `institute_lms/ai.py:222` |
| `ai.admin_insights` | `classroom, explain=False, request_id=None` | `institute_lms/ai.py:229` |
| `ai_accounting.reconcile` | `request, decision, reason` | `institute_lms/ai_accounting.py:89` |
| `ai_provider.configure` | `data` | `institute_lms/ai_provider.py:12` |
| `api.bootstrap` | `` | `institute_lms/api.py:118` |
| `api.classrooms` | `page: int=0, search: str='', deleted: int=0` | `institute_lms/api.py:127` |
| `api.set_classroom_deleted` | `name: str, deleted: int` | `institute_lms/api.py:161` |
| `api.classroom_detail` | `name: str, page: int=0` | `institute_lms/api.py:178` |
| `api.save_classroom` | `data: dict \| str` | `institute_lms/api.py:192` |
| `api.save_session` | `data: dict \| str` | `institute_lms/api.py:267` |
| `api.schedule` | `page: int=0, starts_on: str \| None=None, ends_on: str \| None=None` | `institute_lms/api.py:294` |
| `api.add_material` | `data: dict \| str` | `institute_lms/api.py:309` |
| `api.post_announcement` | `data: dict \| str` | `institute_lms/api.py:336` |
| `api.post_feedback` | `session: str, body: str` | `institute_lms/api.py:347` |
| `api.news` | `page: int=0` | `institute_lms/api.py:363` |
| `api.publish_news` | `data: dict \| str` | `institute_lms/api.py:371` |
| `api.members` | `page: int=0, role: str \| None=None, search: str \| None=None` | `institute_lms/api.py:389` |
| `api.add_member` | `data: dict \| str` | `institute_lms/api.py:401` |
| `api.set_member_active` | `member_id: str, active: int` | `institute_lms/api.py:437` |
| `api.teachers` | `search: str=''` | `institute_lms/api.py:455` |
| `api.notification_preferences` | `phone: str, opted_in: int, language: str='en'` | `institute_lms/api.py:470` |
| `api.enroll` | `data: dict \| str` | `institute_lms/api.py:497` |
| `api.enrollments` | `classroom: str, page: int=0` | `institute_lms/api.py:541` |
| `api.set_access` | `enrollment: str, override: str, reason: str, grace_until: str \| None=None` | `institute_lms/api.py:547` |
| `api.invoices` | `page: int=0` | `institute_lms/api.py:565` |
| `api.notifications` | `page: int=0` | `institute_lms/api.py:582` |
| `api.dashboard_summary` | `` | `institute_lms/api.py:592` |
| `api.save_branding` | `data: dict \| str` | `institute_lms/api.py:608` |
| `billing.summary` | `` | `institute_lms/billing.py:15` |
| `calendar_sync.connect` | `` | `institute_lms/calendar_sync.py:32` |
| `calendar_sync.callback` | `state=None, code=None, error=None` | `institute_lms/calendar_sync.py:44` |
| `calendar_sync.disconnect` | `` | `institute_lms/calendar_sync.py:97` |
| `catalog.detail` | `profile, page=0` | `institute_lms/catalog.py:24` |
| `catalog.publishing_options` | `` | `institute_lms/catalog.py:34` |
| `catalog.join_class` | `classroom` | `institute_lms/catalog.py:60` |
| `contact.status` | `` | `institute_lms/contact.py:30` |
| `contact.request_verification` | `email` | `institute_lms/contact.py:38` |
| `contact.verify` | `code` | `institute_lms/contact.py:58` |
| `contact.preferences` | `email_opt_in` | `institute_lms/contact.py:78` |
| `devices.register` | `device_id, token, platform` | `institute_lms/devices.py:8` |
| `devices.revoke` | `device` | `institute_lms/devices.py:25` |
| `health.live` | `` | `institute_lms/health.py:7` |
| `health.readiness` | `` | `institute_lms/health.py:16` |
| `invitations.invite_teacher` | `email` | `institute_lms/invitations.py:18` |
| `invitations.list_invitations` | `` | `institute_lms/invitations.py:34` |
| `invitations.respond` | `name, decision` | `institute_lms/invitations.py:45` |
| `invitations.request_by_email` | `email` | `institute_lms/invitations.py:60` |
| `knowledge.ingest` | `classroom, source_type, source_name` | `institute_lms/knowledge.py:45` |
| `knowledge.deactivate` | `document` | `institute_lms/knowledge.py:165` |
| `knowledge.documents` | `classroom` | `institute_lms/knowledge.py:171` |
| `knowledge.reset_index` | `classroom, reason` | `institute_lms/knowledge.py:176` |
| `materials.upload` | `classroom, purpose='original'` | `institute_lms/materials.py:12` |
| `materials.content` | `material, action='view'` | `institute_lms/materials.py:66` |
| `mobile_api.current` | `` | `institute_lms/mobile_api.py:5` |
| `mobile_api.classes` | `page=0` | `institute_lms/mobile_api.py:11` |
| `mobile_api.enrollments` | `page=0` | `institute_lms/mobile_api.py:16` |
| `mobile_api.lesson` | `course, chapter, lesson` | `institute_lms/mobile_api.py:23` |
| `mobile_auth.authorize` | `challenge, state, redirect_uri` | `institute_lms/mobile_auth.py:26` |
| `mobile_auth.approve` | `challenge, state, redirect_uri` | `institute_lms/mobile_auth.py:41` |
| `mobile_auth.exchange` | `code, verifier, redirect_uri, device_id` | `institute_lms/mobile_auth.py:53` |
| `mobile_auth.logout` | `session=None` | `institute_lms/mobile_auth.py:89` |
| `mobile_verification.request_code` | `phone` | `institute_lms/mobile_verification.py:10` |
| `mobile_verification.verify` | `code, channel='SMS', challenge=None` | `institute_lms/mobile_verification.py:16` |
| `mobile_verification.claim_trial` | `` | `institute_lms/mobile_verification.py:21` |
| `notification_service.save_preferences` | `settings` | `institute_lms/notification_service.py:50` |
| `notification_service.inbox` | `page=0, unread=False` | `institute_lms/notification_service.py:67` |
| `notification_service.mark_read` | `name` | `institute_lms/notification_service.py:78` |
| `notification_service.whatsapp_webhook` | `**kwargs` | `institute_lms/notification_service.py:123` |
| `operations.mark_attendance` | `session, student, status, note=''` | `institute_lms/operations.py:27` |
| `operations.join_session` | `session` | `institute_lms/operations.py:35` |
| `operations.attendance` | `classroom, session=None, page=0` | `institute_lms/operations.py:54` |
| `operations.attendance_csv` | `classroom, session=None, page=0` | `institute_lms/operations.py:57` |
| `operations.create_ticket` | `subject, category, body` | `institute_lms/operations.py:66` |
| `operations.tickets` | `page=0` | `institute_lms/operations.py:82` |
| `operations.thread` | `ticket, page=0` | `institute_lms/operations.py:89` |
| `operations.reply` | `ticket, body, status=None` | `institute_lms/operations.py:95` |
| `owner_pricing.assign` | `data` | `institute_lms/owner_pricing.py:30` |
| `owner_pricing.assignments` | `page=0` | `institute_lms/owner_pricing.py:57` |
| `owner_pricing.quote` | `product` | `institute_lms/owner_pricing.py:62` |
| `owner_pricing.classroom_price` | `classroom, amount_minor, reason` | `institute_lms/owner_pricing.py:77` |
| `owner_pricing.entitlements` | `` | `institute_lms/owner_pricing.py:99` |
| `owner_pricing.grant` | `customer, product, expires_at, reason` | `institute_lms/owner_pricing.py:104` |
| `owner_pricing.revoke` | `name, reason` | `institute_lms/owner_pricing.py:116` |
| `papers.listing` | `classroom=None, page=0` | `institute_lms/papers.py:23` |
| `papers.draft` | `data` | `institute_lms/papers.py:34` |
| `papers.detail` | `name` | `institute_lms/papers.py:63` |
| `papers.publish` | `name, reviewed=False` | `institute_lms/papers.py:70` |
| `papers.archive` | `name` | `institute_lms/papers.py:79` |
| `papers.start` | `name` | `institute_lms/papers.py:85` |
| `papers.submit` | `attempt, answers` | `institute_lms/papers.py:103` |
| `papers.submissions` | `paper, page=0` | `institute_lms/papers.py:116` |
| `papers.mark` | `attempt, score, feedback` | `institute_lms/papers.py:124` |
| `papers.upload_answer` | `attempt` | `institute_lms/papers.py:134` |
| `papers.answer_file` | `attempt` | `institute_lms/papers.py:152` |
| `papers.generate` | `classroom, topic, count=5, document=None, request_id=None` | `institute_lms/papers.py:166` |
| `payments.checkout` | `invoice: str, customer: dict \| str` | `institute_lms/payments.py:8` |
| `payments.notify` | `**kwargs` | `institute_lms/payments.py:41` |
| `payments_lk.notify` | `**kwargs` | `institute_lms/payments_lk.py:96` |
| `platform.register` | `title, code, site_hostname, admin_contact, plan='STARTER'` | `institute_lms/platform.py:28` |
| `platform.organizations` | `page=0` | `institute_lms/platform.py:56` |
| `platform.configure_plan` | `plan, features, limits, price_minor, period_days=30, reason=''` | `institute_lms/platform.py:66` |
| `platform.update_organization` | `tenant, enabled, reason, custom_domain=None` | `institute_lms/platform.py:79` |
| `platform.override` | `tenant, values, reason` | `institute_lms/platform.py:92` |
| `platform.trial` | `tenant, days, reason` | `institute_lms/platform.py:102` |
| `platform.subscription_state` | `tenant, state, reason, grace_until=None` | `institute_lms/platform.py:116` |
| `platform.manifest` | `tenant` | `institute_lms/platform.py:129` |
| `platform.provisioning_spec` | `job` | `institute_lms/platform.py:146` |
| `platform.provisioning_result` | `job, status, reason` | `institute_lms/platform.py:153` |
| `platform.invite_billing_contact` | `tenant` | `institute_lms/platform.py:162` |
| `platform.reactivate` | `tenant, reason` | `institute_lms/platform.py:170` |
| `portal_policy.public` | `` | `institute_lms/portal_policy.py:7` |
| `portal_policy.save` | `privacy_policy_url='', privacy_policy_version='', provider_applications_enabled=0` | `institute_lms/portal_policy.py:14` |
| `portal_policy.google_start` | `` | `institute_lms/portal_policy.py:27` |
| `portal_session.current` | `` | `institute_lms/portal_session.py:6` |
| `portal_session.overview` | `` | `institute_lms/portal_session.py:29` |
| `private_contact.get_details` | `` | `institute_lms/private_contact.py:14` |
| `private_contact.save_details` | `data` | `institute_lms/private_contact.py:22` |
| `private_contact.request_whatsapp_code` | `phone` | `institute_lms/private_contact.py:38` |
| `profiles.me` | `` | `institute_lms/profiles.py:34` |
| `profiles.save_profile` | `data` | `institute_lms/profiles.py:39` |
| `profiles.pending` | `page=0` | `institute_lms/profiles.py:78` |
| `profiles.review` | `profile, decision, reason, workspace=None` | `institute_lms/profiles.py:83` |
| `profiles.search` | `query='', page=0` | `institute_lms/profiles.py:102` |
| `profiles.upload_image` | `kind` | `institute_lms/profiles.py:109` |
| `profiles.relate` | `profile, kind` | `institute_lms/profiles.py:137` |
| `profiles.change_relationship` | `relationship, status, reason=''` | `institute_lms/profiles.py:156` |
| `profiles.relationships` | `profile` | `institute_lms/profiles.py:174` |
| `profiles.publish_update` | `headline, body, url=''` | `institute_lms/profiles.py:182` |
| `profiles.followed_updates` | `page=0` | `institute_lms/profiles.py:195` |
| `registration.request_code` | `data` | `institute_lms/registration.py:28` |
| `registration.verify_code` | `challenge, code` | `institute_lms/registration.py:57` |
| `registration.applications` | `page=0` | `institute_lms/registration.py:93` |
| `registration.review_application` | `name, decision, reason` | `institute_lms/registration.py:98` |
| `release.workspace` | `` | `institute_lms/release.py:17` |
| `release.billing` | `` | `institute_lms/release.py:35` |
| `release.control_room` | `page=0` | `institute_lms/release.py:52` |
| `release.custom_price` | `tenant, amount_minor, period, reason` | `institute_lms/release.py:64` |
| `release.channels` | `` | `institute_lms/release.py:84` |
| `release.otp_status` | `` | `institute_lms/release.py:105` |
| `release.unread` | `` | `institute_lms/release.py:115` |
| `release.learning_sources` | `classroom` | `institute_lms/release.py:125` |
| `retention.configure_course` | `classroom, expires_at, grace_days=0, archive_days=30, delete_days=180` | `institute_lms/retention.py:31` |
| `retention.purge_orphan` | `object_name, reason` | `institute_lms/retention.py:78` |
| `saas.status` | `` | `institute_lms/saas.py:51` |
| `saas.apply_manifest` | `payload, signature` | `institute_lms/saas.py:56` |
| `soul.status` | `` | `institute_lms/soul.py:25` |
| `soul.configure` | `api_key=None, model='gpt-4.1-mini', enabled=False, remove_key=False` | `institute_lms/soul.py:36` |
| `soul.chat` | `message, page='dashboard', language='en', history=None, consent=False, request_id=None` | `institute_lms/soul.py:89` |
| `soul.test_connection` | `` | `institute_lms/soul.py:128` |
| `subscription_payments.quote` | `tenant, plan` | `institute_lms/subscription_payments.py:29` |
| `subscription_payments.checkout` | `quote` | `institute_lms/subscription_payments.py:58` |
| `subscription_payments.notify` | `**kwargs` | `institute_lms/subscription_payments.py:114` |
| `subscription_payments.status` | `attempt` | `institute_lms/subscription_payments.py:148` |
| `teaching.overview` | `` | `institute_lms/teaching.py:32` |
| `teaching.membership` | `name, status` | `institute_lms/teaching.py:53` |
| `teaching.leave_class` | `classroom` | `institute_lms/teaching.py:75` |
| `teaching.programmes` | `` | `institute_lms/teaching.py:84` |
| `teaching.save_programme` | `data` | `institute_lms/teaching.py:99` |
| `teaching.enroll_programme` | `programme` | `institute_lms/teaching.py:134` |
| `teaching.month_invoice` | `classroom, month` | `institute_lms/teaching.py:157` |
| `usage.summary` | `` | `institute_lms/usage.py:37` |
| `wallet.provision_wallet` | `user, beneficiary, country, currency, institute=None` | `institute_lms/wallet.py:77` |
| `wallet.dashboard` | `wallet=None, page=0` | `institute_lms/wallet.py:103` |
| `wallet.submit_method` | `wallet, data` | `institute_lms/wallet.py:118` |
| `wallet.review_method` | `method, decision, reason` | `institute_lms/wallet.py:132` |
| `wallet.request_payout` | `wallet, method, amount, request_key` | `institute_lms/wallet.py:146` |
| `wallet.update_payout` | `request, status, reference='', reason='', receipt=None` | `institute_lms/wallet.py:165` |
| `wallet.admin_queue` | `region='Local', page=0` | `institute_lms/wallet.py:187` |
| `wallet.reveal_method` | `method` | `institute_lms/wallet.py:194` |
| `wallet.export_local` | `requests` | `institute_lms/wallet.py:200` |
| `youtube.connect` | `` | `institute_lms/youtube.py:21` |
| `youtube.callback` | `state: str, code: str \| None=None, error: str \| None=None` | `institute_lms/youtube.py:33` |
| `youtube.schedule_broadcast` | `session: str, privacy: str='unlisted', made_for_kids: bool \| None=None` | `institute_lms/youtube.py:76` |
| `youtube.sync_broadcast` | `session: str` | `institute_lms/youtube.py:107` |
| `youtube.transition_broadcast` | `session: str, status: str` | `institute_lms/youtube.py:132` |
| `youtube.live_chat` | `session: str` | `institute_lms/youtube.py:152` |

## Custom DocTypes

| DocType | Fields (source order) | Schema file |
|---|---|---|
| IL Access Audit | institute, enrollment, actor, before_state, after_state, reason | `institute_lms/institute_lms/doctype/il_access_audit/il_access_audit.json` |
| IL Account Request | institute, requested_by, kind, reason, status, resolution | `institute_lms/institute_lms/doctype/il_account_request/il_account_request.json` |
| IL AI Conversation | institute, user, classroom, member_role, title, status, archived_at, delete_after | `institute_lms/institute_lms/doctype/il_ai_conversation/il_ai_conversation.json` |
| IL AI Message | conversation, request_key, role, content, citations, model, provider_request_id | `institute_lms/institute_lms/doctype/il_ai_message/il_ai_message.json` |
| IL AI Usage | request_key, payload_hash, institute, user, classroom, subscription, feature, request_type, period, provider, model, state, reserved_units, charged_units, input_tokens, cached_tokens, output_tokens, total_tokens, usage_reported, estimated_cost, cost_currency, rate_snapshot, provider_requests, result, error_code, completed_at | `institute_lms/institute_lms/doctype/il_ai_usage/il_ai_usage.json` |
| IL Announcement | institute, classroom, headline, body | `institute_lms/institute_lms/doctype/il_announcement/il_announcement.json` |
| IL Attendance | institute, classroom, session, student, attendance_key, channel, status, recorded_at, recorded_by, note | `institute_lms/institute_lms/doctype/il_attendance/il_attendance.json` |
| IL Calendar Connection | institute, member, google_email, calendar_id, refresh_token, status, last_synced | `institute_lms/institute_lms/doctype/il_calendar_connection/il_calendar_connection.json` |
| IL Calendar Job | institute, member, event_key, session, connection, status, attempts, next_attempt, last_error | `institute_lms/institute_lms/doctype/il_calendar_job/il_calendar_job.json` |
| IL Checkout Quote | customer, assignment, product, currency, period, total_minor, breakdown, expires_at, status, tenant_id, plan_snapshot | `institute_lms/institute_lms/doctype/il_checkout_quote/il_checkout_quote.json` |
| IL Classroom | institute, title, teacher, subject, description, profile_image, cover_image, font, fee, exam_date, motivation, comments_enabled, allow_teacher_access_override, active, lms_course, exam_type, curriculum, grade, teaching_medium, public_provider, published, fee_mode, schedule_label, owner_type, owner_user, teacher_access, teacher_assignment_active, billing_type, programme, expires_at, course_grace_until, archive_at, delete_at, lifecycle | `institute_lms/institute_lms/doctype/il_classroom/il_classroom.json` |
| IL Device Token | user, device_id, platform, token, token_hash, revoked | `institute_lms/institute_lms/doctype/il_device_token/il_device_token.json` |
| IL Enrollment | institute, classroom, student, fee, active, access_override, grace_until, override_reason, programme_enrollment, expires_at, course_grace_until, archive_at, delete_at, lifecycle | `institute_lms/institute_lms/doctype/il_enrollment/il_enrollment.json` |
| IL Feedback | institute, classroom, session, student, body | `institute_lms/institute_lms/doctype/il_feedback/il_feedback.json` |
| IL Institute | code, title, logo, accent, base_fee, billing_day, support_email, phone, address, city, language, school_mode | `institute_lms/institute_lms/doctype/il_institute/il_institute.json` |
| IL Institute Bill | institute, period, active_students, included_students, extra_students, unit_rate, base_fee, total, status, paid_at, reference | `institute_lms/institute_lms/doctype/il_institute_bill/il_institute_bill.json` |
| IL Invoice | institute, enrollment, student, classroom, amount, due_date, installment, status, paid_at, payment_id, receipt_number, gateway_status, gateway_checkout_id, gateway_request_key, gateway_request, gateway_requested_at, gateway_mode, currency, payout_wallet, beneficiary_minor, platform_minor, pricing_assignment, billing_month, billing_key | `institute_lms/institute_lms/doctype/il_invoice/il_invoice.json` |
| IL Knowledge Chunk | document, ordinal, section, text, text_hash | `institute_lms/institute_lms/doctype/il_knowledge_chunk/il_knowledge_chunk.json` |
| IL Knowledge Document | source_key, institute, classroom, source_type, source_name, source_file, source_hash, source_revision, title, mime_type, version, requested_by, index, provider_file, status, enabled, error_code, indexed_at, delete_after, cleanup_attempts | `institute_lms/institute_lms/doctype/il_knowledge_document/il_knowledge_document.json` |
| IL Knowledge Index | index_key, institute, classroom, tenant_id, provider_store, status, error_code | `institute_lms/institute_lms/doctype/il_knowledge_index/il_knowledge_index.json` |
| IL Material | institute, classroom, session, title, kind, url, youtube_id, description, file_id, preview_file_id, filename, file_type, file_size, download_policy | `institute_lms/institute_lms/doctype/il_material/il_material.json` |
| IL Member | institute, user, role, full_name, phone, whatsapp_opt_in, language, active, soul_ai_enabled, contact_email, contact_email_verified, email_opt_in | `institute_lms/institute_lms/doctype/il_member/il_member.json` |
| IL Mobile Session | user, device_id, token_hash, google_authenticated, expires_at, revoked | `institute_lms/institute_lms/doctype/il_mobile_session/il_mobile_session.json` |
| IL News | institute, headline, description, cta_label, cta_url, starts_on, ends_on, images, author | `institute_lms/institute_lms/doctype/il_news/il_news.json` |
| IL News Image | image, alt | `institute_lms/institute_lms/doctype/il_news_image/il_news_image.json` |
| IL Notification | institute, recipient, event_key, body, status, attempts, next_attempt, provider_id, last_error, channel, event, device, sent_at, failed_at | `institute_lms/institute_lms/doctype/il_notification/il_notification.json` |
| IL Notification Event | event_key, event_type, user, recipient, institute, body, read_at | `institute_lms/institute_lms/doctype/il_notification_event/il_notification_event.json` |
| IL Notification Preference | user, settings | `institute_lms/institute_lms/doctype/il_notification_preference/il_notification_preference.json` |
| IL Organization | tenant_id, title, institute_code, site_hostname, custom_domain, admin_contact, plan, enabled, provisioning_state, revision | `institute_lms/institute_lms/doctype/il_organization/il_organization.json` |
| IL Paper | institute, classroom, title, description, source, status, questions, duration_minutes, opens_at, closes_at, max_marks, material, allow_upload, published_by, published_at, ai_request_key | `institute_lms/institute_lms/doctype/il_paper/il_paper.json` |
| IL Paper Attempt | paper, student, attempt_key, started_at, deadline, status, answers, submitted_at, score, feedback, graded_by, file_id | `institute_lms/institute_lms/doctype/il_paper_attempt/il_paper_attempt.json` |
| IL Payment Attempt | attempt_id, quote, tenant_id, amount_minor, currency, mode, status, request_key, request, snapshot, checkout_id, payment_id | `institute_lms/institute_lms/doctype/il_payment_attempt/il_payment_attempt.json` |
| IL Payment Transaction | attempt, payment_id, tenant_id, amount_minor, currency, settled_at | `institute_lms/institute_lms/doctype/il_payment_transaction/il_payment_transaction.json` |
| IL Payout Audit | action, actor, reference, details | `institute_lms/institute_lms/doctype/il_payout_audit/il_payout_audit.json` |
| IL Payout Method | wallet, kind, country, masked_label, secret_details, status, submitted_by, reviewed_by, reviewed_at, review_reason | `institute_lms/institute_lms/doctype/il_payout_method/il_payout_method.json` |
| IL Payout Request | wallet, method, request_key, amount_minor, currency, region, status, transaction_reference, receipt, reason, processed_by, completed_at, settlement_key | `institute_lms/institute_lms/doctype/il_payout_request/il_payout_request.json` |
| IL Portal Settings | privacy_policy_url, privacy_policy_version, provider_applications_enabled | `institute_lms/institute_lms/doctype/il_portal_settings/il_portal_settings.json` |
| IL Price Assignment | customer, customer_kind, institute, product, currency, period, base_minor, included_units, unit_minor, discount_bps, tax_bps, active, reason, assigned_by, tenant_id | `institute_lms/institute_lms/doctype/il_price_assignment/il_price_assignment.json` |
| IL Private Contact | user, date_of_birth, gender, gender_description, contact_phone, city, address, guardian_name, guardian_relationship, guardian_phone, guardian_email, guardian_permission, whatsapp_phone, whatsapp_opt_in, notification_language, consent_at | `institute_lms/institute_lms/doctype/il_private_contact/il_private_contact.json` |
| IL Product Entitlement | customer, product, expires_at, revoked, reason, granted_by | `institute_lms/institute_lms/doctype/il_product_entitlement/il_product_entitlement.json` |
| IL Profile Relationship | relationship_key, profile, user, kind, status, reviewed_by, reason | `institute_lms/institute_lms/doctype/il_profile_relationship/il_profile_relationship.json` |
| IL Programme | institute, provider, title, description, cover_image, duration_months, fee, currency, starts_on, ends_on, active, modules | `institute_lms/institute_lms/doctype/il_programme/il_programme.json` |
| IL Programme Enrollment | programme, student, billing_enrollment, active | `institute_lms/institute_lms/doctype/il_programme_enrollment/il_programme_enrollment.json` |
| IL Programme Module | classroom, title, teacher, duration_weeks, starts_on | `institute_lms/institute_lms/doctype/il_programme_module/il_programme_module.json` |
| IL Provider Update | profile, headline, body, url, expires_at | `institute_lms/institute_lms/doctype/il_provider_update/il_provider_update.json` |
| IL Provisioning Job | organization, status, detail | `institute_lms/institute_lms/doctype/il_provisioning_job/il_provisioning_job.json` |
| IL Public Profile | user, username, display_name, kind, country, status, code, bio, socials, curriculum, languages, grades, is_school, review_reason, reviewed_by, profile_image, cover_image, tagline, qualifications, workspace | `institute_lms/institute_lms/doctype/il_public_profile/il_public_profile.json` |
| IL Registration Request | email, account_type, status, email_verified, details, review_reason, reviewed_by | `institute_lms/institute_lms/doctype/il_registration_request/il_registration_request.json` |
| IL SaaS Audit | action, reference, actor, details | `institute_lms/institute_lms/doctype/il_saas_audit/il_saas_audit.json` |
| IL SaaS Plan | plan_name, features, limits, price_minor, period_days, version | `institute_lms/institute_lms/doctype/il_saas_plan/il_saas_plan.json` |
| IL Session | institute, classroom, title, description, starts_at, ends_at, mode, location, youtube_id, youtube_privacy, status, comments, meeting_provider, meeting_url | `institute_lms/institute_lms/doctype/il_session/il_session.json` |
| IL SOUL Settings | enabled, api_key, model, moderation_model, retrieval_backend, retrieval_model, request_timeout, max_output_tokens, model_rates, feature_credits, hosted_retrieval_reviewed, conversation_days, usage_detail_days, user_daily_limit, site_daily_limit, max_documents_per_course | `institute_lms/institute_lms/doctype/il_soul_settings/il_soul_settings.json` |
| IL Stored Object | file, institute, classroom, owner_user, bytes, backend, storage_key, status, expiry_at, archive_at, delete_at, legal_hold, course | `institute_lms/institute_lms/doctype/il_stored_object/il_stored_object.json` |
| IL Subscription | tenant_id, plan, state, enabled, starts_at, ends_at, grace_until, lease_until, revision, features, limits, overrides, last_payment, trial_used, support_tier | `institute_lms/institute_lms/doctype/il_subscription/il_subscription.json` |
| IL Support Reply | ticket, author_user, body | `institute_lms/institute_lms/doctype/il_support_reply/il_support_reply.json` |
| IL Support Ticket | institute, requester, subject, status, category | `institute_lms/institute_lms/doctype/il_support_ticket/il_support_ticket.json` |
| IL Teacher Invitation | institute, profile, invite_email, invited_by, expires_at, status, responded_at | `institute_lms/institute_lms/doctype/il_teacher_invitation/il_teacher_invitation.json` |
| IL Trial Claim | user, verified_card_reference, expires_at, status | `institute_lms/institute_lms/doctype/il_trial_claim/il_trial_claim.json` |
| IL Usage Entry | event_key, tenant_id, resource, period, quantity, reference | `institute_lms/institute_lms/doctype/il_usage_entry/il_usage_entry.json` |
| IL Verified Phone | user, phone, verified_at | `institute_lms/institute_lms/doctype/il_verified_phone/il_verified_phone.json` |
| IL Wallet | identity_key, owner_user, beneficiary, institute, country, currency, available_minor, held_minor, enabled | `institute_lms/institute_lms/doctype/il_wallet/il_wallet.json` |
| IL Wallet Transaction | wallet, event_key, kind, available_delta, held_delta, available_after, held_after, invoice, payout, reference, actor, reason | `institute_lms/institute_lms/doctype/il_wallet_transaction/il_wallet_transaction.json` |
| IL Webhook Event | event_key, attempt, event_type, provider_id, received_at | `institute_lms/institute_lms/doctype/il_webhook_event/il_webhook_event.json` |
| IL YouTube Connection | institute, member, refresh_token, channel_title | `institute_lms/institute_lms/doctype/il_youtube_connection/il_youtube_connection.json` |
