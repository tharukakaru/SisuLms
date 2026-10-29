"""Public liveness only; sensitive readiness details require the local owner."""
import time
import frappe


@frappe.whitelist(allow_guest=True,methods=['GET'])
def live():
    return {'service':'sisu','reachable':True}


def heartbeat():
    frappe.cache.set_value('il_release_worker_heartbeat',time.time(),expires_in_sec=900)


@frappe.whitelist()
def readiness():
    from .wallet import owner
    owner();checks={}
    try:checks['database']=frappe.db.sql('SELECT 1')[0][0]==1
    except Exception:checks['database']=False
    if not checks['database']:return {'ready':False,'checks':checks,'release':'RUN3'}
    try:
        frappe.cache.set_value('il_readiness_probe',True,expires_in_sec=30)
        checks['cache']=bool(frappe.cache.get_value('il_readiness_probe'))
        stamp=frappe.cache.get_value('il_release_worker_heartbeat')
        checks['scheduled_worker_recent']=bool(stamp and time.time()-float(stamp)<900)
    except Exception:checks['cache']=False;checks['scheduled_worker_recent']=False
    checks['run1_schema']=bool(frappe.db.exists('DocType','IL Subscription'))
    checks['run2_schema']=bool(frappe.db.exists('DocType','IL Knowledge Document'))
    checks['run3_contract_schema']=bool(frappe.db.has_column('IL Price Assignment','tenant_id'))
    checks['site_identity']=bool(frappe.conf.get('il_control_plane') or frappe.conf.get('il_tenant_id'))
    checks['https']=str(frappe.conf.get('host_name','')).startswith('https://')
    if not frappe.conf.get('il_control_plane'):
        checks['tenant_signing_key']=len(str(frappe.conf.get('il_control_plane_key') or ''))>=32
        try:
            from .saas import resolved
            checks['subscription_current']=bool(resolved()['available'])
        except Exception:checks['subscription_current']=False
    configured={k:all(bool(frappe.conf.get(field)) for field in fields) for k,fields in {
        'student_payments':('il_payments_lk_secret_key','il_payments_lk_webhook_secret'),
        'subscription_payments':('il_subscription_payments_lk_secret_key','il_subscription_payments_lk_webhook_secret'),
        'whatsapp':('il_whatsapp_token','il_whatsapp_phone_id'),
        'sms':('il_sms_adapter',),'push':('il_push_adapter',),
        'youtube':('il_youtube_client_id','il_youtube_client_secret'),
        'calendar':('il_calendar_client_id','il_calendar_client_secret')}.items()}
    configured['email']=bool(frappe.db.exists('Email Account',{'enable_outgoing':1}))
    configured['google_login']=bool(frappe.db.exists('Social Login Key',{'name':'google','enable_social_login':1}))
    try:
        settings=frappe.get_single('IL SOUL Settings')
        configured['openai']=bool(settings.enabled and settings.get_password('api_key',raise_exception=False))
    except Exception:configured['openai']=False
    return {'ready':all(checks.values()),'checks':checks,'release':'RUN3','provider_configured':configured,
        'installed_apps':frappe.get_installed_apps(),'provider_acceptance':'Requires staging',
        'note':'Heartbeat confirms one scheduled worker path, not all queues or provider availability.'}
