"""One recipient event, many durable deliveries. Accepted is not delivered."""
import hashlib
import hmac
import json
import frappe
from frappe.utils import now_datetime
from .saas import managed
from .saas_rules import notification_key

EVENTS=('whatsapp.payment_approved','whatsapp.enrolment_reminder','whatsapp.class_scheduled','delivery.submitted','delivery.reviewed','delivery.dispatched','payment.slip','payment.review','announcement','session.changed','material.created','assignment.created','assignment.due',
        'quiz.available','quiz.result','payment.successful','payment.failed','subscription.renewed',
        'subscription.expiry','course.expiry','certificate.issued','lesson.refunded','lesson.payment',
        'live.changed','recording.ready','recording.published','paper.ready','ai.low','premium.offer','premium.receipt')
CHANNELS=('IN_APP','EMAIL','SMS','WHATSAPP','PUSH')
LABELS={'IN_APP':'IN_APP','EMAIL':'Email','SMS':'SMS','WHATSAPP':'WhatsApp','PUSH':'PUSH'}

def preference(user,event):
    name=frappe.db.get_value('IL Notification Preference',{'user':user},'name')
    d=json.loads(frappe.db.get_value('IL Notification Preference',name,'settings') or '{}') if name else {}
    return {**{'IN_APP':True,'EMAIL':True,'WHATSAPP':True,'SMS':False,'PUSH':False},**d.get('channels',{}),**d.get('events',{}).get(event,{})}

def emit(institute,recipient,event,key,body,channels=None,classroom=None):
    if event not in EVENTS:raise ValueError('Unknown notification event')
    # Serialize initial insert as well as retries. All inserts share caller transaction.
    frappe.db.sql('SELECT name FROM `tabIL Member` WHERE name=%s FOR UPDATE',(recipient,))
    member=frappe.get_doc('IL Member',recipient,for_update=True)
    if member.institute!=institute:frappe.throw('Foreign notification recipient',frappe.PermissionError)
    event_key=notification_key(key,recipient)
    existing=frappe.db.sql('SELECT name FROM `tabIL Notification Event` WHERE event_key=%s FOR UPDATE',(event_key,))
    if existing:return existing[0][0]
    e=managed(frappe.get_doc({'doctype':'IL Notification Event','event_key':event_key,'event_type':event,
        'user':member.user,'recipient':recipient,'institute':institute,'body':str(body)[:1000],**({'classroom':classroom} if classroom else {})}))
    prefs=preference(member.user,event)
    from .notifications import whatsapp_allowed
    for channel in (channels or CHANNELS):
        enabled=bool(member.active and prefs[channel])
        if channel=='EMAIL':enabled=bool(enabled and member.contact_email_verified and member.email_opt_in and member.contact_email)
        if channel=='WHATSAPP':enabled=bool(enabled and whatsapp_allowed(member))
        if channel=='SMS':enabled=bool(enabled and frappe.db.exists('IL Verified Phone',{'user':member.user,'phone':member.phone}))
        devices=frappe.get_all('IL Device Token',filters={'user':member.user,'revoked':0},pluck='name') if channel=='PUSH' and enabled else [None]
        for device in devices or [None]:
            ready=enabled and (channel!='PUSH' or bool(device))
            status='Delivered' if channel=='IN_APP' and ready else 'Queued' if ready else 'Skipped'
            frappe.get_doc({'doctype':'IL Notification','institute':institute,'recipient':recipient,'event':e.name,
                'channel':LABELS[channel],'device':device,'event_key':notification_key(event_key,channel+':'+str(device)),
                'body':e.body,'status':status,'attempts':0,'next_attempt':now_datetime(),
                'sent_at':now_datetime() if status=='Delivered' else None}).insert(ignore_permissions=True)
    return e.name

@frappe.whitelist(methods=['POST'])
def save_preferences(settings):
    from .wallet import signed_in
    signed_in();data=json.loads(settings) if isinstance(settings,str) else settings
    if not isinstance(data,dict) or set(data)-{'channels','events'}:frappe.throw('Invalid preferences')
    entries=[data.get('channels',{})]
    events=data.get('events',{})
    if not isinstance(events,dict) or set(events)-set(EVENTS):frappe.throw('Invalid notification event')
    entries+=list(events.values())
    for row in entries:
        if not isinstance(row,dict) or set(row)-set(CHANNELS) or any(type(v) is not bool for v in row.values()):frappe.throw('Invalid channel preferences')
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE',(frappe.session.user,))
    name=frappe.db.get_value('IL Notification Preference',{'user':frappe.session.user},'name')
    d=frappe.get_doc('IL Notification Preference',name) if name else frappe.get_doc({'doctype':'IL Notification Preference','user':frappe.session.user})
    d.settings=json.dumps(data);managed(d)
    return {'saved':True}

@frappe.whitelist()
def inbox(page=0,unread=False):
    from .api import identity
    inst,m=identity();filters={'user':frappe.session.user,'institute':inst.name}
    if unread:filters['read_at']=['is','not set']
    # Only delivered in-app events are shown; preference-disabled events stay in outbox history.
    return frappe.db.sql('''SELECT e.name,e.body,e.event_type,e.creation,e.read_at FROM `tabIL Notification Event` e
        WHERE e.user=%s AND e.institute=%s AND (%s=0 OR e.read_at IS NULL)
        AND EXISTS (SELECT 1 FROM `tabIL Notification` d WHERE d.event=e.name AND d.channel='IN_APP' AND d.status='Delivered')
        ORDER BY e.creation DESC LIMIT 50 OFFSET %s''',(frappe.session.user,inst.name,int(bool(unread)),max(0,min(int(page),10000))*50),as_dict=True)

@frappe.whitelist(methods=['POST'])
def mark_read(name):
    from .wallet import signed_in
    signed_in();d=frappe.get_doc('IL Notification Event',name)
    if d.user!=frappe.session.user:frappe.throw('Notification unavailable',frappe.PermissionError)
    if not d.read_at:d.read_at=now_datetime();managed(d)
    return {'read':True}

def delivery_allowed(doc,member,channel):
    event=frappe.db.get_value('IL Notification Event',doc.event,'event_type') if doc.event else 'announcement'
    return preference(member.user,event or 'announcement').get(channel,False)

def delivery_timestamps(doc,method=None):
    if doc.status in ('Accepted','Delivered','Read') and not doc.sent_at:doc.sent_at=now_datetime()
    if doc.status=='Failed' and not doc.failed_at:doc.failed_at=now_datetime()

def dispatch_adapters():
    from .providers import sms,push
    from .saas import require
    with frappe.cache.lock('il_channel_dispatch',timeout=300,blocking_timeout=1):
        for name in frappe.get_all('IL Notification',filters={'channel':['in',['SMS','PUSH']],'status':'Queued'},pluck='name',limit_page_length=20):
            frappe.db.sql('SELECT name FROM `tabIL Notification` WHERE name=%s FOR UPDATE',(name,))
            d=frappe.get_doc('IL Notification',name,for_update=True);m=frappe.get_doc('IL Member',d.recipient)
            if d.status!='Queued':continue
            e=frappe.get_doc('IL Notification Event',d.event)
            if not m.active or not preference(m.user,e.event_type).get(d.channel):
                d.status='Skipped';d.save(ignore_permissions=True);frappe.db.commit();continue
            try:require('integrations.'+d.channel.lower())
            except frappe.PermissionError:continue
            if not frappe.conf.get('il_sms_adapter' if d.channel=='SMS' else 'il_push_adapter'):continue
            # Commit uncertain state BEFORE sending; worker crashes never blindly resend.
            d.status='Review';d.attempts=int(d.attempts or 0)+1;d.save(ignore_permissions=True);frappe.db.commit()
            try:
                if d.channel=='SMS':
                    if not frappe.db.exists('IL Verified Phone',{'user':m.user,'phone':m.phone}):raise ValueError('Phone verification changed')
                    result=sms(m.phone,d.body,d.event_key)
                else:
                    device=frappe.get_doc('IL Device Token',d.device)
                    if device.revoked or device.user!=m.user:raise ValueError('Device revoked')
                    result=push(device.get_password('token'),device.platform,d.body,d.event_key)
                d.status='Accepted';d.provider_id=result.get('provider_id');d.last_error=''
            except Exception:
                d.last_error='Provider delivery unconfirmed; reconcile before retrying'
            d.save(ignore_permissions=True);frappe.db.commit()

@frappe.whitelist(allow_guest=True,methods=['GET','POST'])
def whatsapp_webhook(**kwargs):
    request=frappe.request
    if request.method=='GET':
        token=frappe.conf.get('il_whatsapp_verify_token')
        if not token or not hmac.compare_digest(str(request.args.get('hub.verify_token','')),token):frappe.throw('Invalid verification token',frappe.PermissionError)
        if request.args.get('hub.mode')!='subscribe':frappe.throw('Invalid subscription verification')
        from werkzeug.wrappers import Response
        return Response(str(request.args.get('hub.challenge','')),mimetype='text/plain')
    raw=request.get_data(cache=True);secret=frappe.conf.get('il_whatsapp_app_secret')
    expected='sha256='+hmac.new(str(secret).encode(),raw,hashlib.sha256).hexdigest()
    if not secret or len(raw)>262144 or not hmac.compare_digest(expected,request.headers.get('X-Hub-Signature-256','')):
        frappe.throw('Invalid WhatsApp signature',frappe.PermissionError)
    data=json.loads(raw)
    rank={'Accepted':0,'Failed':1,'Delivered':2,'Read':3}
    for entry in data.get('entry',[]):
        for change in entry.get('changes',[]):
            value=change.get('value',{})
            if value.get('metadata',{}).get('phone_number_id')!=str(frappe.conf.get('il_whatsapp_phone_id')):continue
            for status in value.get('statuses',[]):
                target={'sent':'Accepted','delivered':'Delivered','read':'Read','failed':'Failed'}.get(status.get('status'))
                if not target:continue
                names=frappe.get_all('IL Notification',filters={'channel':'WhatsApp','provider_id':status.get('id')},pluck='name',limit_page_length=10)
                for name in names:
                    frappe.db.sql('SELECT name FROM `tabIL Notification` WHERE name=%s FOR UPDATE',(name,))
                    d=frappe.get_doc('IL Notification',name,for_update=True)
                    if rank.get(target,0)>=rank.get(d.status,0):d.status=target;d.save(ignore_permissions=True)
    return {'accepted':True}
