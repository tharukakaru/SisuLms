"""Tenant lesson products. Purchases never grant a classroom or SaaS subscription."""
import json
import hashlib
import uuid
import frappe
from frappe.utils import now_datetime, get_datetime, get_url
from .saas import managed, audit

PUBLIC=('name','title','description','includes','classroom','teacher','price_minor','currency','status','version','creation')

def checked(name, manage=False):
    from .api import identity,classroom_for
    inst,member=identity();doc=frappe.get_doc('IL Lecture Product',name)
    if doc.institute!=inst.name:frappe.throw('Lesson unavailable',frappe.PermissionError)
    if manage:
        _,_,room=classroom_for(doc.classroom,write=True)
        if member.role!='Admin' and doc.teacher!=member.user:frappe.throw('Lesson ownership required',frappe.PermissionError)
        from .teaching import require
        require(room,member,'edit')
    return doc,member

def owned(product,user):
    name=frappe.db.get_value('IL Lecture Access',{'product':product,'user':user,'revoked':0},'name')
    if not name:return None
    doc=frappe.get_doc('IL Lecture Access',name)
    if doc.expires_at and get_datetime(doc.expires_at)<=now_datetime():return None
    return doc

@frappe.whitelist()
def listing(library=False,purchases=False,classroom=None):
    from .api import identity,require_role
    inst,member=identity();filters={'institute':inst.name}
    if classroom:
        from .api import accessible_room
        accessible_room(classroom)
        filters['classroom']=classroom
    if library is True:
        require_role(member,'Teacher','Admin')
        if member.role=='Teacher':filters['teacher']=member.user
    elif purchases is True:
        ids=frappe.get_all('IL Lecture Access',filters={'user':member.user,'revoked':0},pluck='product')
        filters['name']=['in',ids or ['__none__']]
    else:filters['status']='Published'
    # Service-owned DocType has no generic Desk permissions. Authorize above,
    # then query only this institute and the selected ownership/publication scope.
    conditions=['institute=%s'];params=[inst.name]
    for field in ('classroom','teacher','status'):
        if field in filters:conditions.append('`'+field+'`=%s');params.append(filters[field])
    if 'name' in filters:
        names=filters['name'][1]
        conditions.append('name IN ('+','.join(['%s']*len(names))+')');params.extend(names)
    rows=frappe.db.sql('SELECT '+','.join('`'+field+'`' for field in PUBLIC)+' FROM `tabIL Lecture Product` WHERE '+
                       ' AND '.join(conditions)+' ORDER BY modified DESC LIMIT 100',tuple(params),as_dict=True)
    for row in rows:row['owned']=bool(owned(row.name,member.user));row['locked']=bool(row.price_minor and not row['owned'])
    return rows

@frappe.whitelist(methods=['POST'])
def save(data):
    from .api import classroom_for,require_role
    from .teaching import require
    from .pricing_rules import integer
    values=json.loads(data) if isinstance(data,str) else data
    if not isinstance(values,dict):frappe.throw('Invalid lesson')
    inst,member,room=classroom_for(values.get('classroom'),write=True);require_role(member,'Teacher','Admin');require(room,member,'edit')
    doc,_=checked(values['name'],True) if values.get('name') else (frappe.get_doc({'doctype':'IL Lecture Product','institute':inst.name,
        'classroom':room.name,'teacher':member.user,'version':1,'status':'Draft'}),member)
    if doc.classroom!=room.name:frappe.throw('A product cannot change classrooms')
    if not doc.is_new():
        frappe.db.sql('SELECT name FROM `tabIL Lecture Product` WHERE name=%s FOR UPDATE',(doc.name,))
        doc=frappe.get_doc('IL Lecture Product',doc.name,for_update=True)
    title=str(values.get('title','')).strip();price=integer(values.get('price_minor',0),'Price')
    if not 1<=len(title)<=120:frappe.throw('Lesson title required')
    status=values.get('status','Draft')
    if status not in ('Draft','Published','Unlisted','Archived'):frappe.throw('Invalid publication state')
    media=str(values.get('media_key') or doc.media_key or '').strip()
    if not media or len(media)>500 or '://' in media:frappe.throw('Use a private storage object key, not a public media URL')
    objects=frappe.get_all('IL Stored Object',filters={'storage_key':media,'institute':inst.name,
        'classroom':room.name,'owner_user':doc.teacher,'status':'ACTIVE'},fields=['name','backend','file','media_state'],limit_page_length=2)
    if len(objects)!=1 or objects[0].backend=='frappe':
        frappe.throw('An owned, classroom-scoped private media object is required',frappe.PermissionError)
    if objects[0].backend in ('s3_media','r2_media') and objects[0].media_state!='Ready':frappe.throw('Complete the private upload first')
    live=frappe.db.get_value('IL Live Room',{'stored_object':objects[0].name},'recording_status')
    if live and live!='Ready':frappe.throw('Recording is not ready for publication')
    if not doc.is_new() and media!=doc.media_key and frappe.db.exists('IL Lecture Order',{'product':doc.name}):
        frappe.throw('A sold/ordered media version cannot be replaced; publish a separate lesson version')
    doc.title=title;doc.description=str(values.get('description',''))[:4000];doc.includes=str(values.get('includes',''))[:2000]
    doc.price_minor=price;doc.currency='LKR';doc.media_key=media;doc.status=status
    doc.access_days=integer(values.get('access_days',0),'Access days',36500)
    if not doc.is_new():doc.version=int(doc.version or 0)+1
    managed(doc);audit('Lecture publication',doc.name,status)
    return {k:doc.get(k) for k in PUBLIC}

@frappe.whitelist(methods=['POST'])
def checkout(product,mobile=False):
    from .api import require_role
    from .payments_lk import config,provider_request
    from .payments_lk_contract import hosted_url
    doc,member=checked(product);require_role(member,'Student')
    frappe.db.sql('SELECT name FROM `tabIL Lecture Product` WHERE name=%s FOR UPDATE',(product,))
    doc=frappe.get_doc('IL Lecture Product',product)
    if owned(product,member.user):return {'owned':True}
    if doc.status!='Published' or doc.price_minor<=0:frappe.throw('Paid lesson unavailable')
    if not get_url().startswith('https://'):frappe.throw('HTTPS is required for checkout')
    key,_,mode=config()
    existing=frappe.db.get_value('IL Lecture Order',{'product':product,'user':member.user,'status':['in',['created','pending']]},'name')
    if existing:order=frappe.get_doc('IL Lecture Order',existing,for_update=True)
    else:
        wallets=frappe.get_all('IL Wallet',filters={'beneficiary':'Teacher','owner_user':doc.teacher,'currency':'LKR','enabled':1},pluck='name',limit_page_length=2)
        if len(wallets)!=1:frappe.throw('Teacher beneficiary wallet must be configured by finance')
        snapshot={'purpose':'lecture','product':doc.name,'version':doc.version,'media_key':doc.media_key,
            'title':doc.title,'access_days':doc.access_days or 0,'beneficiary':doc.teacher,'fee_minor':0,'tax_minor':0}
        order=managed(frappe.get_doc({'doctype':'IL Lecture Order','order_id':'lesson-'+uuid.uuid4().hex,'product':doc.name,
            'user':member.user,'institute':doc.institute,'amount_minor':doc.price_minor,'currency':'LKR','status':'created',
            'wallet':wallets[0],'mode':mode,'snapshot':json.dumps(snapshot),'request_key':'lesson-'+uuid.uuid4().hex}))
        order.request=json.dumps({'amountCents':order.amount_minor,'reference':order.name,'description':'SISU individual lecture',
            'successUrl':get_url('/mobile_payment_return' if mobile is True else '/campus#purchases'),'cancelUrl':get_url('/mobile_payment_return' if mobile is True else '/campus#purchases'),'locale':'en'})
        managed(order)
    from datetime import timedelta
    if order.mode!=mode or get_datetime(order.creation)<now_datetime()-timedelta(hours=23):frappe.throw('Existing purchase requires reconciliation')
    order.status='pending';managed(order);frappe.db.commit()
    result=provider_request('GET','/checkouts/'+order.checkout_id,key) if order.checkout_id else provider_request('POST','/checkouts',key,order.request,order.request_key)
    payment=result.get('payment') or {}
    import re
    if result.get('mode')!=mode or not hosted_url(result.get('url')) or payment.get('reference')!=order.name or payment.get('amountCents')!=order.amount_minor or payment.get('currency')!='LKR' or not re.fullmatch(r'chk_[A-Za-z0-9]{24}',str(result.get('id',''))):
        frappe.throw('Checkout requires reconciliation')
    frappe.db.sql('SELECT name FROM `tabIL Lecture Order` WHERE name=%s FOR UPDATE',(order.name,))
    current=frappe.get_doc('IL Lecture Order',order.name,for_update=True)
    if current.checkout_id and current.checkout_id!=result['id']:frappe.throw('Checkout identity changed')
    current.checkout_id=result['id'];managed(current)
    if result.get('status')!='open':frappe.db.commit();frappe.throw('Await verified settlement; checkout is not open')
    return {'order':current.name,'redirect_url':result['url']}

@frappe.whitelist(allow_guest=True,methods=['POST'])
def notify(**kwargs):
    from .payments_lk import config
    from .payments_lk_contract import verify_signature,valid_payment
    _,secret,mode=config();raw=frappe.request.get_data(cache=True)
    if len(raw)>65536 or not verify_signature(raw,frappe.request.headers.get('Payments-Signature'),secret):frappe.throw('Invalid payment signature',frappe.PermissionError)
    event=json.loads(raw);payment=event.get('data') or {};reference=payment.get('reference','')
    if not isinstance(reference,str) or not reference.startswith('lesson-'):frappe.throw('Wrong payment purpose',frappe.PermissionError)
    frappe.db.sql('SELECT name FROM `tabIL Lecture Order` WHERE name=%s FOR UPDATE',(reference,))
    order=frappe.get_doc('IL Lecture Order',reference,for_update=True)
    if event.get('mode')!=mode or order.mode!=mode:frappe.throw('Payment mode mismatch')
    incoming={'payment.failed':'failed','payment.cancelled':'cancelled'}.get(event.get('type'))
    if incoming:
        if not (payment.get('object')=='payment' and payment.get('status')==incoming and payment.get('mode')==mode
                and type(payment.get('amountCents')) is int and payment['amountCents']==order.amount_minor
                and payment.get('currency')==order.currency and bool(order.checkout_id) and payment.get('checkoutId')==order.checkout_id):
            frappe.throw('Payment identity mismatch',frappe.PermissionError)
        if order.status not in ('succeeded','refunded'):order.status=incoming;managed(order)
        audit('Lecture payment '+incoming,order.name,'Verified provider status')
        return {'accepted':True,'settled':order.status=='succeeded'}
    if event.get('type')!='payment.succeeded':return {'accepted':True,'settled':False}
    if not valid_payment(payment,{'name':order.name,'amount':order.amount_minor/100,'gateway_checkout_id':order.checkout_id},mode):frappe.throw('Payment identity mismatch',frappe.PermissionError)
    if order.status=='succeeded':
        if order.payment_id!=payment['id']:frappe.throw('Duplicate payment needs reconciliation')
        return {'accepted':True,'duplicate':True}
    if order.status=='refunded':frappe.throw('Refunded order cannot settle again')
    if frappe.db.exists('IL Lecture Order',{'payment_id':payment['id'],'name':['!=',order.name]}) or frappe.db.exists('IL Invoice',{'payment_id':payment['id']}):
        frappe.throw('Payment reference already used',frappe.PermissionError)
    snapshot=json.loads(order.snapshot)
    if snapshot.get('purpose')!='lecture':frappe.throw('Wrong settlement purpose')
    from .wallet import locked_wallet,post
    wallet=locked_wallet(order.wallet)
    if wallet.owner_user!=snapshot['beneficiary'] or wallet.beneficiary!='Teacher':frappe.throw('Beneficiary mismatch')
    post(wallet,'lecture:'+order.name,'Earning',int(order.amount_minor),0,reference=order.name,reason='Verified individual lecture payment')
    from datetime import timedelta
    now=now_datetime()
    access_key=hashlib.sha256((order.user+':'+order.product).encode()).hexdigest()
    prior=frappe.db.get_value('IL Lecture Access',{'access_key':access_key},'name')
    values={'doctype':'IL Lecture Access','access_key':access_key,
        'product':order.product,'user':order.user,'order':order.name,'media_key':snapshot['media_key'],
        'expires_at':now+timedelta(days=snapshot['access_days']) if snapshot['access_days'] else None,'revoked':0}
    access=frappe.get_doc('IL Lecture Access',prior,for_update=True) if prior else frappe.get_doc(values)
    if prior:access.update({k:v for k,v in values.items() if k!='doctype'})
    access=managed(access)
    order.status='succeeded';order.payment_id=payment['id'];order.paid_at=now;order.receipt_number='LESSON-'+order.name;managed(order)
    audit('Verified lecture settlement',order.name,access.name)
    from .notification_service import emit
    member=frappe.db.get_value('IL Member',{'user':order.user,'institute':order.institute},'name')
    if member:emit(order.institute,member,'payment.successful','lecture:'+order.name,'Lesson purchase confirmed. Receipt '+order.receipt_number)
    return {'accepted':True,'settled':True}

@frappe.whitelist()
def history(classroom=None):
    from .api import identity
    inst,member=identity()
    filters={'institute':inst.name,'user':member.user}
    if classroom:
        from .api import accessible_room
        accessible_room(classroom)
        products=frappe.get_all('IL Lecture Product',filters={'institute':inst.name,'classroom':classroom},pluck='name')
        filters['product']=['in',products or ['__none__']]
    return frappe.get_all('IL Lecture Order',filters=filters,
        fields=['name','product','amount_minor','currency','status','receipt_number','paid_at','creation'],order_by='creation desc',limit_page_length=100)

@frappe.whitelist()
def detail(name):
    doc,_=checked(name,True)
    return {k:doc.get(k) for k in PUBLIC+('media_key','access_days')}

@frappe.whitelist()
def receipt(name):
    from .api import identity
    inst,m=identity();d=frappe.get_doc('IL Lecture Order',name)
    if d.institute!=inst.name or (d.user!=m.user and m.role!='Admin'):frappe.throw('Receipt unavailable',frappe.PermissionError)
    if d.status not in ('succeeded','refunded'):frappe.throw('No verified payment receipt yet')
    return {**{k:d.get(k) for k in ('name','amount_minor','currency','status','receipt_number','paid_at','product')},
        'title':json.loads(d.snapshot).get('title'),'notice':'Payment receipt; not a tax invoice'}

@frappe.whitelist(methods=['POST'])
def playback(product):
    doc,member=checked(product);access=owned(product,member.user)
    if not access and (doc.price_minor or doc.status!='Published'):frappe.throw('Purchase required',frappe.PermissionError)
    media=access.media_key if access else doc.media_key
    if not frappe.db.exists('IL Stored Object',{'storage_key':media,'institute':doc.institute,'status':'ACTIVE'}):
        frappe.throw('Media unavailable; contact your institute')
    path=frappe.conf.get('il_private_video_adapter')
    if not path:frappe.throw('Protected video provider is not configured')
    value=frappe.get_attr(path)(object_key=media,user=member.user,expires_in=120)
    from urllib.parse import urlsplit
    url=value.get('url','') if isinstance(value,dict) else ''
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname not in (frappe.conf.get('il_private_video_hosts') or []) or parsed.username or parsed.password:
        frappe.throw('Protected media provider returned an invalid grant')
    from .workspace import consume_view,enforce_session
    room=frappe.get_doc('IL Classroom',doc.classroom)
    enforce_session(room,member);consume_view(room,member,'lecture:'+doc.name,'video')
    return {'url':url,'expires_in':120,'title':doc.title}
