"""Explicit, provider-scoped Zoom scheduling with uncertain-outcome protection."""
from urllib.parse import quote,urlsplit
import secrets,string
import frappe
from frappe.utils import get_datetime,now_datetime
def create(session):
    from .api import classroom_for
    from .commercial import account_for,require_room,locked
    from .workspace import record,DT
    doc=frappe.get_doc('IL Session',session)
    _,member,room=classroom_for(doc.classroom,write=True);require_room(room,'integrations')
    if doc.meeting_provider!='Zoom' or doc.mode!='Online':frappe.throw('Choose Zoom for this online session first')
    start,end=get_datetime(doc.starts_at),get_datetime(doc.ends_at)
    if start<=now_datetime() or end<=start or (end-start).total_seconds()>86400:frappe.throw('Schedule a future lesson lasting at most 24 hours')
    account=account_for(room);locked('IL Provider Account',account.name)
    key='zoom:'+doc.name
    previous=frappe.db.get_value(DT,{'record_key':key},'name')
    if previous:
        import json
        value=json.loads(frappe.get_doc(DT,previous).payload)
        if value.get('state')=='Created':return {'meeting_url':value['join_url'],'state':'Created'}
        frappe.throw('A previous Zoom request needs reconciliation. Check Zoom before creating another meeting.')
    if doc.meeting_url:frappe.throw('This session already has a meeting link. Manage it in Zoom.')
    config=(frappe.conf.get('il_zoom_server') or {}).get(account.name) or {}
    if not all(config.get(k) for k in ('account_id','client_id','client_secret','host_user')):frappe.throw('Connect this provider’s Zoom server-to-server OAuth account first')
    import requests
    try:
        token=requests.post('https://zoom.us/oauth/token',params={'grant_type':'account_credentials','account_id':config['account_id']},auth=(config['client_id'],config['client_secret']),timeout=15)
        if token.status_code!=200:frappe.throw('Zoom authorization failed. Check the configured account and scopes.')
        bearer=token.json().get('access_token')
        if not bearer:frappe.throw('Zoom did not return an access token')
    except requests.RequestException:frappe.throw('Could not connect to Zoom authorization. No meeting was requested.')
    # Persist intent before the remote side effect. Never blindly retry an ambiguous create.
    record(account,'Zoom',key,{'state':'Pending'},classroom=room.name,subject_user=member.user);frappe.db.commit()
    password=''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(10))
    payload={'topic':doc.title,'type':2,'start_time':start.strftime('%Y-%m-%dT%H:%M:%S'),'timezone':'Asia/Colombo','duration':max(1,int((end-start).total_seconds()/60)),
        'password':password,'settings':{'waiting_room':True,'join_before_host':False,'mute_upon_entry':True,'approval_type':2}}
    try:
        response=requests.post('https://api.zoom.us/v2/users/'+quote(config['host_user'],safe='')+'/meetings',headers={'Authorization':'Bearer '+bearer},json=payload,timeout=20)
        if response.status_code!=201:frappe.throw('Zoom did not confirm creation. Reconcile this session in Zoom before trying again.')
        result=response.json();url=result.get('join_url','');parsed=urlsplit(url)
        if parsed.scheme!='https' or not parsed.hostname or not (parsed.hostname=='zoom.us' or parsed.hostname.endswith('.zoom.us')) or parsed.username or parsed.password:frappe.throw('Zoom returned an unexpected meeting URL; reconcile in Zoom.')
        # Never return or store the privileged host start_url.
        record(account,'Zoom',key,{'state':'Created','meeting_id':str(result.get('id','')),'join_url':url})
        frappe.db.set_value('IL Session',doc.name,'meeting_url',url)
        return {'meeting_url':url,'state':'Created'}
    except requests.RequestException:frappe.throw('Zoom creation could not be confirmed. Check the host account; do not submit another request.')
