"""Platinum physical material delivery. No automatic bank settlement or courier calls."""
import hashlib
import json
import frappe
from frappe.utils import now_datetime, getdate
from .delivery_rules import address_snapshot, offer_values, next_status
from .commercial_rules import money_minor
from .plan_catalog import plan_features

def save(doc):
    doc.flags.delivery_service=True
    return doc.save(ignore_permissions=True)

def context(classroom,write=False,require_plan=True):
    from .api import classroom_for, access
    from .commercial import account_for, locked_reason
    inst,member,room=classroom_for(classroom,write)
    if not room.active:frappe.throw('This classroom is archived',frappe.PermissionError)
    account=account_for(room,False)
    if account and locked_reason(account):frappe.throw(locked_reason(account),frappe.PermissionError)
    allowed=bool(account and plan_features(account.plan).get('tute_delivery'))
    if require_plan and not allowed:frappe.throw('Tute delivery requires the class owner’s Platinum package',frappe.PermissionError)
    if member.role=='Student' and not access(room,member)['allowed']:
        frappe.throw('Active classroom access is required',frappe.PermissionError)
    return inst,member,room,account,allowed

def offer_for(room):
    name=frappe.db.get_value('IL Delivery Offer',{'classroom':room.name},'name')
    return frappe.get_doc('IL Delivery Offer',name) if name else None

def lock(doctype,name):
    frappe.db.sql('SELECT name FROM `tab'+doctype+'` WHERE name=%s FOR UPDATE',(name,))
    return frappe.get_doc(doctype,name)

@frappe.whitelist()
def state(classroom,page=0):
    inst,member,room,account,allowed=context(classroom,require_plan=False)
    base=dict(available=allowed,plan=account.plan if account else 'Unassigned',owner_type=room.get('owner_type') or 'Institute',gateway_ready=False)
    if not allowed:return dict(base,offer=None,orders=[],has_more=False)
    offer=offer_for(room)
    filters={'institute':inst.name,'classroom':room.name}
    if member.role=='Student':filters['student']=member.name
    fields=['name','student','offer_revision','title','amount_minor','recipient','phone','address_line1','address_line2','city','region','postal_code','country','status','reference','transfer_date','review_note','courier','tracking_reference','creation']
    rows=frappe.get_all('IL Delivery Order',filters=filters,fields=fields,order_by='creation desc',start=max(0,int(page))*25,page_length=26)
    config={k:offer.get(k) for k in ('enabled','revision','title','description','amount_minor','bank_instructions')} if offer else None
    current_status=frappe.db.get_value('IL Delivery Order',{'classroom':room.name,'student':member.name,'offer_revision':offer.revision},'status') if member.role=='Student' and offer else None
    return dict(base,offer=config,orders=rows[:25],has_more=len(rows)>25,current_order_status=current_status)

@frappe.whitelist(methods=['POST'])
def configure(classroom,data):
    inst,member,room,account,_=context(classroom,True)
    values=offer_values(json.loads(data) if isinstance(data,str) else data)
    lock('IL Classroom',room.name)
    offer=offer_for(room)
    if not offer and not values['enabled']:return {'saved':True}
    if not offer:offer=frappe.get_doc(dict(doctype='IL Delivery Offer',classroom=room.name,institute=inst.name,revision=0))
    changed=any(offer.get(k)!=v for k,v in values.items() if k!='enabled')
    if changed:offer.revision=int(offer.revision or 0)+1
    offer.update(values);offer.updated_by=frappe.session.user;save(offer)
    return {'saved':True}

@frappe.whitelist(methods=['POST'])
def submit_order(classroom,data,proof):
    from .commercial import owned_proof, notify_people
    inst,member,room,account,_=context(classroom)
    if member.role!='Student':frappe.throw('Student account required',frappe.PermissionError)
    data=json.loads(data) if isinstance(data,str) else data
    address=address_snapshot(data)
    lock('IL Classroom',room.name)
    offer=offer_for(room)
    if not offer or not offer.enabled:frappe.throw('Delivery is switched off for this class')
    if int(data.get('offer_revision') or 0)!=offer.revision:frappe.throw('The material offer changed. Refresh and confirm the new price')
    if money_minor(data.get('amount'))!=offer.amount_minor:frappe.throw('The bank transfer must match the material and delivery total')
    reference=str(data.get('reference') or '').strip()
    if not reference or len(reference)>140:frappe.throw('Add a bank transaction reference')
    if not data.get('transfer_date') or getdate(data['transfer_date'])>getdate(now_datetime()):frappe.throw('Enter a transfer date that is not in the future')
    key=hashlib.sha256((room.name+':'+member.name+':'+str(offer.revision)).encode()).hexdigest()
    existing=frappe.db.get_value('IL Delivery Order',{'order_key':key},'name')
    order=lock('IL Delivery Order',existing) if existing else None
    if order and order.status!='Rejected':frappe.throw('You already ordered this material. See your order below')
    file,digest=owned_proof(proof)
    if frappe.db.exists('IL Bank Slip',{'proof_hash':digest}) or frappe.db.exists('IL Delivery Order',{'proof_hash':digest}):frappe.throw('This bank slip has already been used')
    payment_key=hashlib.sha256((account.name+':'+reference.casefold()).encode()).hexdigest()
    duplicate_filters={'payment_key':payment_key}
    if order:duplicate_filters['name']=['!=',order.name]
    if frappe.db.exists('IL Delivery Order',duplicate_filters) or frappe.db.exists('IL Invoice',{'payment_id':'BANK-'+payment_key}):frappe.throw('This transfer reference has already been used')
    if not order:order=frappe.get_doc(dict(doctype='IL Delivery Order',order_key=key,institute=inst.name,classroom=room.name,student=member.name))
    order.update(dict(**address,provider_account=account.name,offer_revision=offer.revision,title=offer.title,amount_minor=offer.amount_minor,address_confirmed_at=now_datetime(),proof_file=file.name,proof_hash=digest,reference=reference,payment_key=payment_key,transfer_date=data['transfer_date'],status='Pending',review_note='',reviewed_by=None,reviewed_at=None))
    save(order)
    file.attached_to_doctype='IL Delivery Order';file.attached_to_name=order.name;file.save(ignore_permissions=True)
    notify_people(room,'delivery.submitted','delivery:'+order.name,'A material delivery order needs payment review for '+room.title,member.name)
    return {'name':order.name,'status':order.status}

def checked_order(name,write=False):
    order=frappe.get_doc('IL Delivery Order',name)
    inst,member,room,_,_=context(order.classroom,write)
    if order.institute!=inst.name or (member.role=='Student' and order.student!=member.name):
        frappe.throw('Delivery order unavailable',frappe.PermissionError)
    return order,member,room

@frappe.whitelist(methods=['POST'])
def review_order(name,decision,note):
    from .commercial import notify_people
    order,_,room=checked_order(name,True);order=lock('IL Delivery Order',order.name)
    status=next_status(order.status,decision)
    if decision not in ('Approved','Rejected'):frappe.throw('Choose approve or reject')
    if not str(note).strip() or len(str(note))>1000:frappe.throw('Add a bank verification or rejection note')
    order.update(dict(status=status,review_note=str(note).strip(),reviewed_by=frappe.session.user,reviewed_at=now_datetime()));save(order)
    notify_people(room,'delivery.reviewed','delivery-review:'+order.name+':'+str(order.modified),'Material delivery payment '+status.lower()+' for '+room.title,order.student)
    return {'status':status}

@frappe.whitelist(methods=['POST'])
def dispatch(name,courier,tracking_reference):
    from .commercial import notify_people
    order,_,room=checked_order(name,True);order=lock('IL Delivery Order',order.name)
    status=next_status(order.status,'Dispatched')
    if any(not str(v).strip() or len(str(v))>140 for v in (courier,tracking_reference)):frappe.throw('Add courier and tracking reference')
    order.update(dict(status=status,courier=str(courier).strip(),tracking_reference=str(tracking_reference).strip(),dispatched_at=now_datetime()));save(order)
    notify_people(room,'delivery.dispatched','delivery-dispatched:'+order.name,'Your material for '+room.title+' has been dispatched. Open your classroom for tracking.',order.student)
    return {'status':status}

@frappe.whitelist()
def proof(name):
    order,_,_=checked_order(name)
    file=frappe.get_doc('File',order.proof_file)
    if not file.is_private or file.attached_to_doctype!='IL Delivery Order' or file.attached_to_name!=order.name:frappe.throw('Proof unavailable',frappe.PermissionError)
    frappe.local.response.update(type='download',filename=file.file_name,filecontent=file.get_content(),display_content_as='attachment')
