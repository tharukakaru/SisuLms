"""Small authenticated UI contracts; never queries another site's database."""
import json
from urllib.parse import urlsplit
import frappe


def https_origin(value):
    try:
        u=urlsplit(value or '')
        if u.scheme=='https' and u.hostname and not u.username and not u.password and u.path in ('','/') and not u.query and not u.fragment:
            return value.rstrip('/')
    except ValueError:pass
    return None


@frappe.whitelist()
def workspace():
    from .account_storage import configured,workspace as account_workspace
    if configured():return account_workspace()
    from .api import identity
    from .saas import resolved
    from .usage import summary,used
    inst,m=identity();r=resolved()
    data={'subscription':r,'storage_backend':frappe.conf.get('il_storage_backend','frappe'),
          'billing_url':None,'usage':None}
    if m.role=='Admin':
        data['usage']=summary()
        origin=https_origin(frappe.conf.get('il_control_plane_url'))
        if origin:data['billing_url']=origin+'/campus'
    # Allocation information is tenant-local and used for upload warnings only.
    n=used('storage_bytes');limit=r['limits']['storage_bytes']
    data['storage']={'used':n,'limit':limit,'remaining':max(0,limit-n)}
    return data


@frappe.whitelist()
def billing():
    from .platform import control,organization
    from .wallet import signed_in,admin_actor
    control();signed_in()
    filters={} if admin_actor() else {'admin_contact':frappe.session.user}
    rows=frappe.get_all('IL Organization',filters=filters,fields=['name','title','site_hostname','enabled'],limit_page_length=100)
    for row in rows:
        organization(row.name,administrator=True)
        row['subscription']=frappe.db.get_value('IL Subscription',{'tenant_id':row.name},
            ['plan','state','starts_at','ends_at','grace_until','features','limits','overrides','support_tier'],as_dict=True)
        row['payments']=frappe.get_all('IL Payment Attempt',filters={'tenant_id':row.name},
            fields=['name','status','amount_minor','currency','creation'],order_by='creation desc',limit_page_length=20)
    plans=frappe.get_all('IL SaaS Plan',filters={'name':['in',['STARTER','PREMIUM AI']]},fields=['name','features','limits','price_minor','period_days','version'],limit_page_length=3)
    return {'organizations':rows,'plans':plans,'usage_available':False}


@frappe.whitelist()
def control_room(page=0):
    from .platform import owner,organizations
    owner();data={'plans':frappe.get_all('IL SaaS Plan',fields=['name','features','limits','price_minor','period_days','version'],limit_page_length=3),'usage_available':False}
    data['organizations']=organizations(page=page)
    data['jobs']=frappe.get_all('IL Provisioning Job',fields=['name','organization','status','detail','modified'],order_by='modified desc',limit_page_length=100)
    data['counts']={k:frappe.db.count('IL Organization',f) for k,f in [('registered',{}),('enabled',{'enabled':1}),('disabled',{'enabled':0})]}
    from .saas_rules import FEATURES,LIMITS
    data.update(feature_keys=FEATURES,limit_keys=LIMITS)
    return data


@frappe.whitelist(methods=['POST'])
def custom_price(tenant,amount_minor,period,reason):
    """Tenant-scoped platform contract; no fake institute row on the control plane."""
    from .platform import owner,organization
    from .owner_pricing import save
    from .saas import audit
    from .pricing_rules import integer
    owner();d=organization(tenant)
    amount=integer(amount_minor,'Price')
    if not amount or period not in ('Monthly','Yearly') or not str(reason).strip():frappe.throw('Positive price, period and audit reason required')
    frappe.db.sql('SELECT name FROM `tabIL Organization` WHERE name=%s FOR UPDATE',(tenant,))
    for name in frappe.get_all('IL Price Assignment',filters={'tenant_id':tenant,'product':'Platform','active':1},pluck='name'):
        old=frappe.get_doc('IL Price Assignment',name);old.active=0;save(old)
    doc=save(frappe.get_doc({'doctype':'IL Price Assignment','customer':d.admin_contact,'customer_kind':'Institute',
        'tenant_id':tenant,'product':'Platform','currency':'LKR','period':period,'base_minor':amount,'included_units':0,
        'unit_minor':0,'discount_bps':0,'tax_bps':0,'reason':reason,'active':1,'assigned_by':frappe.session.user}))
    audit('Assign organization contract',tenant,reason)
    return {'assignment':doc.name}


@frappe.whitelist()
def channels():
    from .wallet import signed_in
    signed_in()
    features={}
    if not frappe.conf.get('il_control_plane'):
        from .account_billing import policy
        try:r=policy();features=r['features'] if r['available'] else {}
        except frappe.PermissionError:pass
    configured={'IN_APP':True,'EMAIL':bool(frappe.db.exists('Email Account',{'enable_outgoing':1})),
        'SMS':bool(frappe.conf.get('il_sms_adapter')),
        'WHATSAPP':all(bool(frappe.conf.get(k)) for k in ('il_whatsapp_token','il_whatsapp_phone_id','il_whatsapp_graph_version','il_whatsapp_templates')),
        'PUSH':bool(frappe.conf.get('il_push_adapter'))}
    available={k:bool(v and (k=='IN_APP' or features.get('integrations.'+k.lower()))) for k,v in configured.items()}
    raw=frappe.db.get_value('IL Notification Preference',{'user':frappe.session.user},'settings')
    saved=json.loads(raw or '{}')
    preferences={**{'IN_APP':True,'EMAIL':True,'WHATSAPP':True,'SMS':False,'PUSH':False},**saved.get('channels',{})}
    return {'available':available,'configured':configured,'preferences':preferences,'settings':saved,
        'browser_push_available':bool(available['PUSH'] and frappe.conf.get('il_web_push_enabled'))}


@frappe.whitelist()
def otp_status():
    from .wallet import signed_in
    signed_in()
    return {'verified':bool(frappe.db.exists('IL Verified Phone',{'user':frappe.session.user})),
        'SMS':bool(frappe.conf.get('il_sms_adapter') or frappe.get_hooks('il_send_verification_sms')),
        'WHATSAPP':all(bool(frappe.conf.get(k)) for k in ('il_whatsapp_token','il_whatsapp_phone_id','il_whatsapp_graph_version','il_whatsapp_auth_template')),
        'cooldown_seconds':60,'expiry_seconds':600}


@frappe.whitelist()
def unread(profile=''):
    from .api import identity
    from .learning_spaces import notification_rooms
    inst,m=identity();names=notification_rooms(profile,inst)
    scope=' AND e.classroom IN %s' if names is not None else ''
    params=[frappe.session.user,inst.name]
    if names is not None:params.append(tuple(names or ['__none__']))
    return {'count':frappe.db.sql("""SELECT COUNT(*) FROM `tabIL Notification Event` e
        WHERE e.user=%s AND e.institute=%s AND e.read_at IS NULL
        AND EXISTS (SELECT 1 FROM `tabIL Notification` d WHERE d.event=e.name AND d.channel='IN_APP' AND d.status='Delivered')"""+scope,tuple(params))[0][0]}


@frappe.whitelist()
def learning_sources(classroom):
    # Source discovery does not call a provider or grant access by opaque index ID.
    from .saas import resolved
    r=resolved()
    if not r['available'] or not any(v for k,v in r['features'].items() if k.startswith('ai.')):
        frappe.throw('AI feature unavailable',frappe.PermissionError)
    from .ai_access import authorize
    feature=next(k for k,v in r['features'].items() if k.startswith('ai.') and v)
    inst,m,room=authorize(feature,classroom)
    from .knowledge import current
    result=[]
    for name in frappe.get_all('IL Knowledge Document',filters={'institute':inst.name,'classroom':room.name,'status':'Ready','enabled':1},pluck='name',limit_page_length=100):
        d=frappe.get_doc('IL Knowledge Document',name)
        try:current(d,room)
        except (PermissionError,frappe.PermissionError,frappe.DoesNotExistError):continue
        result.append({k:d.get(k) for k in ('name','title','version','source_type','source_name')})
    return result
