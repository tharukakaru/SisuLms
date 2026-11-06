"""Reproduce the named test student's slip submission; retain no database changes."""
import io
from pathlib import Path
import json
import os
import secrets
import traceback
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch


def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com');frappe.connect()
    stage='test account'
    written=[]
    try:
        from institute_lms import public_student, commercial, account_billing, saas
        from institute_lms.campus_context import SESSION_KEY
        user='sisu.student.test@gmail.com'
        inst=frappe.db.get_value('IL Institute',{'code':'SISUDEMO'},'name')
        student=frappe.db.get_value('IL Member',{'institute':inst,'user':user,'role':'Student','active':1},'name')
        assert student and frappe.db.get_value('User',user,'enabled'), 'Named test student unavailable'
        frappe.set_user(user);frappe.session.data[SESSION_KEY]=inst
        frappe.session.data.csrf_token=secrets.token_hex(32)
        bills=frappe.get_all('IL Invoice',filters={'institute':inst,'student':student,'status':'Unpaid'},fields=['name','classroom','amount'],order_by='creation desc')
        bills=[b for b in bills if frappe.db.get_value('IL Classroom',b.classroom,'programme')]
        assert bills,'No unpaid programme invoice for named student'
        bill=bills[0]
        files=frappe.get_all('File',filters={'owner':user,'is_private':1,'file_name':['like','bank-proof%']},fields=['name','attached_to_doctype','attached_to_name'],order_by='creation desc',limit_page_length=10)
        proof=next((f for f in files if not f.attached_to_name),None)
        print(json.dumps({'invoice':bill.name,'unattached_bank_proof_found':bool(proof)}))
        with ExitStack() as stack:
            stack.enter_context(patch.object(frappe,'sendmail',side_effect=AssertionError('No diagnostic mail')))
            stack.enter_context(patch.object(frappe,'enqueue',return_value=None))
            stack.enter_context(patch.object(frappe,'publish_realtime',return_value=None))
            if not proof:
                stage='upload synthetic private proof'
                from frappe.utils import file_manager
                original_write=file_manager.save_file_on_filesystem
                def tracked_write(*args,**kwargs):
                    result=original_write(*args,**kwargs)
                    url=result.get('file_url','')
                    if url.startswith('/private/files/bank-proof'):
                        written.append(Path(frappe.get_site_path('private','files',url.rsplit('/',1)[-1])).resolve())
                    return result
                stack.enter_context(patch.object(file_manager,'save_file_on_filesystem',side_effect=tracked_write))
                content=('SISU ROLLBACK DIAGNOSTIC - NOT A PAYMENT '+secrets.token_hex(32)).encode()
                request=SimpleNamespace(path='/api/method/institute_lms.public_student.upload_proof',
                    files={'file':SimpleNamespace(filename='diagnostic.txt',stream=io.BytesIO(content))})
                frappe.local.request=request
                frappe.local.form_dict=frappe._dict(invoice=bill.name)
                account_billing.guard_request();saas.guard_request()
                proof=frappe._dict(public_student.upload_proof(bill.name))
                print('PASS: unique private proof upload. Testing submission next.')
            stage='student bridge and submission'
            args={'invoice':bill.name,'proof':proof.name,'reference':'ROLLBACK-DIAGNOSTIC-'+secrets.token_hex(8),'amount':str(bill.amount),'transfer_date':frappe.utils.today()}
            frappe.local.request=SimpleNamespace(path='/api/method/institute_lms.public_student.action')
            frappe.local.form_dict=frappe._dict(module='commercial',method='submit_slip',args=args)
            account_billing.guard_request();saas.guard_request()
            result=public_student.action('commercial','submit_slip',args)
            print('PASS: submission reached '+result['status']+' in rollback transaction; investigate upload if browser still fails.')
    except Exception as exc:
        print(json.dumps({'failed_stage':stage,'exception':type(exc).__name__,'frames':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
    finally:
        frappe.db.rollback()
        private=Path(frappe.get_site_path('private','files')).resolve()
        for path in written:
            if path.parent==private and path.name.startswith('bank-proof') and not frappe.db.exists('File',{'file_url':'/private/files/'+path.name}):
                path.unlink(missing_ok=True)
        frappe.destroy()
        print('ROLLED BACK: no bank-slip, invoice, file attachment or notification changes retained. No payment or message sent.')


if __name__=='__main__':main()
