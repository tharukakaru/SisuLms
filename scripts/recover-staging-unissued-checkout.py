"""Operator recovery for one sandbox session never saved or delivered to checkout."""
import os,json
from pathlib import Path
ATTEMPT='loiq35ab06'
REFERENCE='sisu-216e9d43c62e48b3ab635b83f2b97e56'

def validate(a):
    expected={'name':ATTEMPT,'reference':REFERENCE,'invoice':'fm34oisjhc','kind':'subscription','customer':'sisu.student.test+hnb@gmail.com','merchant_id':'sisu_academy_1793191054','merchant_scope':'platform','currency':'LKR','amount_minor':100}
    if any(a.get(k)!=v for k,v in expected.items()):raise RuntimeError('Attempt identity mismatch')
    if a.status!='review' or a.active_key!='subscription:fm34oisjhc':raise RuntimeError('Attempt state changed')
    if a.browser_event or a.transaction_id or a.settlement_key or a.session_expires or a.get_password('session_token',raise_exception=False):raise RuntimeError('Session or transaction evidence exists; normal reconciliation required')

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    from frappe.utils import now_datetime,get_datetime
    frappe.init(site='staging.sisuacademylk.com');frappe.connect()
    try:
        from institute_lms.owner_access import primary_email,is_owner
        from institute_lms.cybersource import settings,lock_invoice,save
        from institute_lms.cybersource_transport import request
        from institute_lms.saas import audit
        owner=primary_email()
        if not is_owner(owner):raise RuntimeError('Configured owner unavailable')
        frappe.set_user(owner)
        a=frappe.get_doc('IL CyberSource Attempt',ATTEMPT)
        if a.reference==REFERENCE and a.status=='cancelled' and not a.active_key:
            print('ALREADY CLOSED: refresh staging Subscription.');return
        validate(a)
        age=(now_datetime()-get_datetime(a.creation)).total_seconds()
        if age<3600:raise RuntimeError('Conservative reporting wait: retry after '+str(int(3600-age)+1)+' seconds')
        if age>6*86400:raise RuntimeError('Outside report window; archived reconciliation required')
        config=settings('platform')
        if config.get('mode')!='sandbox' or config.get('merchant_id')!=a.merchant_id:raise RuntimeError('Sandbox merchant mismatch')
        report=request(config,'POST','/tss/v2/searches',{'save':False,'query':'clientReferenceInformation.code:'+REFERENCE,'offset':0,'limit':10,'sort':'submitTimeUtc:desc'})
        if report.get('totalCount')!=0 or report.get('_embedded',{}).get('transactionSummaries'):raise RuntimeError('Zero transactions not confirmed')
        print('PASS: no saved/delivered session evidence; authenticated report has zero transactions.')
        print('Confirm your sandbox Business Center search for: '+REFERENCE)
        if input('Type NO PAYMENT to cancel only this retained test attempt: ').strip()!='NO PAYMENT':
            print('UNCHANGED.');return
        lock_invoice(a.kind,a.invoice)
        a=frappe.get_doc('IL CyberSource Attempt',ATTEMPT,for_update=True);validate(a)
        a.status='cancelled';a.active_key=None;save(a)
        audit('Close unissued sandbox session attempt',a.name,'Operator confirmed empty Business Center result for '+REFERENCE+'; fresh authenticated report empty. No saved session token, expiry, browser event, transaction or settlement. No token was returned by the session-creation failure path.')
        frappe.db.commit()
        print('CLOSED: attempt retained as cancelled. Invoice unchanged. Hard-refresh staging and click Pay online once.')
        print('No checkout, payment, message or gateway configuration change performed.')
    finally:
        frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED:',type(exc).__name__,str(exc) if isinstance(exc,RuntimeError) else 'Recovery not confirmed; no raw details displayed.')
        raise SystemExit(1) from None
