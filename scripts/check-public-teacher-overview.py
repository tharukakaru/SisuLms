"""Read-only checks for the named public test teacher; no persistent session changes."""
import os
import json
import secrets
import traceback
from pathlib import Path
from types import SimpleNamespace

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com'); frappe.connect()
    try:
        frappe.set_user('sisu.student.test+teacher@gmail.com')
        from institute_lms import api, teaching, commercial, account_billing, saas
        from institute_lms.campus_context import SESSION_KEY
        workspace=frappe.db.get_value('IL Institute',{'code':'SISUTESTTC'},'name')
        if not workspace: raise RuntimeError('Expected test workspace missing')
        print('PASS: test workspace resolved by institute code.')
        member=frappe.db.get_value('IL Member',{'user':frappe.session.user,'institute':workspace,'role':'Teacher','active':1},'name')
        if not member: raise RuntimeError('Expected test teacher membership missing')
        frappe.session.data[SESSION_KEY]=workspace
        # CLI checks have no HTTP Session object. Bootstrap only reads the CSRF
        # value here; keep a fresh value in memory so it need not persist one.
        frappe.session.data.csrf_token=secrets.token_hex(32)
        print('PASS: active test teacher membership found.')
        for module,name,run in [('api','bootstrap',api.bootstrap),('teaching','overview',teaching.overview),('commercial','metrics',commercial.metrics)]:
            frappe.local.request=SimpleNamespace(path='/api/method/institute_lms.'+module+'.'+name)
            frappe.local.form_dict=frappe._dict()
            print('CHECKING: '+module+'.'+name)
            account_billing.guard_request()
            print('PASS: account billing guard.')
            saas.guard_request()
            print('PASS: workspace guard.')
            data=run()
            if name=='bootstrap':
                assert data['member']['role']=='Teacher'
                assert data['member']['institute_teacher'] is False
            if name=='overview':
                assert all(frappe.db.get_value('IL Classroom',r['name'],'institute')==workspace for r in data['classrooms'])
            print('PASS: public independent teacher '+name+' through both request guards.')
        print('READ ONLY: rolled back; no settings, payments, accounts, memberships or messages changed.')
        print('NOT TESTED: institute-teacher browser session or online checkout.')
    finally:
        frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'failure_frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-8:]]}))
        print('STOPPED:',type(exc).__name__,'during teacher overview verification; private details withheld.')
        raise SystemExit(1) from None
