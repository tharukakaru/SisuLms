"""Institute-issued invitations require the addressed teacher's explicit consent."""
import hashlib
from datetime import timedelta
from html import escape
from urllib.parse import urlsplit
import frappe
from .message_templates import sendmail
from frappe.utils import now_datetime,get_url,get_datetime
from .registration import limit
from .contact import email_address

def invitation_origin():
    """Use one configured HTTPS address in requests and background email jobs."""
    origin = str(frappe.conf.get('il_teacher_invitation_origin') or get_url()).rstrip('/')
    try:
        parsed = urlsplit(origin)
        valid = (parsed.scheme == 'https' and parsed.hostname and not parsed.username
                 and not parsed.password and not parsed.path and not parsed.query
                 and not parsed.fragment and not any(c.isspace() for c in origin))
        parsed.port  # Reject malformed ports too.
    except ValueError:
        valid = False
    if not valid:
        frappe.throw('Teacher invitations need a configured HTTPS site address. Contact your SISU administrator.')
    return origin

def send_notice(email,subject,body,invitation=None):
    if not frappe.db.exists('Email Account',{'enable_outgoing':1}):return False
    queued=sendmail(frappe, recipients=[email],subject=subject,message='<p>'+escape(body)+'</p><p><a href="'+escape(invitation_origin()+'/campus#invitations',quote=True)+'">Review invitations in SISU</a></p>',delayed=True,reference_doctype='IL Teacher Invitation' if invitation else None,reference_name=invitation)
    if invitation:
        if not queued:frappe.throw('The invitation email could not be queued. Check outgoing email settings.')
        frappe.enqueue('institute_lms.invitations.dispatch_invitation',invitation=invitation,enqueue_after_commit=True,queue='short')
    return True

def require_mail():
    if not frappe.db.exists('Email Account',{'enable_outgoing':1}):
        frappe.throw('Teacher invitations need an enabled outgoing Email Account. Contact your SISU administrator.')
    invitation_origin()

@frappe.whitelist(methods=['POST'])
def invite_teacher(email):
    from .api import identity,require_role
    from .teaching import institute_profile
    inst,member=identity();require_role(member,'Admin');require_mail()
    try:email=email_address(email.strip())
    except ValueError as e:frappe.throw(str(e))
    limit('teacher-invite:'+member.user)
    profile=institute_profile(inst)
    with frappe.cache.lock('il_invite:'+inst.name+':'+email,timeout=10):
        if frappe.db.exists('IL Profile Relationship',{'profile':profile,'user':email,'kind':'Teacher membership','status':'Active'}):
            frappe.throw('This teacher is already connected to your institute.')
        if frappe.db.exists('IL Teacher Invitation',{'institute':inst.name,'invite_email':email,'status':'Pending','expires_at':['>',now_datetime()]}):frappe.throw('An invitation for this email is already pending')
        d=frappe.get_doc({'doctype':'IL Teacher Invitation','institute':inst.name,'profile':profile,'invite_email':email,'invited_by':member.user,'status':'Pending','expires_at':now_datetime()+timedelta(days=7)})
        d.flags.contact_service=True;d.insert(ignore_permissions=True)
        send_notice(email,'You are invited to teach at '+inst.title,inst.title+' invited you to teach on SISU. Sign in with this email and accept or reject the invitation within 7 days. Accepting connects your institute workspace. Your personal workspace stays separate; the institute assigns your classes.',invitation=d.name)
    return {'name':d.name,'status':'Pending','email_queued':True}

@frappe.whitelist(methods=['POST'])
def list_invitations():
    from .api import identity,require_role
    inst,m=identity();require_role(m,'Admin','Teacher')
    filters={'institute':inst.name} if m.role=='Admin' else {'invite_email':m.user.lower()}
    rows=frappe.get_all('IL Teacher Invitation',filters=filters,fields=['name','invite_email','profile','institute','status','expires_at','creation','responded_at'],order_by='creation desc',limit_page_length=0)
    for r in rows:
        r['institute_title']=frappe.db.get_value('IL Public Profile',r.profile,'display_name')
        queue_status=frappe.db.get_value('Email Queue',{'reference_doctype':'IL Teacher Invitation','reference_name':r.name},'status')
        r['email_status']={'Sent':'Sent to email server','Not Sent':'Queued for email','Sending':'Sending email','Error':'Email failed — contact support','Partially Sent':'Email delivery needs review'}.get(queue_status,'Email status unavailable')
        r['expired']=r.status=='Pending' and get_datetime(r.expires_at)<=now_datetime()
        r['connected']=r.status=='Accepted' and bool(frappe.db.exists('IL Profile Relationship',{'profile':r.profile,'user':r.invite_email,'kind':'Teacher membership','status':'Active'}) and frappe.db.exists('IL Member',{'institute':r.institute,'user':r.invite_email,'role':'Teacher','active':1}))
    return rows

@frappe.whitelist(methods=['POST'])
def respond(name,decision):
    from .api import identity,require_role
    from .profiles import mine
    from .teacher_identity import eligible
    _,m=identity();require_role(m,'Teacher');p=mine()
    if not p or p.kind!='Teacher' or (p.status!='Verified' and not eligible(m.user)):
        frappe.throw('Complete your teacher identity verification first',frappe.PermissionError)
    if decision not in ('Accepted','Declined'):frappe.throw('Choose accept or decline')
    frappe.db.sql('SELECT name FROM `tabIL Teacher Invitation` WHERE name=%s FOR UPDATE',(name,))
    d=frappe.get_doc('IL Teacher Invitation',name)
    if d.invite_email.lower()!=m.user.lower():frappe.throw('This invitation belongs to another account',frappe.PermissionError)
    if d.status==decision:return {'status':decision}
    if d.status!='Pending' or get_datetime(d.expires_at)<=now_datetime():frappe.throw('This invitation is no longer pending')
    if decision=='Accepted':connect_teacher(d,m.user)
    d.status=decision;d.responded_at=now_datetime();d.flags.contact_service=True;d.save(ignore_permissions=True)
    from .invitation_notifications import queue_response
    queue_response(d,p)
    return {'status':decision}


def connect_teacher(invitation,user):
    """An invitation authorizes only Teacher membership in its original institute."""
    from .profiles import write
    from .campus_teachers import sync
    target=frappe.get_doc('IL Public Profile',invitation.profile)
    if target.kind!='Institute' or target.status!='Verified' or target.workspace!=invitation.institute:
        frappe.throw('This institute invitation is no longer available')
    if not frappe.db.exists('IL Member',{'institute':invitation.institute,'user':invitation.invited_by,'role':'Admin','active':1}):
        frappe.throw('The inviting administrator no longer has access. Ask the institute for a new invitation.')
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE',(user,))
    current=set(frappe.get_all('IL Profile Relationship',filters={'user':user,'kind':'Teacher membership','status':['in',['Pending','Active']]},pluck='profile'))
    if len(current|{target.name})>5:frappe.throw('You can have at most five active or pending institute memberships.')
    key=hashlib.sha256(f'{user}:{target.name}:Teacher membership'.encode()).hexdigest()
    existing=frappe.db.get_value('IL Profile Relationship',{'relationship_key':key},'name')
    relationship=frappe.get_doc('IL Profile Relationship',existing) if existing else frappe.get_doc({'doctype':'IL Profile Relationship','relationship_key':key,'profile':target.name,'user':user,'kind':'Teacher membership'})
    # A removal after the invitation was issued invalidates that old invitation.
    if existing and relationship.status in ('Removed','Rejected','Left') and get_datetime(relationship.modified)>get_datetime(invitation.creation):
        frappe.throw('Membership changed after this invitation. Ask the institute to send a new invitation.')
    sync(relationship,invitation.institute,'Active')
    relationship.status='Active';relationship.reviewed_by=invitation.invited_by
    relationship.reason='Teacher accepted institute invitation '+invitation.name
    write(relationship)

@frappe.whitelist(methods=['POST'])
def request_by_email(email):
    from .profiles import required,relate
    p=required()
    if p.kind!='Teacher':frappe.throw('Only verified teachers can request membership',frappe.PermissionError)
    require_mail()
    try:email=email_address(email.strip())
    except ValueError as e:frappe.throw(str(e))
    limit('institute-request:'+frappe.session.user)
    target=frappe.db.get_value('IL Public Profile',{'user':email,'kind':'Institute','status':'Verified'},'name')
    if target:relate(target,'Teacher membership')
    return {'message':'If this email belongs to a verified institute on this site, your request is now in its membership inbox.'}


def dispatch_invitation(invitation):
    """Send only this committed invitation; normal queue retry policy remains active."""
    if not frappe.db.exists('IL Teacher Invitation',invitation):return
    if frappe.db.get_default('suspend_email_queue') in (1,'1') or frappe.are_emails_muted():return
    for name in frappe.get_all('Email Queue',filters={'reference_doctype':'IL Teacher Invitation',
            'reference_name':invitation,'status':['in',['Not Sent','Partially Sent']]},pluck='name'):
        queue=frappe.get_doc('Email Queue',name,for_update=True)
        queue.send()
