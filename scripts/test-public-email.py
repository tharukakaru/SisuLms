"""One explicitly addressed email per target, with durable no-auto-retry markers."""
import argparse,getpass,json,logging,os,stat,warnings
from pathlib import Path
from email.message import EmailMessage
from email.utils import formataddr,make_msgid
BENCH=Path('/home/sisu/frappe-bench')
SITES=('sisuacademylk.com',)
SENDER='noreply@sisuacademylk.com'
stage='startup'

def reserve(path):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as out:
        json.dump({'state':'reserved'},out);out.flush();os.fsync(out.fileno())

def record(path,data):
    with path.open('w') as out:
        json.dump(data,out);out.flush();os.fsync(out.fileno())

def main():
    global stage
    parser=argparse.ArgumentParser();parser.add_argument('--inspect',action='store_true');args=parser.parse_args()
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    os.umask(0o077);logging.disable(logging.CRITICAL);warnings.simplefilter('error',getpass.GetPassWarning)
    directory=Path.home()/'.sisu-secrets/server-email-tests'
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    for p in (directory,directory.parent):
        st=p.lstat()
        if p.is_symlink() or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)&0o077:raise ValueError('Private storage required')
    import frappe
    from frappe.utils import validate_email_address
    recipient=None
    if not args.inspect and any(not (directory/(s+'.json')).exists() for s in SITES):
        recipient=getpass.getpass('Your authorized recipient for ONE public-site test email (hidden): ').strip()
        if any(c in recipient for c in '\r\n,;<>') or recipient.count('@')!=1:raise ValueError('One address required')
        validate_email_address(recipient,throw=True)
    os.chdir(BENCH/'sites')
    for site in SITES:
        stage=site+' connection'
        try:
            frappe.init(site=site,sites_path=str(BENCH/'sites'));frappe.connect();frappe.set_user('Administrator')
            marker=directory/(site+'.json')
            if marker.exists():
                if marker.is_symlink():raise ValueError('Invalid marker')
                state=json.loads(marker.read_text());queue=state.get('queue')
                status=frappe.db.get_value('Email Queue',queue,'status') if queue else 'Reserved; manual review required'
                print(site+': existing test '+str(status)+'; no resend.');continue
            if args.inspect:
                print(site+': no test reserved.');continue
            if not frappe.db.get_default('suspend_email_queue'):raise ValueError('General queue must stay suspended')
            stage=site+' outgoing account validation'
            names=frappe.get_all('Email Account',filters={'enable_outgoing':1,'smtp_server':'smtp-relay.brevo.com','email_id':SENDER},pluck='name')
            if len(names)!=1:raise ValueError('Outgoing account differs')
            account=frappe.get_doc('Email Account',names[0])
            if not account.use_tls or account.use_ssl_for_outgoing or int(account.smtp_port)!=587:raise ValueError('STARTTLS required')
            stage=site+' Frappe SMTP sender probe'
            session=account.get_smtp_server().session
            try:
                code,_=session.mail(SENDER);session.rset()
                print(site+': Frappe SMTP sender response '+str(int(code)))
                if code!=250:raise ValueError('Sender probe failed; no email attempted')
            finally:session.quit()
            stage=site+' test reservation'
            reserve(marker)  # Reserve BEFORE queue creation or sending; uncertain outcomes never retry automatically.
            message=EmailMessage();message['From']=formataddr(('SISU Academy',SENDER));message['To']=recipient
            message['Subject']='SISU deployment email test — '+site
            message['Message-ID']=make_msgid(domain='sisuacademylk.com')
            message.set_content('Authorized delivery test from '+site+'. This does not activate customer emails or account access.')
            queue=frappe.get_doc(dict(doctype='Email Queue',sender=message['From'],email_account=account.name,message=message.as_string(),message_id=message['Message-ID'],status='Not Sent',recipients=[dict(recipient=recipient,status='Not Sent')])).insert(ignore_permissions=True)
            frappe.db.commit();record(marker,{'state':'reserved','queue':queue.name})
            stage=site+' single test send'
            queue.send(force_send=True);frappe.db.commit();queue.reload()
            record(marker,{'state':'attempted','queue':queue.name})
            print(site+': test queue status '+str(queue.status)+'. General queue remains suspended.')
        finally:
            try:frappe.db.rollback()
            except Exception:pass
            frappe.destroy()
    print('Check the recipient inbox for the sisuacademylk.com test email. Sent means SMTP acceptance, not confirmed inbox delivery.')

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print('STOPPED: '+stage+' ['+type(exc).__name__+']. No credentials printed. Use --inspect; do not delete reservation files or blindly resend.');raise SystemExit(1) from None
