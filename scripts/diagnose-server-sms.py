"""One separately authorized diagnostic SMS; no automatic retry or configuration edits."""
import argparse,getpass,hashlib,json,logging,os,re,stat,warnings
from pathlib import Path
ALLOWED_DIGEST='29addf5f2af53ef591755ec2c573d8d6ee57a78717cd3c92f185995ec1a34a8e'

def sanitize(value,secrets):
    if not isinstance(value,str):return 'not provided as text'
    for secret in sorted((str(s) for s in secrets if s),key=len,reverse=True):
        value=value.replace(secret,'[redacted]')
    value=re.sub(r'https?://[^\s]+','[URL redacted]',value)
    value=re.sub(r'[A-Za-z0-9_./+\-=]{24,}','[identifier redacted]',value)
    value=re.sub(r'\b[0-9]{9,}\b','[number redacted]',value)
    value=re.sub(r'[\x00-\x1f\x7f]',' ',value)
    return value[:300]

def summarize(response,payload,secrets):
    result={'http_status':int(response.status_code)}
    if not isinstance(payload,dict):return dict(result,api_status='non-object or non-JSON response')
    status=payload.get('status')
    result['api_status']=status if status in ('success','error','failed') else 'unrecognized'
    for key in ('message','data'):
        if isinstance(payload.get(key),str):result[key]=sanitize(payload[key],secrets)
    result['accepted']=bool(response.ok and status=='success' and payload.get('data')=='Sent')
    return result

def reserve(path):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:
        json.dump({'state':'Review'},f);f.flush();os.fsync(f.fileno())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--inspect',action='store_true');args=parser.parse_args()
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    os.umask(0o077);logging.disable(logging.CRITICAL);warnings.simplefilter('error',getpass.GetPassWarning)
    folder=Path.home()/'.sisu-secrets/server-sms-tests';folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    for part in (folder,folder.parent):
        st=part.lstat()
        if part.is_symlink() or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)&0o077:raise ValueError('Private storage required')
    marker=folder/'authorized-diagnostic-1.json'
    if marker.exists():
        print('Diagnostic already reserved or attempted. No resend.');return
    if args.inspect:
        print('Diagnostic not yet reserved. No message sent.');return
    phone=re.sub(r'[ ()-]','',getpass.getpass('Same authorized test mobile, 07XXXXXXXX or +947XXXXXXXX (hidden): ').strip())
    if re.fullmatch(r'07[0-9]{8}',phone):phone='+94'+phone[1:]
    if re.fullmatch(r'947[0-9]{8}',phone):phone='+'+phone
    if hashlib.sha256(phone.encode()).hexdigest()!=ALLOWED_DIGEST:raise ValueError('Number does not match authorized recipient')
    import frappe,requests
    os.chdir('/home/sisu/frappe-bench/sites')
    try:
        frappe.init(site='staging.sisuacademylk.com',sites_path='/home/sisu/frappe-bench/sites');frappe.connect()
        cfg=frappe.conf.get('il_notify') or {}
        if not isinstance(cfg,dict) or not all(cfg.get(k) for k in ('user_id','api_key')):raise ValueError('Notify configuration missing')
        payload={k:cfg[k] for k in ('user_id','api_key')}
        payload.update(sender_id='SisuAcademy',to=phone[1:],message='SISU: Authorized server SMS test.')
        reserve(marker)
        response=requests.post('https://app.notify.lk/api/v1/send',data=payload,timeout=(5,20),allow_redirects=False)
        try:body=response.json()
        except ValueError:body=None
        result=summarize(response,body,[cfg['api_key'],cfg['user_id'],phone,phone[1:], '0'+phone[3:]])
        with marker.open('w') as f:
            json.dump({'state':'Accepted' if result.get('accepted') else 'Review','diagnostic':result},f);f.flush();os.fsync(f.fileno())
        print(json.dumps(result))
        print('One diagnostic attempt only. Earlier reservation and saved site configuration unchanged. Acceptance requires phone receipt confirmation.')
    finally:
        try:frappe.db.rollback()
        except Exception:pass
        frappe.destroy()

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print('DIAGNOSTIC STOPPED ['+type(exc).__name__+']. No credentials printed. Do not delete markers or retry an uncertain send.');raise SystemExit(1) from None
