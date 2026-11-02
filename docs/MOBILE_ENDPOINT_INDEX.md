# Generated whitelisted endpoint index

Source snapshot; decorators describe transport availability, not role authorization or live test status. All methods still enforce their server guards. Responses are wrapped in `message`; inspect linked source for branch-specific payloads and errors. Public shared-campus integration guidance: [handoff](MOBILE_PUBLIC_CAMPUS_HANDOFF.md).

| Endpoint | HTTP methods | Guest allowed | Arguments | Source |
|---|---|---|---|---|
| `institute_lms.account_billing.status` | ['POST'] | False | `` | [account_billing.py:147](../institute_lms/account_billing.py#L147) |
| `institute_lms.account_billing.preferences` | ['POST'] | False | `plan, billing_email, payment_method='Card'` | [account_billing.py:161](../institute_lms/account_billing.py#L161) |
| `institute_lms.account_billing.request_country` | ['POST'] | False | `country` | [account_billing.py:176](../institute_lms/account_billing.py#L176) |
| `institute_lms.account_billing.admin_accounts` | ['POST'] | False | `` | [account_billing.py:189](../institute_lms/account_billing.py#L189) |
| `institute_lms.account_billing.verify_country` | ['POST'] | False | `subscription, country, reason` | [account_billing.py:195](../institute_lms/account_billing.py#L195) |
| `institute_lms.account_billing.invoice` | ['POST'] | False | `` | [account_billing.py:237](../institute_lms/account_billing.py#L237) |
| `institute_lms.account_billing.cancel` | ['POST'] | False | `cancel=True` | [account_billing.py:246](../institute_lms/account_billing.py#L246) |
| `institute_lms.account_billing.confirm_bank_payment` | ['POST'] | False | `invoice, reference, amount_minor, reason` | [account_billing.py:285](../institute_lms/account_billing.py#L285) |
| `institute_lms.account_billing.document` | ['POST'] | False | `invoice` | [account_billing.py:313](../institute_lms/account_billing.py#L313) |
| `institute_lms.accounts.account_controls` | ['POST'] | False | `` | [accounts.py:7](../institute_lms/accounts.py#L7) |
| `institute_lms.accounts.account_action` | ['POST'] | False | `data` | [accounts.py:17](../institute_lms/accounts.py#L17) |
| `institute_lms.ai.status` | Framework default | False | `` | [ai.py:13](../institute_lms/ai.py#L13) |
| `institute_lms.ai.usage` | Framework default | False | `tenant=False` | [ai.py:33](../institute_lms/ai.py#L33) |
| `institute_lms.ai.create_conversation` | ['POST'] | False | `classroom, title='Learning conversation'` | [ai.py:43](../institute_lms/ai.py#L43) |
| `institute_lms.ai.conversations` | Framework default | False | `page=0` | [ai.py:50](../institute_lms/ai.py#L50) |
| `institute_lms.ai.conversation` | Framework default | False | `name, page=0` | [ai.py:61](../institute_lms/ai.py#L61) |
| `institute_lms.ai.archive_conversation` | ['POST'] | False | `name, delete=False` | [ai.py:72](../institute_lms/ai.py#L72) |
| `institute_lms.ai.summary` | ['POST'] | False | `classroom, document=None, instruction='', request_id=None` | [ai.py:127](../institute_lms/ai.py#L127) |
| `institute_lms.ai.notes` | ['POST'] | False | `classroom, document=None, instruction='', request_id=None` | [ai.py:129](../institute_lms/ai.py#L129) |
| `institute_lms.ai.flashcards` | ['POST'] | False | `classroom, document=None, instruction='', request_id=None` | [ai.py:131](../institute_lms/ai.py#L131) |
| `institute_lms.ai.questions` | ['POST'] | False | `classroom, document=None, instruction='', request_id=None` | [ai.py:133](../institute_lms/ai.py#L133) |
| `institute_lms.ai.teacher_assistant` | ['POST'] | False | `classroom, task='lesson_plan', document=None, instruction='', request_id=None` | [ai.py:136](../institute_lms/ai.py#L136) |
| `institute_lms.ai.course_question` | ['POST'] | False | `classroom, question, request_id, conversation=None, consent=False, mode='question'` | [ai.py:142](../institute_lms/ai.py#L142) |
| `institute_lms.ai.chat` | ['POST'] | False | `conversation, question, request_id, consent=False, mode='question'` | [ai.py:187](../institute_lms/ai.py#L187) |
| `institute_lms.ai.search` | ['POST'] | False | `classroom, query, request_id` | [ai.py:192](../institute_lms/ai.py#L192) |
| `institute_lms.ai.assignment_feedback` | ['POST'] | False | `attempt, request_id` | [ai.py:204](../institute_lms/ai.py#L204) |
| `institute_lms.ai.recommendations` | Framework default | False | `classroom` | [ai.py:226](../institute_lms/ai.py#L226) |
| `institute_lms.ai.admin_insights` | ['POST'] | False | `classroom, explain=False, request_id=None` | [ai.py:233](../institute_lms/ai.py#L233) |
| `institute_lms.ai_accounting.reconcile` | ['POST'] | False | `request, decision, reason` | [ai_accounting.py:93](../institute_lms/ai_accounting.py#L93) |
| `institute_lms.ai_credits.status` | Framework default | False | `` | [ai_credits.py:26](../institute_lms/ai_credits.py#L26) |
| `institute_lms.ai_credits.management` | Framework default | False | `search='', role=None, page=0` | [ai_credits.py:46](../institute_lms/ai_credits.py#L46) |
| `institute_lms.ai_credits.configure` | ['POST'] | False | `mode, allocations=None, reason=''` | [ai_credits.py:68](../institute_lms/ai_credits.py#L68) |
| `institute_lms.ai_provider.configure` | ['POST'] | False | `data` | [ai_provider.py:12](../institute_lms/ai_provider.py#L12) |
| `institute_lms.api.bootstrap` | Framework default | False | `` | [api.py:146](../institute_lms/api.py#L146) |
| `institute_lms.api.classrooms` | Framework default | False | `page: int=0, search: str='', deleted: int=0` | [api.py:162](../institute_lms/api.py#L162) |
| `institute_lms.api.set_classroom_deleted` | ['POST'] | False | `name: str, deleted: int` | [api.py:196](../institute_lms/api.py#L196) |
| `institute_lms.api.classroom_detail` | Framework default | False | `name: str, page: int=0` | [api.py:213](../institute_lms/api.py#L213) |
| `institute_lms.api.save_classroom` | ['POST'] | False | `data: dict | str` | [api.py:241](../institute_lms/api.py#L241) |
| `institute_lms.api.create_internal_classroom` | ['POST'] | False | `data: dict | str` | [api.py:246](../institute_lms/api.py#L246) |
| `institute_lms.api.save_session` | ['POST'] | False | `data: dict | str` | [api.py:352](../institute_lms/api.py#L352) |
| `institute_lms.api.schedule` | Framework default | False | `page: int=0, starts_on: str | None=None, ends_on: str | None=None` | [api.py:379](../institute_lms/api.py#L379) |
| `institute_lms.api.add_material` | ['POST'] | False | `data: dict | str` | [api.py:394](../institute_lms/api.py#L394) |
| `institute_lms.api.post_announcement` | ['POST'] | False | `data: dict | str` | [api.py:424](../institute_lms/api.py#L424) |
| `institute_lms.api.post_feedback` | ['POST'] | False | `session: str, body: str` | [api.py:435](../institute_lms/api.py#L435) |
| `institute_lms.api.news` | Framework default | False | `page: int=0` | [api.py:451](../institute_lms/api.py#L451) |
| `institute_lms.api.publish_news` | ['POST'] | False | `data: dict | str` | [api.py:462](../institute_lms/api.py#L462) |
| `institute_lms.api.members` | Framework default | False | `page: int=0, role: str | None=None, search: str | None=None` | [api.py:482](../institute_lms/api.py#L482) |
| `institute_lms.api.add_member` | ['POST'] | False | `data: dict | str` | [api.py:494](../institute_lms/api.py#L494) |
| `institute_lms.api.set_member_active` | ['POST'] | False | `member_id: str, active: int` | [api.py:530](../institute_lms/api.py#L530) |
| `institute_lms.api.teachers` | Framework default | False | `search: str=''` | [api.py:553](../institute_lms/api.py#L553) |
| `institute_lms.api.notification_preferences` | ['POST'] | False | `phone: str, opted_in: int, language: str='en'` | [api.py:568](../institute_lms/api.py#L568) |
| `institute_lms.api.enroll` | ['POST'] | False | `data: dict | str` | [api.py:595](../institute_lms/api.py#L595) |
| `institute_lms.api.enrollments` | Framework default | False | `classroom: str, page: int=0` | [api.py:642](../institute_lms/api.py#L642) |
| `institute_lms.api.set_access` | ['POST'] | False | `enrollment: str, override: str, reason: str, grace_until: str | None=None` | [api.py:648](../institute_lms/api.py#L648) |
| `institute_lms.api.invoices` | Framework default | False | `page: int=0` | [api.py:666](../institute_lms/api.py#L666) |
| `institute_lms.api.notifications` | Framework default | False | `page: int=0` | [api.py:683](../institute_lms/api.py#L683) |
| `institute_lms.api.dashboard_summary` | Framework default | False | `` | [api.py:693](../institute_lms/api.py#L693) |
| `institute_lms.api.save_branding` | ['POST'] | False | `data: dict | str` | [api.py:711](../institute_lms/api.py#L711) |
| `institute_lms.attendance_register.roster` | Framework default | False | `session, page=0` | [attendance_register.py:35](../institute_lms/attendance_register.py#L35) |
| `institute_lms.attendance_register.submit` | ['POST'] | False | `session, entries` | [attendance_register.py:59](../institute_lms/attendance_register.py#L59) |
| `institute_lms.billing.summary` | Framework default | False | `` | [billing.py:15](../institute_lms/billing.py#L15) |
| `institute_lms.billing_bridge.request` | ['POST'] | False | `action='summary', args=None` | [billing_bridge.py:13](../institute_lms/billing_bridge.py#L13) |
| `institute_lms.billing_bridge.receive` | ['POST'] | True | `payload, signature` | [billing_bridge.py:35](../institute_lms/billing_bridge.py#L35) |
| `institute_lms.billing_transport.invoices` | ['POST'] | False | `tenant, page=0` | [billing_transport.py:39](../institute_lms/billing_transport.py#L39) |
| `institute_lms.billing_transport.verify_payment` | ['POST'] | False | `tenant, invoice, snapshot, reference, amount_lkr, reason` | [billing_transport.py:45](../institute_lms/billing_transport.py#L45) |
| `institute_lms.billing_transport.receive` | ['POST'] | True | `payload, signature` | [billing_transport.py:49](../institute_lms/billing_transport.py#L49) |
| `institute_lms.calendar_sync.connect` | ['POST'] | False | `` | [calendar_sync.py:32](../institute_lms/calendar_sync.py#L32) |
| `institute_lms.calendar_sync.callback` | ['GET'] | False | `state=None, code=None, error=None` | [calendar_sync.py:44](../institute_lms/calendar_sync.py#L44) |
| `institute_lms.calendar_sync.disconnect` | ['POST'] | False | `` | [calendar_sync.py:97](../institute_lms/calendar_sync.py#L97) |
| `institute_lms.campus_context.choices` | ['GET'] | False | `` | [campus_context.py:46](../institute_lms/campus_context.py#L46) |
| `institute_lms.campus_context.clear` | ['POST'] | False | `` | [campus_context.py:62](../institute_lms/campus_context.py#L62) |
| `institute_lms.campus_context.select` | ['POST'] | False | `institute` | [campus_context.py:70](../institute_lms/campus_context.py#L70) |
| `institute_lms.campus_join.directory` | ['GET'] | False | `query='', page=0` | [campus_join.py:8](../institute_lms/campus_join.py#L8) |
| `institute_lms.campus_join.details` | ['GET'] | False | `` | [campus_join.py:34](../institute_lms/campus_join.py#L34) |
| `institute_lms.campus_join.register_student` | ['POST'] | False | `profile, language='en'` | [campus_join.py:48](../institute_lms/campus_join.py#L48) |
| `institute_lms.campus_join.register_teacher` | ['POST'] | False | `profile` | [campus_join.py:97](../institute_lms/campus_join.py#L97) |
| `institute_lms.campus_join.people` | ['GET'] | False | `query=''` | [campus_join.py:124](../institute_lms/campus_join.py#L124) |
| `institute_lms.catalog.detail` | Framework default | False | `profile, page=0` | [catalog.py:24](../institute_lms/catalog.py#L24) |
| `institute_lms.catalog.publishing_options` | Framework default | False | `` | [catalog.py:45](../institute_lms/catalog.py#L45) |
| `institute_lms.catalog.join_class` | ['POST'] | False | `classroom` | [catalog.py:71](../institute_lms/catalog.py#L71) |
| `institute_lms.classroom_quizzes.metadata` | Framework default | False | `classroom` | [classroom_quizzes.py:50](../institute_lms/classroom_quizzes.py#L50) |
| `institute_lms.classroom_quizzes.listing` | Framework default | False | `classroom, page=0` | [classroom_quizzes.py:69](../institute_lms/classroom_quizzes.py#L69) |
| `institute_lms.classroom_quizzes.detail` | Framework default | False | `name` | [classroom_quizzes.py:84](../institute_lms/classroom_quizzes.py#L84) |
| `institute_lms.classroom_quizzes.save` | ['POST'] | False | `data, publish=False` | [classroom_quizzes.py:98](../institute_lms/classroom_quizzes.py#L98) |
| `institute_lms.classroom_quizzes.submit` | ['POST'] | False | `name, answers` | [classroom_quizzes.py:131](../institute_lms/classroom_quizzes.py#L131) |
| `institute_lms.classroom_quizzes.submissions` | Framework default | False | `name, page=0` | [classroom_quizzes.py:157](../institute_lms/classroom_quizzes.py#L157) |
| `institute_lms.commerce_events.receive` | ['POST'] | True | `payload, signature` | [commerce_events.py:46](../institute_lms/commerce_events.py#L46) |
| `institute_lms.commerce_events.listing` | Framework default | False | `tenant=None, page=0` | [commerce_events.py:68](../institute_lms/commerce_events.py#L68) |
| `institute_lms.commercial.pricing_context` | Framework default | False | `classroom=None` | [commercial.py:94](../institute_lms/commercial.py#L94) |
| `institute_lms.commercial.upload_proof` | ['POST'] | False | `` | [commercial.py:143](../institute_lms/commercial.py#L143) |
| `institute_lms.commercial.submit_slip` | ['POST'] | False | `invoice, proof, reference, amount, transfer_date` | [commercial.py:157](../institute_lms/commercial.py#L157) |
| `institute_lms.commercial.review_slip` | ['POST'] | False | `name, decision, note='', access_kind=None, starts_at=None, ends_at=None, rejection_reason=''` | [commercial.py:188](../institute_lms/commercial.py#L188) |
| `institute_lms.commercial.slips` | Framework default | False | `page=0` | [commercial.py:216](../institute_lms/commercial.py#L216) |
| `institute_lms.commercial.proof` | Framework default | False | `name` | [commercial.py:235](../institute_lms/commercial.py#L235) |
| `institute_lms.commercial.catalog` | Framework default | False | `` | [commercial.py:245](../institute_lms/commercial.py#L245) |
| `institute_lms.commercial.configure` | ['POST'] | False | `owner_type, plan, billing_email, owner_user=None, bank_instructions='', reason=''` | [commercial.py:249](../institute_lms/commercial.py#L249) |
| `institute_lms.commercial.summary` | Framework default | False | `` | [commercial.py:263](../institute_lms/commercial.py#L263) |
| `institute_lms.commercial.submit_invoice_payment` | ['POST'] | False | `name, reference, proof_file` | [commercial.py:273](../institute_lms/commercial.py#L273) |
| `institute_lms.commercial.owner_invoices` | Framework default | False | `` | [commercial.py:277](../institute_lms/commercial.py#L277) |
| `institute_lms.commercial.approve_invoice` | ['POST'] | False | `name, reference, received_amount, note` | [commercial.py:284](../institute_lms/commercial.py#L284) |
| `institute_lms.commercial.invoice_detail` | Framework default | False | `name` | [commercial.py:304](../institute_lms/commercial.py#L304) |
| `institute_lms.commercial.provider_proof_data` | Framework default | False | `name` | [commercial.py:317](../institute_lms/commercial.py#L317) |
| `institute_lms.commercial.provider_proof` | Framework default | False | `name` | [commercial.py:329](../institute_lms/commercial.py#L329) |
| `institute_lms.commercial.metrics` | Framework default | False | `start_date=None, end_date=None` | [commercial.py:338](../institute_lms/commercial.py#L338) |
| `institute_lms.commercial.hnb_checkout` | ['POST'] | False | `invoice` | [commercial.py:354](../institute_lms/commercial.py#L354) |
| `institute_lms.commercial.save_billing_preferences` | ['POST'] | False | `account, payment_method, billing_email, auto_pay=False, consent=False` | [commercial.py:367](../institute_lms/commercial.py#L367) |
| `institute_lms.commercial.card_setup` | ['POST'] | False | `account` | [commercial.py:371](../institute_lms/commercial.py#L371) |
| `institute_lms.commercial.remove_card` | ['POST'] | False | `account` | [commercial.py:375](../institute_lms/commercial.py#L375) |
| `institute_lms.commercial.card_checkout` | ['POST'] | False | `name` | [commercial.py:380](../institute_lms/commercial.py#L380) |
| `institute_lms.contact.status` | ['POST'] | False | `` | [contact.py:30](../institute_lms/contact.py#L30) |
| `institute_lms.contact.request_verification` | ['POST'] | False | `email` | [contact.py:38](../institute_lms/contact.py#L38) |
| `institute_lms.contact.verify` | ['POST'] | False | `code` | [contact.py:58](../institute_lms/contact.py#L58) |
| `institute_lms.contact.preferences` | ['POST'] | False | `email_opt_in` | [contact.py:78](../institute_lms/contact.py#L78) |
| `institute_lms.cybersource.availability` | ['POST'] | False | `kind, invoice` | [cybersource.py:110](../institute_lms/cybersource.py#L110) |
| `institute_lms.cybersource.start` | ['POST'] | False | `kind, invoice` | [cybersource.py:118](../institute_lms/cybersource.py#L118) |
| `institute_lms.cybersource.browser_event` | ['POST'] | False | `attempt, event` | [cybersource.py:159](../institute_lms/cybersource.py#L159) |
| `institute_lms.cybersource.status` | ['POST'] | False | `attempt` | [cybersource.py:169](../institute_lms/cybersource.py#L169) |
| `institute_lms.cybersource.reconcile` | ['POST'] | False | `attempt` | [cybersource.py:174](../institute_lms/cybersource.py#L174) |
| `institute_lms.cybersource.review_queue` | ['POST'] | False | `` | [cybersource.py:261](../institute_lms/cybersource.py#L261) |
| `institute_lms.cybersource.close_unpaid` | ['POST'] | False | `attempt, reason` | [cybersource.py:270](../institute_lms/cybersource.py#L270) |
| `institute_lms.delivery.state` | Framework default | False | `classroom, page=0` | [delivery.py:36](../institute_lms/delivery.py#L36) |
| `institute_lms.delivery.configure` | ['POST'] | False | `classroom, data` | [delivery.py:50](../institute_lms/delivery.py#L50) |
| `institute_lms.delivery.submit_order` | ['POST'] | False | `classroom, data, proof` | [delivery.py:63](../institute_lms/delivery.py#L63) |
| `institute_lms.delivery.review_order` | ['POST'] | False | `name, decision, note` | [delivery.py:102](../institute_lms/delivery.py#L102) |
| `institute_lms.delivery.dispatch` | ['POST'] | False | `name, courier, tracking_reference` | [delivery.py:113](../institute_lms/delivery.py#L113) |
| `institute_lms.delivery.proof` | Framework default | False | `name` | [delivery.py:123](../institute_lms/delivery.py#L123) |
| `institute_lms.devices.register` | ['POST'] | False | `device_id, token, platform` | [devices.py:8](../institute_lms/devices.py#L8) |
| `institute_lms.devices.revoke` | ['POST'] | False | `device` | [devices.py:25](../institute_lms/devices.py#L25) |
| `institute_lms.devices.firebase_config` | ['GET'] | False | `` | [devices.py:32](../institute_lms/devices.py#L32) |
| `institute_lms.devices.firebase_test` | ['POST'] | False | `device, request_id, dry_run=True` | [devices.py:38](../institute_lms/devices.py#L38) |
| `institute_lms.full_api.capabilities` | Framework default | False | `` | [full_api.py:5](../institute_lms/full_api.py#L5) |
| `institute_lms.health.live` | ['GET'] | True | `` | [health.py:7](../institute_lms/health.py#L7) |
| `institute_lms.health.readiness` | Framework default | False | `` | [health.py:16](../institute_lms/health.py#L16) |
| `institute_lms.invitations.invite_teacher` | ['POST'] | False | `email` | [invitations.py:18](../institute_lms/invitations.py#L18) |
| `institute_lms.invitations.list_invitations` | ['POST'] | False | `` | [invitations.py:34](../institute_lms/invitations.py#L34) |
| `institute_lms.invitations.respond` | ['POST'] | False | `name, decision` | [invitations.py:45](../institute_lms/invitations.py#L45) |
| `institute_lms.invitations.request_by_email` | ['POST'] | False | `email` | [invitations.py:60](../institute_lms/invitations.py#L60) |
| `institute_lms.knowledge.ingest` | ['POST'] | False | `classroom, source_type, source_name` | [knowledge.py:45](../institute_lms/knowledge.py#L45) |
| `institute_lms.knowledge.deactivate` | ['POST'] | False | `document` | [knowledge.py:165](../institute_lms/knowledge.py#L165) |
| `institute_lms.knowledge.documents` | Framework default | False | `classroom` | [knowledge.py:171](../institute_lms/knowledge.py#L171) |
| `institute_lms.knowledge.reset_index` | ['POST'] | False | `classroom, reason` | [knowledge.py:176](../institute_lms/knowledge.py#L176) |
| `institute_lms.learning_preferences.get_preferences` | Framework default | False | `` | [learning_preferences.py:12](../institute_lms/learning_preferences.py#L12) |
| `institute_lms.learning_preferences.save_preferences` | ['POST'] | False | `data` | [learning_preferences.py:18](../institute_lms/learning_preferences.py#L18) |
| `institute_lms.learning_spaces.directory` | Framework default | False | `query='', page=0` | [learning_spaces.py:10](../institute_lms/learning_spaces.py#L10) |
| `institute_lms.learning_spaces.choices` | Framework default | False | `` | [learning_spaces.py:24](../institute_lms/learning_spaces.py#L24) |
| `institute_lms.learning_spaces.classes` | Framework default | False | `profile='', page=0` | [learning_spaces.py:45](../institute_lms/learning_spaces.py#L45) |
| `institute_lms.lecture_refunds.request` | ['POST'] | False | `order, reason` | [lecture_refunds.py:26](../institute_lms/lecture_refunds.py#L26) |
| `institute_lms.lecture_refunds.listing` | Framework default | False | `` | [lecture_refunds.py:75](../institute_lms/lecture_refunds.py#L75) |
| `institute_lms.lectures.listing` | Framework default | False | `library=False, purchases=False, classroom=None` | [lectures.py:30](../institute_lms/lectures.py#L30) |
| `institute_lms.lectures.save` | ['POST'] | False | `data` | [lectures.py:58](../institute_lms/lectures.py#L58) |
| `institute_lms.lectures.checkout` | ['POST'] | False | `product, mobile=False` | [lectures.py:94](../institute_lms/lectures.py#L94) |
| `institute_lms.lectures.notify` | ['POST'] | True | `**kwargs` | [lectures.py:134](../institute_lms/lectures.py#L134) |
| `institute_lms.lectures.history` | Framework default | False | `classroom=None` | [lectures.py:185](../institute_lms/lectures.py#L185) |
| `institute_lms.lectures.detail` | Framework default | False | `name` | [lectures.py:198](../institute_lms/lectures.py#L198) |
| `institute_lms.lectures.receipt` | Framework default | False | `name` | [lectures.py:203](../institute_lms/lectures.py#L203) |
| `institute_lms.lectures.playback` | ['POST'] | False | `product` | [lectures.py:212](../institute_lms/lectures.py#L212) |
| `institute_lms.live_classes.listing` | Framework default | False | `classroom=None` | [live_classes.py:18](../institute_lms/live_classes.py#L18) |
| `institute_lms.live_classes.schedule` | ['POST'] | False | `session` | [live_classes.py:35](../institute_lms/live_classes.py#L35) |
| `institute_lms.live_classes.control` | ['POST'] | False | `name, action` | [live_classes.py:48](../institute_lms/live_classes.py#L48) |
| `institute_lms.live_classes.join` | ['POST'] | False | `name` | [live_classes.py:79](../institute_lms/live_classes.py#L79) |
| `institute_lms.live_classes.recording` | ['POST'] | False | `name` | [live_classes.py:88](../institute_lms/live_classes.py#L88) |
| `institute_lms.live_classes.lecture_draft` | ['POST'] | False | `name` | [live_classes.py:107](../institute_lms/live_classes.py#L107) |
| `institute_lms.live_classes.webhook` | ['POST'] | True | `**kwargs` | [live_classes.py:117](../institute_lms/live_classes.py#L117) |
| `institute_lms.live_classes.publish_recording` | ['POST'] | False | `name, reviewed=False` | [live_classes.py:144](../institute_lms/live_classes.py#L144) |
| `institute_lms.live_classes.reconcile` | ['POST'] | False | `name` | [live_classes.py:153](../institute_lms/live_classes.py#L153) |
| `institute_lms.live_classes.cleanup_failed` | ['POST'] | False | `name, reason` | [live_classes.py:174](../institute_lms/live_classes.py#L174) |
| `institute_lms.live_classes.room_status` | Framework default | False | `name` | [live_classes.py:201](../institute_lms/live_classes.py#L201) |
| `institute_lms.materials.upload` | ['POST'] | False | `classroom, purpose='original'` | [materials.py:12](../institute_lms/materials.py#L12) |
| `institute_lms.materials.upload_paper` | ['POST'] | False | `classroom, title, request_id, description=''` | [materials.py:34](../institute_lms/materials.py#L34) |
| `institute_lms.materials.paper_listing` | Framework default | False | `classroom, page=0` | [materials.py:59](../institute_lms/materials.py#L59) |
| `institute_lms.materials.content` | ['GET'] | False | `material, action='view'` | [materials.py:114](../institute_lms/materials.py#L114) |
| `institute_lms.materials.update_availability` | ['POST'] | False | `material, availability_days=None` | [materials.py:149](../institute_lms/materials.py#L149) |
| `institute_lms.media_reconciliation.listing` | Framework default | False | `` | [media_reconciliation.py:13](../institute_lms/media_reconciliation.py#L13) |
| `institute_lms.media_reconciliation.cleanup` | ['POST'] | False | `name, reason` | [media_reconciliation.py:20](../institute_lms/media_reconciliation.py#L20) |
| `institute_lms.mobile_api.current` | Framework default | False | `` | [mobile_api.py:5](../institute_lms/mobile_api.py#L5) |
| `institute_lms.mobile_api.classes` | Framework default | False | `page=0` | [mobile_api.py:11](../institute_lms/mobile_api.py#L11) |
| `institute_lms.mobile_api.enrollments` | Framework default | False | `page=0` | [mobile_api.py:16](../institute_lms/mobile_api.py#L16) |
| `institute_lms.mobile_api.lesson` | Framework default | False | `course, chapter, lesson` | [mobile_api.py:23](../institute_lms/mobile_api.py#L23) |
| `institute_lms.mobile_auth.app_authorize` | ['GET'] | True | `code_challenge, state, redirect_uri, code_challenge_method=None, response_type=None, client_id=None, scope=None, nonce=None` | [mobile_auth.py:27](../institute_lms/mobile_auth.py#L27) |
| `institute_lms.mobile_auth.authorize` | ['GET'] | True | `challenge, state, redirect_uri` | [mobile_auth.py:34](../institute_lms/mobile_auth.py#L34) |
| `institute_lms.mobile_auth.approve` | ['POST'] | False | `challenge, state, redirect_uri` | [mobile_auth.py:49](../institute_lms/mobile_auth.py#L49) |
| `institute_lms.mobile_auth.exchange` | ['POST'] | True | `code, verifier, redirect_uri, device_id` | [mobile_auth.py:61](../institute_lms/mobile_auth.py#L61) |
| `institute_lms.mobile_auth.logout` | ['POST'] | False | `session=None` | [mobile_auth.py:97](../institute_lms/mobile_auth.py#L97) |
| `institute_lms.mobile_verification.request_code` | ['POST'] | False | `phone` | [mobile_verification.py:10](../institute_lms/mobile_verification.py#L10) |
| `institute_lms.mobile_verification.verify` | ['POST'] | False | `code, channel='SMS', challenge=None` | [mobile_verification.py:16](../institute_lms/mobile_verification.py#L16) |
| `institute_lms.mobile_verification.claim_trial` | ['POST'] | False | `` | [mobile_verification.py:21](../institute_lms/mobile_verification.py#L21) |
| `institute_lms.notification_service.save_preferences` | ['POST'] | False | `settings` | [notification_service.py:49](../institute_lms/notification_service.py#L49) |
| `institute_lms.notification_service.inbox` | Framework default | False | `page=0, unread=False, profile=''` | [notification_service.py:66](../institute_lms/notification_service.py#L66) |
| `institute_lms.notification_service.mark_read` | ['POST'] | False | `name` | [notification_service.py:83](../institute_lms/notification_service.py#L83) |
| `institute_lms.notification_service.whatsapp_webhook` | ['GET', 'POST'] | True | `**kwargs` | [notification_service.py:128](../institute_lms/notification_service.py#L128) |
| `institute_lms.operations.mark_attendance` | ['POST'] | False | `session, student, status, note=''` | [operations.py:27](../institute_lms/operations.py#L27) |
| `institute_lms.operations.join_session` | ['POST'] | False | `session` | [operations.py:35](../institute_lms/operations.py#L35) |
| `institute_lms.operations.attendance` | Framework default | False | `classroom, session=None, page=0` | [operations.py:54](../institute_lms/operations.py#L54) |
| `institute_lms.operations.attendance_csv` | ['GET'] | False | `classroom, session=None, page=0` | [operations.py:57](../institute_lms/operations.py#L57) |
| `institute_lms.operations.create_ticket` | ['POST'] | False | `subject, category, body` | [operations.py:66](../institute_lms/operations.py#L66) |
| `institute_lms.operations.tickets` | Framework default | False | `page=0` | [operations.py:82](../institute_lms/operations.py#L82) |
| `institute_lms.operations.thread` | Framework default | False | `ticket, page=0` | [operations.py:89](../institute_lms/operations.py#L89) |
| `institute_lms.operations.reply` | ['POST'] | False | `ticket, body, status=None` | [operations.py:95](../institute_lms/operations.py#L95) |
| `institute_lms.owner_access.access_list` | ['GET'] | False | `` | [owner_access.py:26](../institute_lms/owner_access.py#L26) |
| `institute_lms.owner_access.add` | ['POST'] | False | `email, reason` | [owner_access.py:34](../institute_lms/owner_access.py#L34) |
| `institute_lms.owner_access.remove` | ['POST'] | False | `email, reason` | [owner_access.py:74](../institute_lms/owner_access.py#L74) |
| `institute_lms.owner_pricing.assign` | ['POST'] | False | `data` | [owner_pricing.py:30](../institute_lms/owner_pricing.py#L30) |
| `institute_lms.owner_pricing.assignments` | Framework default | False | `page=0` | [owner_pricing.py:59](../institute_lms/owner_pricing.py#L59) |
| `institute_lms.owner_pricing.quote` | ['POST'] | False | `product` | [owner_pricing.py:64](../institute_lms/owner_pricing.py#L64) |
| `institute_lms.owner_pricing.classroom_price` | ['POST'] | False | `classroom, amount_minor, reason` | [owner_pricing.py:80](../institute_lms/owner_pricing.py#L80) |
| `institute_lms.owner_pricing.entitlements` | Framework default | False | `` | [owner_pricing.py:102](../institute_lms/owner_pricing.py#L102) |
| `institute_lms.owner_pricing.grant` | ['POST'] | False | `customer, product, expires_at, reason` | [owner_pricing.py:107](../institute_lms/owner_pricing.py#L107) |
| `institute_lms.owner_pricing.revoke` | ['POST'] | False | `name, reason` | [owner_pricing.py:119](../institute_lms/owner_pricing.py#L119) |
| `institute_lms.paper_generator.create` | ['POST'] | False | `classroom, document, topic, count=10, duration_minutes=120, request_id=None, blueprint=None, template_metadata=None` | [paper_generator.py:16](../institute_lms/paper_generator.py#L16) |
| `institute_lms.paper_generator.status` | Framework default | False | `name` | [paper_generator.py:104](../institute_lms/paper_generator.py#L104) |
| `institute_lms.paper_generator.export` | Framework default | False | `paper` | [paper_generator.py:109](../institute_lms/paper_generator.py#L109) |
| `institute_lms.paper_generator.resume` | ['POST'] | False | `name` | [paper_generator.py:117](../institute_lms/paper_generator.py#L117) |
| `institute_lms.paper_generator.listing` | Framework default | False | `` | [paper_generator.py:129](../institute_lms/paper_generator.py#L129) |
| `institute_lms.paper_generator.printable` | Framework default | False | `paper, answer_key=False` | [paper_generator.py:136](../institute_lms/paper_generator.py#L136) |
| `institute_lms.papers.listing` | Framework default | False | `classroom=None, page=0` | [papers.py:23](../institute_lms/papers.py#L23) |
| `institute_lms.papers.draft` | ['POST'] | False | `data` | [papers.py:34](../institute_lms/papers.py#L34) |
| `institute_lms.papers.detail` | Framework default | False | `name` | [papers.py:63](../institute_lms/papers.py#L63) |
| `institute_lms.papers.publish` | ['POST'] | False | `name, reviewed=False` | [papers.py:70](../institute_lms/papers.py#L70) |
| `institute_lms.papers.archive` | ['POST'] | False | `name` | [papers.py:79](../institute_lms/papers.py#L79) |
| `institute_lms.papers.start` | ['POST'] | False | `name` | [papers.py:85](../institute_lms/papers.py#L85) |
| `institute_lms.papers.submit` | ['POST'] | False | `attempt, answers` | [papers.py:103](../institute_lms/papers.py#L103) |
| `institute_lms.papers.submissions` | Framework default | False | `paper, page=0` | [papers.py:116](../institute_lms/papers.py#L116) |
| `institute_lms.papers.mark` | ['POST'] | False | `attempt, score, feedback` | [papers.py:124](../institute_lms/papers.py#L124) |
| `institute_lms.papers.upload_answer` | ['POST'] | False | `attempt` | [papers.py:134](../institute_lms/papers.py#L134) |
| `institute_lms.papers.answer_file` | ['GET'] | False | `attempt` | [papers.py:152](../institute_lms/papers.py#L152) |
| `institute_lms.papers.generate` | ['POST'] | False | `classroom, topic, count=5, document=None, request_id=None` | [papers.py:166](../institute_lms/papers.py#L166) |
| `institute_lms.payment_reports.history` | Framework default | False | `start_date=None, end_date=None, status='All', page=0` | [payment_reports.py:8](../institute_lms/payment_reports.py#L8) |
| `institute_lms.payments.checkout` | ['POST'] | False | `invoice: str, customer: dict | str` | [payments.py:8](../institute_lms/payments.py#L8) |
| `institute_lms.payments.notify` | ['POST'] | True | `**kwargs` | [payments.py:50](../institute_lms/payments.py#L50) |
| `institute_lms.payments_lk.notify` | ['POST'] | True | `**kwargs` | [payments_lk.py:104](../institute_lms/payments_lk.py#L104) |
| `institute_lms.plan_catalog.admin_get` | ['POST'] | False | `` | [plan_catalog.py:17](../institute_lms/plan_catalog.py#L17) |
| `institute_lms.plan_catalog.publish` | ['POST'] | False | `plans, revision, reason` | [plan_catalog.py:22](../institute_lms/plan_catalog.py#L22) |
| `institute_lms.platform.register` | ['POST'] | False | `title, code, site_hostname, admin_contact, plan='STARTER'` | [platform.py:28](../institute_lms/platform.py#L28) |
| `institute_lms.platform.organizations` | Framework default | False | `page=0` | [platform.py:60](../institute_lms/platform.py#L60) |
| `institute_lms.platform.configure_plan` | ['POST'] | False | `plan, features, limits, price_minor, period_days=30, reason=''` | [platform.py:70](../institute_lms/platform.py#L70) |
| `institute_lms.platform.update_organization` | ['POST'] | False | `tenant, enabled, reason, custom_domain=None` | [platform.py:83](../institute_lms/platform.py#L83) |
| `institute_lms.platform.override` | ['POST'] | False | `tenant, values, reason` | [platform.py:96](../institute_lms/platform.py#L96) |
| `institute_lms.platform.trial` | ['POST'] | False | `tenant, days, reason` | [platform.py:106](../institute_lms/platform.py#L106) |
| `institute_lms.platform.subscription_state` | ['POST'] | False | `tenant, state, reason, grace_until=None` | [platform.py:120](../institute_lms/platform.py#L120) |
| `institute_lms.platform.manifest` | ['POST'] | False | `tenant` | [platform.py:133](../institute_lms/platform.py#L133) |
| `institute_lms.platform.provisioning_spec` | Framework default | False | `job` | [platform.py:157](../institute_lms/platform.py#L157) |
| `institute_lms.platform.provisioning_result` | ['POST'] | False | `job, status, reason` | [platform.py:164](../institute_lms/platform.py#L164) |
| `institute_lms.platform.invite_billing_contact` | ['POST'] | False | `tenant` | [platform.py:173](../institute_lms/platform.py#L173) |
| `institute_lms.platform.reactivate` | ['POST'] | False | `tenant, reason` | [platform.py:181](../institute_lms/platform.py#L181) |
| `institute_lms.platform.audit_log` | ['GET'] | False | `page=0` | [platform.py:192](../institute_lms/platform.py#L192) |
| `institute_lms.portal_policy.public` | Framework default | True | `` | [portal_policy.py:7](../institute_lms/portal_policy.py#L7) |
| `institute_lms.portal_policy.save` | ['POST'] | False | `privacy_policy_url='', privacy_policy_version='', provider_applications_enabled=0` | [portal_policy.py:16](../institute_lms/portal_policy.py#L16) |
| `institute_lms.portal_policy.google_start` | ['POST'] | True | `signup=0` | [portal_policy.py:29](../institute_lms/portal_policy.py#L29) |
| `institute_lms.portal_session.current` | ['GET'] | True | `` | [portal_session.py:6](../institute_lms/portal_session.py#L6) |
| `institute_lms.portal_session.overview` | Framework default | False | `` | [portal_session.py:43](../institute_lms/portal_session.py#L43) |
| `institute_lms.premium.configure_offer` | ['POST'] | False | `tenant, amount_minor, reason, enabled=True` | [premium.py:18](../institute_lms/premium.py#L18) |
| `institute_lms.premium.summary` | Framework default | False | `tenant` | [premium.py:39](../institute_lms/premium.py#L39) |
| `institute_lms.premium.receipt` | Framework default | False | `name` | [premium.py:55](../institute_lms/premium.py#L55) |
| `institute_lms.premium.request_pricing` | ['POST'] | False | `tenant` | [premium.py:61](../institute_lms/premium.py#L61) |
| `institute_lms.private_contact.get_details` | ['POST'] | False | `` | [private_contact.py:14](../institute_lms/private_contact.py#L14) |
| `institute_lms.private_contact.save_details` | ['POST'] | False | `data` | [private_contact.py:22](../institute_lms/private_contact.py#L22) |
| `institute_lms.private_contact.request_whatsapp_code` | ['POST'] | False | `phone` | [private_contact.py:38](../institute_lms/private_contact.py#L38) |
| `institute_lms.private_media.begin` | ['POST'] | False | `classroom, size, content_type` | [private_media.py:22](../institute_lms/private_media.py#L22) |
| `institute_lms.private_media.complete` | ['POST'] | False | `name` | [private_media.py:52](../institute_lms/private_media.py#L52) |
| `institute_lms.profiles.me` | Framework default | False | `` | [profiles.py:39](../institute_lms/profiles.py#L39) |
| `institute_lms.profiles.save_profile` | ['POST'] | False | `data` | [profiles.py:44](../institute_lms/profiles.py#L44) |
| `institute_lms.profiles.pending` | Framework default | False | `page=0` | [profiles.py:83](../institute_lms/profiles.py#L83) |
| `institute_lms.profiles.review` | ['POST'] | False | `profile, decision, reason, workspace=None` | [profiles.py:88](../institute_lms/profiles.py#L88) |
| `institute_lms.profiles.search` | Framework default | False | `query='', page=0` | [profiles.py:107](../institute_lms/profiles.py#L107) |
| `institute_lms.profiles.upload_image` | ['POST'] | False | `kind` | [profiles.py:118](../institute_lms/profiles.py#L118) |
| `institute_lms.profiles.relate` | ['POST'] | False | `profile, kind` | [profiles.py:146](../institute_lms/profiles.py#L146) |
| `institute_lms.profiles.change_relationship` | ['POST'] | False | `relationship, status, reason=''` | [profiles.py:169](../institute_lms/profiles.py#L169) |
| `institute_lms.profiles.relationships` | Framework default | False | `profile` | [profiles.py:187](../institute_lms/profiles.py#L187) |
| `institute_lms.profiles.publish_update` | ['POST'] | False | `headline, body, url=''` | [profiles.py:196](../institute_lms/profiles.py#L196) |
| `institute_lms.profiles.followed_updates` | Framework default | False | `page=0` | [profiles.py:209](../institute_lms/profiles.py#L209) |
| `institute_lms.profiles.upload_asset` | ['POST'] | False | `` | [profiles.py:232](../institute_lms/profiles.py#L232) |
| `institute_lms.profiles.institute_join_options` | ['GET'] | False | `` | [profiles.py:256](../institute_lms/profiles.py#L256) |
| `institute_lms.profiles.request_institutes` | ['POST'] | False | `profiles, purpose` | [profiles.py:265](../institute_lms/profiles.py#L265) |
| `institute_lms.profiles.followed_free_classes` | ['GET'] | False | `page=0` | [profiles.py:286](../institute_lms/profiles.py#L286) |
| `institute_lms.profiles.follow_status` | ['GET'] | False | `profiles` | [profiles.py:305](../institute_lms/profiles.py#L305) |
| `institute_lms.provider_bridge.request` | ['POST'] | False | `tenant, action, args=None` | [provider_bridge.py:20](../institute_lms/provider_bridge.py#L20) |
| `institute_lms.provider_bridge.receive` | ['POST'] | True | `payload, signature` | [provider_bridge.py:41](../institute_lms/provider_bridge.py#L41) |
| `institute_lms.provider_cards.notify` | ['POST'] | True | `**kwargs` | [provider_cards.py:130](../institute_lms/provider_cards.py#L130) |
| `institute_lms.registration.self_start` | ['POST'] | True | `data` | [registration.py:12](../institute_lms/registration.py#L12) |
| `institute_lms.registration.self_phone` | ['POST'] | True | `token` | [registration.py:18](../institute_lms/registration.py#L18) |
| `institute_lms.registration.self_verify` | ['POST'] | True | `token, channel, code` | [registration.py:24](../institute_lms/registration.py#L24) |
| `institute_lms.registration.self_complete` | ['POST'] | True | `token, password, confirmation` | [registration.py:30](../institute_lms/registration.py#L30) |
| `institute_lms.registration.request_code` | ['POST'] | True | `data` | [registration.py:58](../institute_lms/registration.py#L58) |
| `institute_lms.registration.verify_code` | ['POST'] | True | `challenge, code` | [registration.py:87](../institute_lms/registration.py#L87) |
| `institute_lms.registration.applications` | Framework default | False | `page=0` | [registration.py:118](../institute_lms/registration.py#L118) |
| `institute_lms.registration.review_application` | ['POST'] | False | `name, decision, reason` | [registration.py:123](../institute_lms/registration.py#L123) |
| `institute_lms.registration.self_google_details` | ['GET'] | False | `` | [registration.py:139](../institute_lms/registration.py#L139) |
| `institute_lms.registration.account_status` | ['GET'] | False | `` | [registration.py:154](../institute_lms/registration.py#L154) |
| `institute_lms.registration.account_notifications` | ['GET'] | False | `` | [registration.py:166](../institute_lms/registration.py#L166) |
| `institute_lms.release.workspace` | Framework default | False | `` | [release.py:17](../institute_lms/release.py#L17) |
| `institute_lms.release.billing` | Framework default | False | `` | [release.py:37](../institute_lms/release.py#L37) |
| `institute_lms.release.control_room` | Framework default | False | `page=0` | [release.py:55](../institute_lms/release.py#L55) |
| `institute_lms.release.custom_price` | ['POST'] | False | `tenant, amount_minor, period, reason` | [release.py:67](../institute_lms/release.py#L67) |
| `institute_lms.release.channels` | Framework default | False | `` | [release.py:87](../institute_lms/release.py#L87) |
| `institute_lms.release.otp_status` | Framework default | False | `` | [release.py:108](../institute_lms/release.py#L108) |
| `institute_lms.release.unread` | Framework default | False | `profile=''` | [release.py:118](../institute_lms/release.py#L118) |
| `institute_lms.release.learning_sources` | Framework default | False | `classroom` | [release.py:131](../institute_lms/release.py#L131) |
| `institute_lms.retention.configure_course` | ['POST'] | False | `classroom, expires_at, grace_days=0, archive_days=30, delete_days=180` | [retention.py:31](../institute_lms/retention.py#L31) |
| `institute_lms.retention.purge_orphan` | ['POST'] | False | `object_name, reason` | [retention.py:78](../institute_lms/retention.py#L78) |
| `institute_lms.saas.status` | Framework default | False | `` | [saas.py:53](../institute_lms/saas.py#L53) |
| `institute_lms.saas.apply_manifest` | ['POST'] | True | `payload, signature` | [saas.py:59](../institute_lms/saas.py#L59) |
| `institute_lms.soul.status` | ['POST'] | False | `` | [soul.py:25](../institute_lms/soul.py#L25) |
| `institute_lms.soul.configure` | ['POST'] | False | `api_key=None, model='gpt-4.1-mini', enabled=False, remove_key=False` | [soul.py:36](../institute_lms/soul.py#L36) |
| `institute_lms.soul.chat` | ['POST'] | False | `message, page='dashboard', language='en', history=None, consent=False, request_id=None` | [soul.py:89](../institute_lms/soul.py#L89) |
| `institute_lms.soul.test_connection` | ['POST'] | False | `` | [soul.py:128](../institute_lms/soul.py#L128) |
| `institute_lms.student_billing.status` | ['POST'] | False | `` | [student_billing.py:4](../institute_lms/student_billing.py#L4) |
| `institute_lms.subscription_payments.quote` | ['POST'] | False | `tenant, plan` | [subscription_payments.py:30](../institute_lms/subscription_payments.py#L30) |
| `institute_lms.subscription_payments.checkout` | ['POST'] | False | `quote, mobile=False` | [subscription_payments.py:53](../institute_lms/subscription_payments.py#L53) |
| `institute_lms.subscription_payments.notify` | ['POST'] | True | `**kwargs` | [subscription_payments.py:112](../institute_lms/subscription_payments.py#L112) |
| `institute_lms.subscription_payments.status` | Framework default | False | `attempt` | [subscription_payments.py:146](../institute_lms/subscription_payments.py#L146) |
| `institute_lms.teaching.overview` | Framework default | False | `` | [teaching.py:37](../institute_lms/teaching.py#L37) |
| `institute_lms.teaching.membership` | ['POST'] | False | `name, status` | [teaching.py:62](../institute_lms/teaching.py#L62) |
| `institute_lms.teaching.leave_class` | ['POST'] | False | `classroom` | [teaching.py:92](../institute_lms/teaching.py#L92) |
| `institute_lms.teaching.programmes` | Framework default | False | `` | [teaching.py:101](../institute_lms/teaching.py#L101) |
| `institute_lms.teaching.programme_classrooms` | Framework default | False | `` | [teaching.py:116](../institute_lms/teaching.py#L116) |
| `institute_lms.teaching.save_programme` | ['POST'] | False | `data` | [teaching.py:124](../institute_lms/teaching.py#L124) |
| `institute_lms.teaching.enroll_programme` | ['POST'] | False | `programme` | [teaching.py:161](../institute_lms/teaching.py#L161) |
| `institute_lms.teaching.month_invoice` | ['POST'] | False | `classroom, month` | [teaching.py:187](../institute_lms/teaching.py#L187) |
| `institute_lms.usage.summary` | Framework default | False | `` | [usage.py:37](../institute_lms/usage.py#L37) |
| `institute_lms.usage_billing.status` | ['POST'] | False | `` | [usage_billing.py:76](../institute_lms/usage_billing.py#L76) |
| `institute_lms.usage_billing.document` | ['POST'] | False | `invoice` | [usage_billing.py:83](../institute_lms/usage_billing.py#L83) |
| `institute_lms.usage_billing.request_activation` | ['POST'] | False | `invoice` | [usage_billing.py:86](../institute_lms/usage_billing.py#L86) |
| `institute_lms.usage_billing.admin_invoices` | ['POST'] | False | `` | [usage_billing.py:93](../institute_lms/usage_billing.py#L93) |
| `institute_lms.usage_billing.verify_and_reactivate` | ['POST'] | False | `invoice, reference, amount_lkr, reason` | [usage_billing.py:100](../institute_lms/usage_billing.py#L100) |
| `institute_lms.wallet.provision_wallet` | ['POST'] | False | `user, beneficiary, country, currency, institute=None` | [wallet.py:109](../institute_lms/wallet.py#L109) |
| `institute_lms.wallet.dashboard` | Framework default | False | `wallet=None, page=0` | [wallet.py:135](../institute_lms/wallet.py#L135) |
| `institute_lms.wallet.submit_method` | ['POST'] | False | `wallet, data` | [wallet.py:150](../institute_lms/wallet.py#L150) |
| `institute_lms.wallet.review_method` | ['POST'] | False | `method, decision, reason` | [wallet.py:164](../institute_lms/wallet.py#L164) |
| `institute_lms.wallet.request_payout` | ['POST'] | False | `wallet, method, amount, request_key` | [wallet.py:178](../institute_lms/wallet.py#L178) |
| `institute_lms.wallet.update_payout` | ['POST'] | False | `request, status, reference='', reason='', receipt=None` | [wallet.py:198](../institute_lms/wallet.py#L198) |
| `institute_lms.wallet.admin_queue` | Framework default | False | `region='Local', page=0` | [wallet.py:221](../institute_lms/wallet.py#L221) |
| `institute_lms.wallet.reveal_method` | ['POST'] | False | `method` | [wallet.py:228](../institute_lms/wallet.py#L228) |
| `institute_lms.wallet.export_local` | ['POST'] | False | `requests` | [wallet.py:234](../institute_lms/wallet.py#L234) |
| `institute_lms.whatsapp_templates.options` | Framework default | False | `classroom, search=''` | [whatsapp_templates.py:26](../institute_lms/whatsapp_templates.py#L26) |
| `institute_lms.whatsapp_templates.preview` | Framework default | False | `classroom, student, kind, session=None, slip=None` | [whatsapp_templates.py:61](../institute_lms/whatsapp_templates.py#L61) |
| `institute_lms.whatsapp_templates.send` | ['POST'] | False | `classroom, student, kind, request_id, session=None, slip=None` | [whatsapp_templates.py:66](../institute_lms/whatsapp_templates.py#L66) |
| `institute_lms.workspace.overview` | ['GET'] | False | `` | [workspace.py:51](../institute_lms/workspace.py#L51) |
| `institute_lms.workspace.save_settings` | ['POST'] | False | `data` | [workspace.py:57](../institute_lms/workspace.py#L57) |
| `institute_lms.workspace.expenses` | ['GET'] | False | `start=None, end=None` | [workspace.py:64](../institute_lms/workspace.py#L64) |
| `institute_lms.workspace.add_expense` | ['POST'] | False | `data` | [workspace.py:76](../institute_lms/workspace.py#L76) |
| `institute_lms.workspace.void_expense` | ['POST'] | False | `name, reason` | [workspace.py:85](../institute_lms/workspace.py#L85) |
| `institute_lms.workspace.add_operator` | ['POST'] | False | `user` | [workspace.py:94](../institute_lms/workspace.py#L94) |
| `institute_lms.workspace.revoke_operator` | ['POST'] | False | `name` | [workspace.py:108](../institute_lms/workspace.py#L108) |
| `institute_lms.workspace.reviews` | ['GET'] | False | `classroom` | [workspace.py:118](../institute_lms/workspace.py#L118) |
| `institute_lms.workspace.save_review` | ['POST'] | False | `classroom, data` | [workspace.py:126](../institute_lms/workspace.py#L126) |
| `institute_lms.workspace.moderate_review` | ['POST'] | False | `name, action, body=''` | [workspace.py:141](../institute_lms/workspace.py#L141) |
| `institute_lms.workspace.analyse_slip` | ['POST'] | False | `name` | [workspace.py:182](../institute_lms/workspace.py#L182) |
| `institute_lms.workspace.vimeo_playback` | ['POST'] | False | `material` | [workspace.py:208](../institute_lms/workspace.py#L208) |
| `institute_lms.workspace.create_zoom_session` | ['POST'] | False | `session` | [workspace.py:219](../institute_lms/workspace.py#L219) |
| `institute_lms.youtube.connect` | ['POST'] | False | `` | [youtube.py:21](../institute_lms/youtube.py#L21) |
| `institute_lms.youtube.callback` | ['GET'] | False | `state: str, code: str | None=None, error: str | None=None` | [youtube.py:33](../institute_lms/youtube.py#L33) |
| `institute_lms.youtube.schedule_broadcast` | ['POST'] | False | `session: str, privacy: str='unlisted', made_for_kids: bool | None=None` | [youtube.py:76](../institute_lms/youtube.py#L76) |
| `institute_lms.youtube.sync_broadcast` | ['POST'] | False | `session: str` | [youtube.py:107](../institute_lms/youtube.py#L107) |
| `institute_lms.youtube.transition_broadcast` | ['POST'] | False | `session: str, status: str` | [youtube.py:132](../institute_lms/youtube.py#L132) |
| `institute_lms.youtube.live_chat` | ['POST'] | False | `session: str` | [youtube.py:152](../institute_lms/youtube.py#L152) |
