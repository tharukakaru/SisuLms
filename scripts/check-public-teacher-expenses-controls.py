"""Exercise named public teacher workflows inside a rolled-back transaction."""
import os, json, secrets, traceback
from pathlib import Path
from types import SimpleNamespace

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com');frappe.connect()
    stage='test identity'
    try:
        from institute_lms import workspace, accounts, account_billing, saas
        from institute_lms.campus_context import SESSION_KEY
        frappe.set_user('sisu.student.test+teacher@gmail.com')
        inst=frappe.db.get_value('IL Institute',{'code':'SISUTESTTC'},'name')
        if not inst:raise RuntimeError('Named test workspace missing')
        frappe.session.data[SESSION_KEY]=inst
        frappe.session.data.csrf_token=secrets.token_hex(32)
        def check(module,method,**args):
            frappe.local.request=SimpleNamespace(path='/api/method/institute_lms.'+module+'.'+method)
            frappe.local.form_dict=frappe._dict(args)
            account_billing.guard_request();saas.guard_request()
            return getattr({'workspace':workspace,'accounts':accounts}[module],method)(**args)
        day=workspace.business_today().isoformat()
        stage='save expense'
        data=dict(date=day,amount='12.34',category='Teaching',note='[TEST] Rollback-only expense verification',token=secrets.token_hex(16))
        saved=check('workspace','add_expense',data=data)
        assert saved['amount_minor']==1234
        assert check('workspace','add_expense',data=data)['name']==saved['name']
        stage='expense date filters'
        rows=check('workspace','expenses',start=day,end=day)['rows']
        assert any(r['name']==saved['name'] for r in rows)
        assert not any(r['name']==saved['name'] for r in check('workspace','expenses',start='2000-01-01',end='2000-01-01')['rows'])
        print('PASS: save, duplicate-submission protection and inclusive expense date filters.')
        stage='student removal'
        room=frappe.get_doc('IL Classroom','63e7016j4h')
        assert room.institute==inst and room.owner_user==frappe.session.user and room.title.startswith('[TEST]')
        member=frappe.db.get_value('IL Member',{'institute':inst,'user':'sisu.student.test@gmail.com','role':'Student'},'name')
        enrollment=frappe.db.get_value('IL Enrollment',{'classroom':room.name,'student':member,'active':1},'name') if member else None
        if not enrollment:
            print('NOT TESTED: named test student has no active enrollment in the labelled bank practice class.')
        else:
            assert any(r.name==enrollment for r in check('accounts','account_controls')['enrollments'])
            result=check('accounts','account_action',data=dict(kind='remove_student',target=enrollment,confirmation='CONFIRM',reason='[TEST] Rollback-only student removal verification'))
            assert result['removed'] is True
            updated=frappe.get_doc('IL Enrollment',enrollment)
            assert not updated.active and updated.access_override=='Closed'
            assert not any(r.name==enrollment for r in check('accounts','account_controls')['enrollments'])
            print('PASS: teacher removal closes access and removes the student from the active roster.')
    except Exception as exc:
        print(json.dumps({'failed_stage':stage,'exception':type(exc).__name__,'frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-8:]]}))
        raise SystemExit(1) from None
    finally:
        frappe.db.rollback();frappe.destroy()
        print('ROLLED BACK: no expense, student removal, audit or calendar-job change retained. No payment or message sent. Browser acceptance remains separate.')
if __name__=='__main__':main()
