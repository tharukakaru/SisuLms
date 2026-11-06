"""Rollback regression: same PNG as a foreign-owned classroom attachment."""
import io,json,os,secrets,struct,traceback,zlib
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

def png():
    def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',1,1,8,2,0,0,0))+chunk(b'tEXt',b'Test\0'+secrets.token_hex(24).encode())+chunk(b'IDAT',zlib.compress(b'\0\xff\xff\xff'))+chunk(b'IEND',b'')

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com');frappe.connect()
    paths=set();stage='fixture'
    try:
        from institute_lms import public_student,account_billing,saas
        from institute_lms.campus_context import SESSION_KEY
        student='sisu.student.test@gmail.com';admin='sisu.student.test+institute.admin@gmail.com'
        inst=frappe.db.get_value('IL Institute',{'code':'SISUDEMO'},'name')
        member=frappe.db.get_value('IL Member',{'user':student,'institute':inst,'role':'Student','active':1},'name')
        assert member
        bills=frappe.get_all('IL Invoice',filters={'student':member,'institute':inst,'status':'Unpaid'},fields=['name','classroom','amount'],order_by='creation desc')
        bill=next(b for b in bills if frappe.db.get_value('IL Classroom',b.classroom,'programme'))
        def login(user):
            frappe.set_user(user);frappe.session.data[SESSION_KEY]=inst;frappe.session.data.csrf_token=secrets.token_hex(32)
        content=png()
        with ExitStack() as stack:
            stack.enter_context(patch.object(frappe,'sendmail',side_effect=AssertionError('No mail')))
            stack.enter_context(patch.object(frappe,'enqueue',return_value=None))
            stack.enter_context(patch.object(frappe,'publish_realtime',return_value=None))
            login(admin)
            frappe.local.request=SimpleNamespace(path='/api/method/institute_lms.public_student.upload_proof',files={})
            frappe.local.form_dict=frappe._dict()
            fixture=frappe.get_doc({'doctype':'File','file_name':'sisu-proof-regression.png','content':content,'is_private':1,'attached_to_doctype':'IL Classroom','attached_to_name':bill.classroom}).insert(ignore_permissions=True)
            paths.add(Path(fixture.get_full_path()).resolve())
            login(student)
            stage='identical PNG upload'
            frappe.local.request=SimpleNamespace(path='/api/method/institute_lms.public_student.upload_proof',files={'file':SimpleNamespace(filename='proof.png',stream=io.BytesIO(content))})
            frappe.local.form_dict=frappe._dict(invoice=bill.name)
            account_billing.guard_request();saas.guard_request()
            proof=public_student.upload_proof(bill.name)
            uploaded=frappe.get_doc('File',proof['name']);paths.add(Path(uploaded.get_full_path()).resolve())
            assert uploaded.name!=fixture.name and uploaded.owner==student and uploaded.is_private and not uploaded.attached_to_name
            fixture.reload();assert fixture.owner==admin and fixture.attached_to_doctype=='IL Classroom' and fixture.attached_to_name==bill.classroom
            print('PASS: identical classroom image uploads as a new student-owned private proof; original attachment unchanged.')
            stage='submission'
            frappe.local.request.path='/api/method/institute_lms.public_student.action'
            args={'invoice':bill.name,'proof':uploaded.name,'reference':'ROLLBACK-'+secrets.token_hex(12),'amount':str(bill.amount),'transfer_date':frappe.utils.today()}
            frappe.local.form_dict=frappe._dict(module='commercial',method='submit_slip',args=args)
            account_billing.guard_request();saas.guard_request()
            result=public_student.action('commercial','submit_slip',args)
            assert result['status']=='Pending'
            assert frappe.db.get_value('IL Invoice',bill.name,'status')=='Unpaid'
            print('PASS: proof submitted Pending; invoice remains unpaid.')
    except Exception as exc:
        print(json.dumps({'stage':stage,'exception':type(exc).__name__,'frames':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
        raise SystemExit(1) from None
    finally:
        frappe.db.rollback()
        private=Path(frappe.get_site_path('private','files')).resolve()
        for path in paths:
            if path.parent==private and path.name.startswith(('sisu-proof-regression','bank-proof')) and not frappe.db.exists('File',{'file_url':'/private/files/'+path.name}):path.unlink(missing_ok=True)
        frappe.destroy()
        print('ROLLED BACK: no test file, slip, invoice or notification changes retained. No payment or message sent.')
if __name__=='__main__':main()
