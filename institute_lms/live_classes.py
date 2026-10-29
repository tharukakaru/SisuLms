"""Class-scoped live authority. Scheduling never implies that a room is live."""
import hashlib
import frappe
from frappe.utils import now_datetime
from .saas import managed,audit

def checked(name,teach=False):
    from .api import accessible_room,classroom_for
    d=frappe.get_doc('IL Live Room',name)
    inst,member,room=classroom_for(d.classroom,write=True) if teach else accessible_room(d.classroom)
    if d.institute!=inst.name:frappe.throw('Foreign live room',frappe.PermissionError)
    # Admin monitoring does not imply recording authority. A named class teacher controls it.
    if teach and member.name!=room.teacher and room.get('owner_user')!=member.user:
        frappe.throw('Only the class teacher controls this live lesson',frappe.PermissionError)
    return d,member,room

@frappe.whitelist()
def listing(classroom=None):
    from .api import identity,room_filters
    inst,member=identity()
    rooms=frappe.get_all('IL Classroom',filters=room_filters(inst,member),pluck='name')
    if classroom:
        from .api import accessible_room
        accessible_room(classroom)
        rooms=[classroom] if classroom in rooms else []
    rows=frappe.get_all('IL Live Room',filters={'institute':inst.name,'classroom':['in',rooms or ['__none__']]},
        fields=['name','classroom','session','title','starts_at','status','recording_status','recording_published'],order_by='starts_at desc',limit_page_length=100)
    for row in rows:
        row['can_control']=False
        try:checked(row.name,True);row['can_control']=True
        except frappe.PermissionError:pass
    return rows

@frappe.whitelist(methods=['POST'])
def schedule(session):
    from .api import classroom_for
    s=frappe.get_doc('IL Session',session)
    inst,member,room=classroom_for(s.classroom,write=True)
    if member.name!=room.teacher and room.get('owner_user')!=member.user:frappe.throw('Class teacher required',frappe.PermissionError)
    old=frappe.db.get_value('IL Live Room',{'session':session},'name')
    if old:return {'name':old}
    d=managed(frappe.get_doc({'doctype':'IL Live Room','session':session,'institute':inst.name,'classroom':room.name,
        'title':s.title,'starts_at':s.starts_at,'status':'Upcoming','recording_status':'None',
        'provider_room':'sisu-'+hashlib.sha256((frappe.local.site+':'+session).encode()).hexdigest()}))
    return {'name':d.name}

@frappe.whitelist(methods=['POST'])
def control(name,action):
    if action not in ('start','end','record','stop_recording'):frappe.throw('Invalid live action')
    from .live_provider import operation
    with frappe.cache.lock('il_live:'+name,timeout=90,blocking_timeout=1):
        d,member,_=checked(name,True)
        if action=='start':
            if d.status=='Live':return {'status':d.status}
            if d.status!='Upcoming':frappe.throw('Create a new session after a lesson ends')
            operation('start',d.provider_room);d.status='Live'
        elif action=='end':
            operation('end',d.provider_room);d.status='Ended'
        elif action=='record':
            if d.status!='Live' or d.recording_status!='None':frappe.throw('Reconcile the existing recording; create a new session for a new recording')
            from .saas import quota
            from .usage import used
            maximum=int(frappe.conf.get('il_recording_reservation_bytes',1073741824))
            quota('storage_bytes',lambda:used('storage_bytes'),maximum)
            obj=managed(frappe.get_doc({'doctype':'IL Stored Object','institute':d.institute,'classroom':d.classroom,
                'owner_user':member.user,'bytes':maximum,'backend':'livekit','status':'ACTIVE',
                'storage_key':d.provider_room+'/recording.mp4'}))
            d.stored_object=obj.name;d.recording_status='Processing';managed(d);frappe.db.commit()
            # Ambiguous creation is not retried automatically; operator/provider reconciliation required.
            result=operation('record',d.provider_room,object_key=obj.storage_key)
            d.egress_id=result.egress_id;d.recording_status='Recording'
        else:
            if not d.egress_id:frappe.throw('Recording needs reconciliation')
            operation('stop_recording',d.provider_room,egress=d.egress_id);d.recording_status='Processing'
        managed(d);audit('Live '+action,d.name,'Teacher-authorized action')
        return {'status':d.status,'recording_status':d.recording_status}

@frappe.whitelist(methods=['POST'])
def join(name):
    d,member,room=checked(name)
    if d.status!='Live':frappe.throw('This live lesson is not active')
    teacher=member.name==room.teacher or room.get('owner_user')==member.user
    from .live_provider import participant
    return {**participant(d.provider_room,member.name,member.full_name,teacher,bool(d.student_publish)),
            'name':d.name,'can_control':teacher,'recording_status':d.recording_status}

@frappe.whitelist(methods=['POST'])
def recording(name):
    d,member,_=checked(name)
    if d.recording_status!='Ready':frappe.throw('Recording is not ready')
    if member.role=='Student' and not d.recording_published:frappe.throw('Recording awaits teacher review')
    obj=frappe.get_doc('IL Stored Object',d.stored_object)
    if obj.institute!=d.institute or obj.status!='ACTIVE':frappe.throw('Recording unavailable')
    path=frappe.conf.get('il_private_video_adapter')
    if not path:frappe.throw('Protected video provider is not configured')
    value=frappe.get_attr(path)(object_key=obj.storage_key,user=member.user,expires_in=120)
    from urllib.parse import urlsplit
    parsed=urlsplit(value.get('url',''))
    if parsed.scheme!='https' or parsed.hostname not in (frappe.conf.get('il_private_video_hosts') or []) or parsed.username or parsed.password:
        frappe.throw('Invalid media grant')
    from .workspace import consume_view,enforce_session
    room=frappe.get_doc('IL Classroom',d.classroom)
    enforce_session(room,member);consume_view(room,member,'live-recording:'+d.name,'video')
    return {'url':value['url'],'expires_in':120,'title':d.title}

@frappe.whitelist(methods=['POST'])
def lecture_draft(name):
    d,_,_=checked(name,True)
    if d.recording_status!='Ready':frappe.throw('Recording is not ready')
    obj=frappe.get_doc('IL Stored Object',d.stored_object)
    prior=frappe.db.get_value('IL Lecture Product',{'media_key':obj.storage_key,'classroom':d.classroom},'name')
    if prior:return {'name':prior}
    from .lectures import save
    return save({'classroom':d.classroom,'title':d.title,'media_key':obj.storage_key,'price_minor':0,'status':'Draft'})

@frappe.whitelist(allow_guest=True,methods=['POST'])
def webhook(**kwargs):
    from .live_provider import webhook as verify
    raw=frappe.request.get_data(cache=True)
    if len(raw)>1048576:frappe.throw('Invalid live event')
    try:event=verify(raw.decode('utf-8'),frappe.request.headers.get('Authorization',''))
    except Exception:frappe.throw('Invalid live webhook',frappe.PermissionError)
    if event.event=='room_finished':
        name=frappe.db.get_value('IL Live Room',{'provider_room':event.room.name},'name')
        if name:
            d=frappe.get_doc('IL Live Room',name,for_update=True);d.status='Ended';managed(d)
    if event.event=='egress_ended':
        info=event.egress_info
        name=frappe.db.get_value('IL Live Room',{'egress_id':info.egress_id},'name')
        if not name:return {'accepted':True,'reconciliation_required':True}
        d=frappe.get_doc('IL Live Room',name,for_update=True)
        if d.recording_status in ('Ready','Failed'):return {'accepted':True,'duplicate':True}
        files=list(info.file_results)
        obj=frappe.get_doc('IL Stored Object',d.stored_object,for_update=True)
        size=sum(int(f.size) for f in files)
        complete=int(info.status)==3 and len(files)==1 and files[0].filename==obj.storage_key and size>0
        d.recording_status='Ready' if complete else 'Failed'
        if size>0:
            obj.bytes=size if complete else max(size,int(obj.bytes));managed(obj)
        managed(d)
    return {'accepted':True}

@frappe.whitelist(methods=['POST'])
def publish_recording(name,reviewed=False):
    d,_,_=checked(name,True)
    if d.recording_status!='Ready' or reviewed is not True:frappe.throw('Review the ready recording before publication')
    d.recording_published=1;managed(d);audit('Recording published',d.name,'Teacher reviewed classroom recording')
    from .product_events import classroom_event
    classroom_event(d.classroom,'recording.published',d.name,'Class recording is available: '+d.title)
    return {'published':True}

@frappe.whitelist(methods=['POST'])
def reconcile(name):
    from .live_provider import operation
    with frappe.cache.lock('il_live:'+name,timeout=90,blocking_timeout=1):
        d,_,_=checked(name,True)
        if d.recording_status=='Ready':return {'recording_status':'Ready'}
        if not d.stored_object:frappe.throw('No recording reservation exists')
        obj=frappe.get_doc('IL Stored Object',d.stored_object,for_update=True)
        result=operation('reconcile',d.provider_room)
        matches=[e for e in result.items if e.room_name==d.provider_room and
            ((d.egress_id and e.egress_id==d.egress_id) or (not d.egress_id and any(f.filename==obj.storage_key for f in e.file_results)))]
        if len(matches)!=1:frappe.throw('Provider outcome remains ambiguous; reservation retained')
        e=matches[0];d.egress_id=e.egress_id
        files=list(e.file_results);size=sum(int(f.size) for f in files)
        if int(e.status)==3 and len(files)==1 and files[0].filename==obj.storage_key and size>0:
            obj.bytes=size;managed(obj);d.recording_status='Ready'
        elif int(e.status) in (4,5,6):d.recording_status='Failed'
        else:d.recording_status='Processing'
        managed(d);audit('Recording reconciled',d.name,d.recording_status)
        return {'recording_status':d.recording_status}

@frappe.whitelist(methods=['POST'])
def cleanup_failed(name,reason):
    from .live_provider import operation
    from .private_media import client
    from .media_reconciliation import remove_exact
    from .saas import state
    with frappe.cache.lock('il_live:'+name,timeout=90,blocking_timeout=1):
        d,_,_=checked(name,True);state(lock=True)
        if d.recording_status=='Removed':return {'status':'Removed'}
        if d.recording_status!='Failed' or not d.egress_id or len(str(reason).strip())<10:
            frappe.throw('Reconcile a failed recording and provide an audit reason first')
        obj=frappe.get_doc('IL Stored Object',d.stored_object,for_update=True)
        if obj.get('legal_hold') or d.recording_published or frappe.db.exists('IL Lecture Product',{'media_key':obj.storage_key}) or frappe.db.exists('IL Lecture Access',{'media_key':obj.storage_key}):
            frappe.throw('Held or referenced recording cannot be removed')
        result=operation('reconcile',d.provider_room)
        matches=[e for e in result.items if e.egress_id==d.egress_id and e.room_name==d.provider_room]
        if len(matches)!=1 or int(matches[0].status) not in (4,5,6):frappe.throw('Provider has not confirmed terminal failure; quota retained')
        provider,bucket=client()
        recording_config=frappe.conf.get('il_live_recording_s3') or {}
        private_config=frappe.conf.get('il_private_media_s3') or {}
        if bucket!=recording_config.get('bucket') or private_config.get('endpoint_url','')!=recording_config.get('endpoint','') or private_config.get('region')!=recording_config.get('region'):
            frappe.throw('Recording and cleanup storage configuration must match exactly')
        remove_exact(provider,bucket,obj.storage_key,versioned=private_config.get('provider')!='r2')
        obj.status='PURGED';obj.media_state='Removed';managed(obj)
        d.recording_status='Removed';managed(d);audit('Failed recording removed',d.name,reason)
        return {'status':'Removed','released_bytes':obj.bytes}

@frappe.whitelist()
def room_status(name):
    d,_,_=checked(name)
    return {'status':d.status,'recording_status':d.recording_status}
