"""Explicit owner controls for student-count policy and same-Bench campus receipts.

Campus names come only from the operator's reporting allowlist. SQL targets and
fields are fixed; no caller-supplied database, paths, identifiers or statuses.
"""
import hashlib
import json
from pathlib import Path
import frappe
from frappe.utils import now_datetime
from .student_count import SETTINGS, policy, save
from .student_count_rules import month_bounds, rate_minor


def authorize():
    from .platform import owner
    from .owner_access import require_manager
    owner();require_manager()


def source(site):
    authorize()
    from .owner_operations import sources,connect
    if site not in sources():
        frappe.throw('Campus is not enabled for student-count administration.',frappe.PermissionError)
    return connect(site)


@frappe.whitelist(methods=['GET'])
def settings():
    authorize()
    from .owner_operations import sources
    return dict(**policy(),sites=sources(),current_month=now_datetime().strftime('%Y-%m'))


@frappe.whitelist(methods=['POST'])
def configure(unit_lkr,month,enabled,bank,revision,reason):
    authorize()
    from .plan_catalog_source import require_source_writer
    require_source_writer()
    start,_=month_bounds(month)
    current=now_datetime().strftime('%Y-%m')
    if month<current:
        frappe.throw('Rates cannot be changed for a completed month.')
    if not isinstance(reason,str) or not 10<=len(reason.strip())<=1000:
        frappe.throw('Explain this change in at least 10 characters.')
    bank=json.loads(bank) if isinstance(bank,str) else bank
    if not isinstance(bank,dict):frappe.throw('Enter receiving bank details.')
    clean={k:str(bank.get(k,'')).strip() for k in ('bank_name','account_name','account_number','branch')}
    if any(len(v)>140 for v in clean.values()):frappe.throw('Each bank detail must be at most 140 characters.')
    try:minor=rate_minor(unit_lkr)
    except ValueError as exc:frappe.throw(str(exc))
    frappe.db.sql('SELECT name FROM `tabDocType` WHERE name=%s FOR UPDATE',(SETTINGS,))
    before=policy()
    if int(revision)!=before['revision']:frappe.throw('Settings changed. Refresh before saving.')
    existing=[r for r in before['rates'] if r['month']<=current]
    if existing and month==current:
        active=max(existing,key=lambda r:r['month'])
        if active['unit_minor']!=minor or bool(active['enabled'])!=bool(int(enabled)):
            frappe.throw('This month’s rate is fixed. Schedule rate changes for next month.')
    rates=[r for r in before['rates'] if r['month']!=month]+[dict(month=month,unit_minor=minor,enabled=bool(int(enabled)))]
    doc=frappe.get_doc(SETTINGS,'current') if before['revision'] else frappe.get_doc(dict(doctype=SETTINGS,name='current'))
    doc.payload=json.dumps(dict(rates=sorted(rates,key=lambda r:r['month']),bank=clean));doc.revision=before['revision']+1
    save(doc)
    from .saas import audit
    audit('Student count policy',str(doc.revision),reason.strip())
    return {'saved':True,'revision':doc.revision}


@frappe.whitelist(methods=['GET'])
def bills(site,month='',status='',page=0):
    if month:month_bounds(month)
    if status not in ('','Unpaid','Pending','Paid','Rejected'):frappe.throw('Invalid payment status.')
    page=max(0,min(int(page),10000))
    connection=source(site)
    try:
        with connection.cursor() as c:
            c.execute('START TRANSACTION READ ONLY')
            c.execute('''SELECT name,provider_name,provider_role,month,quantity,unit_minor,amount_minor,
                status,reference,submitted_at,review_note,reviewed_by,paid_at,modified,proof_file
                FROM `tabIL Student Count Bill` WHERE (%s='' OR month=%s) AND (%s='' OR status=%s)
                ORDER BY month DESC,creation DESC LIMIT 51 OFFSET %s''',(month,month,status,status,page*50))
            rows=c.fetchall()
        return dict(rows=rows[:50],has_next=len(rows)>50)
    finally:connection.close()


@frappe.whitelist(methods=['POST'])
def review(site,invoice,decision,note,modified):
    if decision not in ('Paid','Rejected'):frappe.throw('Choose approve or reject.')
    if not isinstance(note,str) or not 10<=len(note.strip())<=1000:
        frappe.throw('Enter a bank confirmation or rejection reason (at least 10 characters).')
    connection=source(site)
    try:
        with connection.cursor() as c:
            c.execute('SELECT * FROM `tabIL Student Count Bill` WHERE name=%s FOR UPDATE',(invoice,))
            doc=c.fetchone()
            if not doc or doc['status']!='Pending' or not doc['proof_file'] or str(doc['modified'])!=str(modified):
                frappe.throw('This submission changed or is not pending. Refresh before reviewing.')
            payment_key=hashlib.sha256(('student-count-bank:'+doc['reference'].strip().casefold()).encode()).hexdigest() if decision=='Paid' else None
            if payment_key:
                c.execute('SELECT name FROM `tabIL Student Count Bill` WHERE payment_key=%s',(payment_key,))
                if c.fetchone():frappe.throw('This transfer reference has already been approved.')
            now=now_datetime()
            c.execute('''UPDATE `tabIL Student Count Bill` SET status=%s,review_note=%s,reviewed_by=%s,
                reviewed_at=%s,paid_at=%s,payment_key=%s,modified=%s,modified_by=%s WHERE name=%s''',
                (decision,note.strip(),frappe.session.user,now,now if decision=='Paid' else None,payment_key,now,frappe.session.user,invoice))
        connection.commit()
    except Exception:
        connection.rollback();raise
    finally:connection.close()
    from .saas import audit
    audit('Student count payment '+decision,site+':'+invoice,note.strip())
    return {'status':decision}


@frappe.whitelist(methods=['GET'])
def proof(site,invoice):
    connection=source(site)
    try:
        with connection.cursor() as c:
            c.execute('START TRANSACTION READ ONLY')
            c.execute('''SELECT f.file_url,f.file_name FROM `tabIL Student Count Bill` b JOIN `tabFile` f
                ON f.name=b.proof_file AND f.is_private=1 AND f.attached_to_doctype='IL Student Count Bill'
                AND f.attached_to_name=b.name WHERE b.name=%s''',(invoice,))
            row=c.fetchone()
    finally:connection.close()
    if not row or not row['file_url'].startswith('/private/files/'):
        frappe.throw('Private receipt is unavailable on this Bench.')
    root=Path(frappe.get_site_path()).resolve().parent/site/'private'/'files'
    path=(root/row['file_url'].removeprefix('/private/files/')).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size>5*1024*1024:
        frappe.throw('Private receipt is unavailable.')
    frappe.local.response.update(type='download',filename=row['file_name'],filecontent=path.read_bytes(),display_content_as='attachment')
    frappe.local.response_headers.update({'Cache-Control':'no-store, private'})
