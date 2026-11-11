"""One isolated sandbox session probe. No checkout, payment or database writes."""
import os,json,uuid,traceback
from pathlib import Path

def main():
    if Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe,requests
    frappe.init(site='staging.sisuacademylk.com');frappe.connect()
    original=requests.Session.request
    def observed(self,method,url,**kwargs):
        stage='sessions' if '/uc/v1/sessions' in url else 'signing_key' if '/flex/v2/public-keys/' in url else 'other'
        try:
            response=original(self,method,url,**kwargs)
            info={'stage':stage,'http_status':response.status_code,'response_bytes':len(response.content)}
            if response.status_code>=400:
                try:
                    obj=response.json()
                    # Only fixed allowlisted reason codes and field paths, no raw messages.
                    import re
                    reason=obj.get('reason') if isinstance(obj,dict) else None
                    if isinstance(reason,str) and re.fullmatch(r'[A-Z_]{1,80}',reason):info['reason']=reason
                    details=obj.get('details',[]) if isinstance(obj,dict) else []
                    info['invalid_fields']=[d['field'] for d in details if isinstance(d,dict) and isinstance(d.get('field'),str) and re.fullmatch(r'[A-Za-z0-9_.\[\]]{1,120}',d['field'])][:20]
                except (ValueError,TypeError):pass
            print(json.dumps(info));return response
        except requests.RequestException as exc:
            print(json.dumps({'stage':stage,'network_exception':type(exc).__name__}));raise
    try:
        from institute_lms.cybersource import settings
        from institute_lms import cybersource_transport as transport
        from institute_lms.cybersource_contract import session_request
        config=settings('platform')
        if config.get('mode')!='sandbox':raise RuntimeError('Sandbox required')
        requests.Session.request=observed
        payload=session_request('sisu-'+uuid.uuid4().hex,100,'LKR',config['origin'],config['methods'])
        print('PROBE: one new sandbox session, discarded without browser checkout or payment.')
        transport.request(config,'POST','/uc/v1/sessions',payload,token=True)
        print('PASS: session accepted and signature/expiry verified.')
    except Exception as exc:
        print(json.dumps({'exception':type(exc).__name__,'frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-6:]]}))
    finally:
        requests.Session.request=original
        frappe.db.rollback();frappe.destroy()
    print('No credentials or tokens printed. Existing attempt retained; no payment, invoice or settings changed.')
if __name__=='__main__':main()
