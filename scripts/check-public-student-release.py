"""Read-only public release and schema check; no messages or configuration changes."""
import os,json,hashlib
from pathlib import Path
EXPECTED = {'frontend/src/App.vue': '7be575f429b32c840106f2fa5b16bf3e12d52228c197e69ad5a63db3a07210b0', 'frontend/src/native/AccountReceipts.vue': '25630d029a969afcd71e047cc9cf7bd35c2ebf77c55ae9c13287974c7cd4ff95', 'frontend/src/native/BankPayments.vue': '59b025cef3811c6ba72442691e4704b82575f4b778e8866ecf4a613368a856ab', 'frontend/src/native/CyberSourcePayment.vue': '268178c7987021348f7c7236ff94fef607500613c9f7f4dac0575d9527c39164', 'frontend/src/native/LiveRoom.vue': '05dec0113b80ade7886070b0486ba3553eb15fcad232c9857270c7552aa69e35', 'frontend/src/native/ProductWorkspace.vue': 'bb43a1fdd3d3ad2d29c6b68beb979c337d6bdbe071f5b25cc359f710af07f06c', 'frontend/src/native/StudentClassrooms.vue': '9cc4b4193e88c8c7f0278d4894a87b2a4f468f5e798992f2e14c84a1ee747257', 'frontend/src/native/SubscriptionBilling.vue': 'a83e09d5744bdc3f9af7433198c685eda3b899d1b418b53842380aba836cdbbc', 'frontend/src/native/cybersourceCheckout.js': '49631d032317ff069f639f06f73d9080456b11d497623f5886ae15d65cec9085', 'institute_lms/account_confirmations.py': '8907c2c4e53c30382065095b562b6d72d5f24c14353bb3dc2a0bfaef9d6ac22e', 'institute_lms/api.py': '1b30f1c8c08397a2cf25a0cccbb57225882c14ddf11a456ce66b0adbbdf0b82b', 'institute_lms/class_keys.py': '30c6ac1cc16a49f944a93b14ef56303cecbc641c28074bfc52464ab903147ecb', 'institute_lms/commercial.py': '98f63683bee8ded99101f6842509fd05f6eb5ca3350ebddf5719aeed87f3507e', 'institute_lms/learning_spaces.py': '2795ca023786680aed4b657ca9afe25d190ed27af251ff988a48e4b53fe4eca6', 'institute_lms/live_classes.py': '301eeb26307afb943ace2b52edc6c294c726ca36af8e28cf16b2d8a836bed920', 'institute_lms/registration.py': '9af446f5a4f2c6f3537a0a85229a4b28603e1724fb2a7e13c4132b093148f498', 'institute_lms/institute_lms/doctype/il_paid_access/il_paid_access.json': '7e69527e643ff21e7f4ee8018fb83a20e31b454ecacd0bfc92950382c945916b'}
BENCH=Path('/home/sisu/frappe-bench')
def main():
    app=BENCH/'apps/institute_lms'
    mismatch=[]
    for name,expected in EXPECTED.items():
        p=app/name
        actual=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() if p.exists() else None
        if actual!=expected:mismatch.append(name)
    if mismatch:raise RuntimeError('Source mismatch: '+', '.join(mismatch))
    print('PASS: all '+str(len(EXPECTED))+' consolidated source files match.')
    import frappe
    os.chdir(BENCH/'sites')
    frappe.init(site='sisuacademylk.com',sites_path=str(BENCH/'sites'));frappe.connect()
    try:
        meta=frappe.get_meta('IL Paid Access',cached=False)
        if 'Awaiting key' not in meta.get_field('status').options.splitlines() or not frappe.db.has_column('IL Paid Access','enrollment_key_hash'):
            raise RuntimeError('Public paid-access schema is not ready; run the targeted schema repair.')
        print('PASS: public paid-access status and enrollment-key storage.')
        gateway=frappe.conf.get('il_cybersource') or {}
        if gateway.get('enabled'):raise RuntimeError('Public online gateway is enabled unexpectedly; review settings.')
        print('PASS: public Cybersource remains disabled.')
        from institute_lms.live_provider import settings
        try:
            settings();print('PASS: public LiveKit settings/library available; real public media not tested here.')
        except Exception:print('PENDING: public LiveKit configuration requires review; staging success does not establish public connectivity.')
        print('READ ONLY: no payments, accounts, access, settings or messages changed. Public browser acceptance and SMS delivery remain separate.')
    finally:frappe.destroy()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__))
        raise SystemExit(1) from None
