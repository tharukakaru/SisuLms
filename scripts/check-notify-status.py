"""Read-only Notify account-status request; no send endpoint and no credential output."""
import json,logging,os
from decimal import Decimal,InvalidOperation
from pathlib import Path

def summary(http,payload):
    result={'http_status':int(http)}
    if not isinstance(payload,dict):return dict(result,response='unexpected JSON shape')
    result['api_status']=payload.get('status') if payload.get('status') in ('success','error','failed') else 'unrecognized'
    data=payload.get('data')
    if result['api_status']=='success' and isinstance(data,dict):
        active=data.get('active')
        result['account_active']=active if isinstance(active,bool) else 'not reported as boolean'
        value=data.get('acc_balance')
        try:
            if len(str(value))>30:raise ValueError()
            balance=Decimal(str(value))
            if not balance.is_finite():raise ValueError()
            result['account_balance']=str(balance)
        except (ValueError,InvalidOperation):result['account_balance']='not reported as a number'
    else:
        # Only fixed diagnostic labels; never echo provider text that might contain keys.
        text=str(payload.get('message',''))+' '+(data if isinstance(data,str) else '')
        lower=text.lower()
        result['reason_categories']=[label for term,label in (('api key','API key'),('user','user ID'),('auth','authentication'),('ip','IP restriction'),('balance','balance'),('suspend','suspension')) if term in lower]
    return result

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    logging.disable(logging.CRITICAL)
    import frappe,requests
    os.chdir('/home/sisu/frappe-bench/sites')
    try:
        frappe.init(site='staging.sisuacademylk.com',sites_path='/home/sisu/frappe-bench/sites');frappe.connect()
        cfg=frappe.conf.get('il_notify') or {}
        if not isinstance(cfg,dict) or not all(cfg.get(k) for k in ('user_id','api_key')):raise ValueError('Notify fields missing')
        response=requests.get('https://app.notify.lk/api/v1/status',params={k:cfg[k] for k in ('user_id','api_key')},timeout=(5,20),allow_redirects=False)
        try:payload=response.json()
        except ValueError:payload=None
        print(json.dumps(summary(response.status_code,payload)))
        print('No SMS sent; configuration and test reservation unchanged. No request URL, credentials or raw response printed.')
    finally:
        try:frappe.db.rollback()
        except Exception:pass
        frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STATUS CHECK FAILED ['+type(exc).__name__+']. No credentials or request URL printed.');raise SystemExit(1) from None
