"""Compare Notify dashboard credentials locally; never print values or send requests."""
import getpass,hmac,logging,os,warnings
from pathlib import Path

def matches(saved,entered):
    return hmac.compare_digest(str(saved or '').encode(),entered.encode())

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    logging.disable(logging.CRITICAL)
    warnings.simplefilter('error',getpass.GetPassWarning)
    user=getpass.getpass('Notify dashboard User ID (hidden; Settings > API Keys): ').strip()
    key=getpass.getpass('Notify dashboard API key (hidden): ').strip()
    if not user or not key:raise ValueError('Both fields required')
    import frappe
    os.chdir('/home/sisu/frappe-bench/sites')
    try:
        frappe.init(site='staging.sisuacademylk.com',sites_path='/home/sisu/frappe-bench/sites');frappe.connect()
        config=frappe.conf.get('il_notify') or {}
        if not isinstance(config,dict):raise ValueError('Unexpected saved configuration')
        print('Dashboard User ID matches server: '+str(matches(config.get('user_id'),user)))
        print('Dashboard API key matches server: '+str(matches(config.get('api_key'),key)))
        print('Saved sender matches SisuAcademy: '+str(config.get('sender_id')=='SisuAcademy'))
        print('Comparison only. No credentials displayed or saved; no provider request or SMS sent; test reservation preserved.')
    finally:
        try:frappe.db.rollback()
        except Exception:pass
        frappe.destroy()

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print('CHECK STOPPED ['+type(exc).__name__+']. No credentials printed.');raise SystemExit(1) from None
