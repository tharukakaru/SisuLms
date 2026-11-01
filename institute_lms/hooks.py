app_name = "institute_lms"
app_title = "Sisu Â· Institute LMS"
app_publisher = "Institute LMS contributors"
app_description = "Institute classrooms, schedules, payments and communication"
app_email = "admin@example.com"
app_license = "AGPL-3.0"
required_apps = ["lms"]
role_home_page = {"Institute Student": "campus", "Institute Teacher": "campus", "Institute Admin": "campus"}
after_install = "institute_lms.setup.after_install"
after_migrate = "institute_lms.setup.add_indexes"
website_route_rules = [{"from_route": "/campus", "to_route": "campus"}, {"from_route": "/super-admin", "to_route": "super_admin"}]
scheduler_events = {"cron": {"*/5 * * * *": ["institute_lms.notifications.dispatch", "institute_lms.notifications.dispatch_email", "institute_lms.calendar_sync.dispatch"]},
                    "daily": ["institute_lms.billing.daily", "institute_lms.retention.purge_expired_promotions", "institute_lms.profiles.purge_updates"]}
doc_events = {"IL Institute": {"validate": "institute_lms.validation.validate_institute"},
              "IL Session": {"on_update":"institute_lms.calendar_sync.session_changed"},
              "IL Enrollment": {"on_update":"institute_lms.calendar_sync.enrollment_changed"}}
add_to_apps_screen = [{"name": "institute_lms", "title": "Sisu", "route": "/campus",
                       "logo": "/assets/institute_lms/brand.svg"}]

on_session_creation = "institute_lms.portal_policy.stamp_session"
on_login = "institute_lms.portal_policy.validate_login"

# Authentication hook order matters: establish mobile identity before authorization.
auth_hooks = ["institute_lms.mobile_auth.authenticate", "institute_lms.account_billing.guard_request", "institute_lms.saas.guard_request", "institute_lms.native_access.guard"]
before_migrate = "institute_lms.patches.run1.before_migrate"
before_write_file = "institute_lms.storage.before_write"
has_permission = {"File": "institute_lms.native_access.file_permission"}
doc_events.update({
    "IL Member": {"validate":"institute_lms.saas.enforce_member"},
    "IL Classroom": {"validate":["institute_lms.saas.enforce_class","institute_lms.native_access.validate_link"]},
    "LMS Course": {"validate":"institute_lms.saas.enforce_course"},
    "Course Lesson": {"validate":"institute_lms.native_access.validate_lesson"},
    "File": {"before_insert":"institute_lms.native_access.validate_file", "validate":"institute_lms.native_access.validate_file", "after_insert":"institute_lms.storage.file_saved", "on_update":"institute_lms.storage.file_saved", "after_delete":"institute_lms.storage.file_deleted"},
    "IL Notification": {"validate":"institute_lms.notification_service.delivery_timestamps"},
})
doc_events['IL Enrollment']['validate']='institute_lms.commercial.enforce_enrollment_limit'
scheduler_events["cron"]["*/5 * * * *"].append("institute_lms.notification_service.dispatch_adapters")
scheduler_events["daily"].append("institute_lms.retention.sweep")
scheduler_events["daily"].append("institute_lms.storage.backfill")
doc_events["IL Paper"]={"on_update":"institute_lms.notification_events.paper_changed"}
doc_events["IL Paper Attempt"]={"on_update":"institute_lms.notification_events.attempt_changed"}
doc_events["LMS Certificate"]={"after_insert":"institute_lms.notification_events.certificate_issued"}
scheduler_events["cron"]["*/5 * * * *"].append("institute_lms.notification_events.due_reminders")

# RUN 2 keeps existing File/calendar/notification hooks and adds invalidation.
def _ai_hook(doctype,event,path):
    events=doc_events.setdefault(doctype,{})
    previous=events.get(event,[])
    events[event]=([previous] if isinstance(previous,str) else previous)+[path]
for _dt in ('IL Material','IL Session','Course Lesson','File'):
    for _event in ('on_update','on_trash'):
        _ai_hook(_dt,_event,'institute_lms.knowledge.source_changed')
scheduler_events['cron']['*/5 * * * *'].append('institute_lms.knowledge.maintain')

scheduler_events['cron'].setdefault('*/5 * * * *', []).append('institute_lms.health.heartbeat')

# Final build: authoritative policy delivery is queued/retried, never a UI activation.
doc_events['IL Organization']={'on_update':'institute_lms.policy_delivery.changed'}
doc_events['IL Subscription']={'on_update':'institute_lms.policy_delivery.changed'}
scheduler_events['cron']['*/5 * * * *'].append('institute_lms.policy_delivery.dispatch')

# V2 transaction-coupled events and minimized tenant financial outbox.
for _dt in ('IL Live Room','IL Paper Generation Job','IL Lecture Order'):
    _ai_hook(_dt,'on_update','institute_lms.product_events.observe')
for _dt in ('IL Lecture Order','IL Invoice'):
    _ai_hook(_dt,'on_update','institute_lms.commerce_events.observe')
scheduler_events['cron']['*/5 * * * *'].append('institute_lms.commerce_events.deliver')

for _dt in ('IL Price Assignment','IL Payment Attempt','IL Premium Receipt'):
    _ai_hook(_dt,'on_update','institute_lms.subscription_notices.changed')
_ai_hook('IL AI Usage','on_update','institute_lms.subscription_notices.low_credit')
scheduler_events['daily'].append('institute_lms.subscription_notices.expiry_reminders')

# Monthly provider billing; access checks evaluate the exact seven-day deadline on every request.
scheduler_events['daily'].append('institute_lms.account_billing.daily')

scheduler_events['daily'].append('institute_lms.wallet.prepare_monthly_settlements')

# Collect SISU provider invoices only after merchant sandbox acceptance.


_ai_hook('IL Member','after_insert','institute_lms.account_billing.member_created')

scheduler_events['daily'].append('institute_lms.usage_billing.daily')

scheduler_events["cron"]["*/5 * * * *"].append("institute_lms.whatsapp_webhook.reconcile")

# Sandbox-only transactional test notices; no production dispatch.
for _dt in ('IL Account Invoice','IL Usage Invoice','IL Profile Relationship'):
    _ai_hook(_dt,'on_update','institute_lms.sandbox_notices.observe')
scheduler_events['daily'].append('institute_lms.sandbox_notices.expiry')
