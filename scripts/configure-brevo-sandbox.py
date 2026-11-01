"""Sandbox-only SMTP setup and one explicitly addressed test; no queue flush."""
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
import getpass
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import smtplib
import ssl
import subprocess
import sys
import inspect
import tempfile
import warnings

SITE = 'hnb-checkout.localhost'
HOST = 'smtp-relay.brevo.com'
USERNAME = 'be4def001@smtp-brevo.com'
SENDER = 'noreply@sisuacademylk.com'
ACCOUNT = 'SISU Academy'
stage = 'sandbox checks'


def recipient(value):
    value = value.strip()
    if len(value) > 254 or not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', value):
        raise ValueError('Expected exactly one email address.')
    return value


def probe(secret):
    with smtplib.SMTP(HOST, 587, timeout=30) as smtp:
        smtp.ehlo()
        if not smtp.has_extn('starttls'):
            raise ValueError('STARTTLS unavailable')
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(USERNAME, secret)


def sender_probe(secret):
    """Check envelope acceptance only: never issue RCPT TO or DATA."""
    with smtplib.SMTP(HOST,587,timeout=30) as smtp:
        smtp.ehlo()
        if not smtp.has_extn('starttls'): raise ValueError('STARTTLS unavailable')
        smtp.starttls(context=ssl.create_default_context()); smtp.ehlo()
        smtp.login(USERNAME,secret)
        code, response = smtp.mail(SENDER)
        print('SMTP MAIL FROM response code:', int(code))
        text = response.decode('utf-8','replace').lower() if isinstance(response,bytes) else ''
        # Fixed diagnostic labels only; never print server response contents.
        labels = [('not activated','transactional account not activated'),
                  ('not active','transactional account not active'),
                  ('suspend','account suspended'),('blocked','account or sender blocked'),
                  ('verify','sender/domain verification mentioned'),
                  ('verified','sender/domain verification mentioned'),
                  ('validat','account or sender validation mentioned'),
                  ('quota','sending quota mentioned'),('credit','sending credits mentioned'),
                  ('authenticat','authentication mentioned')]
        print('Sender check:', 'accepted (no email sent)' if code == 250 else
              next((label for needle,label in labels if needle in text),'rejected; inspect Brevo account/sender status'))
        smtp.rset()


def reply_to_field(meta):
    fields = [f.fieldname for f in meta.fields if f.fieldtype == 'Data' and f.options == 'Email']
    if len(fields) == 1:
        return fields[0]
    # Frappe 17's Reply To Address uses plain Data fields _name and email.
    # Never guess the first Data field: _name is the display name, not an address.
    if not fields and any(f.fieldname == 'email' and f.fieldtype == 'Data' for f in meta.fields):
        return 'email'
    raise ValueError('Reply-To child schema requires review')


def repair_and_retry(frappe, bench):
    global stage
    stage = 'validate narrowly scoped SMTP repair'
    if not frappe.conf.get('pause_scheduler') or not frappe.db.get_default('suspend_email_queue'):
        raise ValueError('General email delivery must remain suspended')
    from frappe.email.smtp import SMTPServer
    if 'smtp_no_ehlo_after_auth' not in inspect.getsource(SMTPServer):
        print('STOP: this Frappe version lacks the SMTP compatibility option; no change made.')
        return
    directory = Path.home()/'.sisu-secrets/brevo-sandbox'
    marker = directory/'single-test.json'
    state = json.loads(marker.read_text())
    if state.get('repair_retry_reserved'):
        print('Repair retry already attempted. No further email sent.')
        print('Existing queue status:',frappe.db.get_value('Email Queue',state['queue'],'status'))
        return
    queue = frappe.get_doc('Email Queue',state['queue'])
    failure = queue.get('error') or ''
    if (queue.email_account != ACCOUNT or queue.status != 'Not Sent' or len(queue.recipients) != 1
            or any(r.status != 'Not Sent' for r in queue.recipients)
            or not re.search(r'SMTPSenderRefused:\s*\(502',failure) or 'authenticat' not in failure.lower()
            or hashlib.sha256(queue.recipients[0].recipient.encode()).hexdigest() != state['recipient_hash']):
        raise ValueError('Only the original test rejected before DATA is eligible')
    doc = frappe.get_doc('Email Account',ACCOUNT)
    if doc.smtp_server != HOST or doc.email_id != SENDER or doc.login_id != USERNAME or not doc.use_tls:
        raise ValueError('Saved SMTP account differs')
    stage = 'test Frappe without post-authentication EHLO'
    old = frappe.conf.get('smtp_no_ehlo_after_auth')
    frappe.conf.smtp_no_ehlo_after_auth = 1
    server = doc.get_smtp_server()
    try:
        code, _ = server.session.mail(queue.sender)
        server.session.rset()
        print('Frappe sender check without post-AUTH EHLO:',int(code))
        if code != 250: raise ValueError('Compatibility change did not fix acceptance')
    finally:
        server.quit()
        frappe.conf.smtp_no_ehlo_after_auth = old
    stage = 'save sandbox-only SMTP compatibility setting'
    config_path = bench/'sites'/SITE/'site_config.json'
    raw = config_path.read_bytes(); config = json.loads(raw)
    backup = directory/('pre-smtp-compat-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    with backup.open('xb') as output: output.write(raw)
    config['smtp_no_ehlo_after_auth'] = 1
    fd, temporary = tempfile.mkstemp(dir=config_path.parent,prefix='.brevo-compat-')
    with os.fdopen(fd,'w') as output:
        json.dump(config,output,indent=2);output.flush();os.fsync(output.fileno())
    if config_path.read_bytes()!=raw:
        os.unlink(temporary);raise ValueError('Configuration changed concurrently')
    os.replace(temporary,config_path)
    frappe.conf.smtp_no_ehlo_after_auth = 1
    # Persist before I/O; never auto-repeat this retry after a crash or ambiguous result.
    state['repair_retry_reserved'] = True
    marker.write_text(json.dumps(state))
    stage = 'retry only original pre-DATA-rejected email'
    queue.send(force_send=True)
    frappe.db.commit();queue.reload()
    print('Authorized test queue status:',queue.status)
    print('Sandbox SMTP compatibility setting saved. No general queue flush performed.')
    print('Check your inbox and Brevo Transactional Logs. Sent means SMTP acceptance, not inbox delivery.')


def main():
    global stage
    warnings.simplefilter('error', getpass.GetPassWarning)
    logging.disable(logging.CRITICAL)
    os.umask(0o077)
    bench = Path.home() / 'sisu-hnb-sandbox-bench'
    if os.name != 'posix' or Path.cwd().resolve() != bench.resolve():
        raise ValueError('Dedicated Ubuntu sandbox required')
    import frappe
    os.chdir(bench / 'sites')
    stage = 'sandbox database connection'
    frappe.init(site=SITE, sites_path=str(bench / 'sites'))
    frappe.connect(); frappe.set_user('Administrator')
    try:
        stage = 'inspect existing email setup'
        accounts = frappe.get_all('Email Account', fields=['name','enable_outgoing','default_outgoing','smtp_server'])
        print('Existing Email Accounts:', len(accounts))
        print('Pending Email Queue records:', frappe.db.count('Email Queue', {'status':['in',['Not Sent','Partially Sent','Sending','Error']]}))
        print('Registration enabled:', bool(frappe.conf.get('il_registration_enabled')))
        print('Scheduler paused:', bool(frappe.conf.get('pause_scheduler')))
        if '--repair-and-retry' in sys.argv:
            repair_and_retry(frappe,bench)
            return
        if '--diagnose-sender' in sys.argv:
            stage = 'read saved test queue'
            queue_doc = None
            marker = Path.home()/'.sisu-secrets/brevo-sandbox/single-test.json'
            if marker.exists():
                queue = json.loads(marker.read_text()).get('queue')
                if queue:
                    print('Authorized test queue status:', frappe.db.get_value('Email Queue',queue,'status'))
                    queue_doc = frappe.get_doc('Email Queue',queue)
                    saved_error = queue_doc.get('error') or ''
                    match = re.search(r'SMTPSenderRefused:\s*\((\d{3})', saved_error)
                    print('Saved sender rejection code:', match.group(1) if match else 'not recorded')
                    print('Saved error mentions authentication:', 'authenticat' in saved_error.lower())
                    print('Saved error mentions sender verification:', any(x in saved_error.lower() for x in ('not verified','unverified','sender invalid','sender is invalid')))
            stage = 'probe saved SMTP sender without sending'
            doc = frappe.get_doc('Email Account',ACCOUNT)
            if doc.smtp_server != HOST or doc.email_id != SENDER or doc.login_id != USERNAME:
                raise ValueError('Saved SMTP account differs')
            sender_probe(doc.get_password('password'))
            stage = 'probe Frappe SMTP transport without sending'
            server = doc.get_smtp_server()
            session = server.session
            try:
                print('Frappe STARTTLS configured:', bool(doc.use_tls))
                code, _ = session.mail(queue_doc.sender if queue_doc else SENDER)
                print('Frappe SMTP MAIL FROM response code:', int(code))
                session.rset()
            finally:
                session.quit()
            print('No recipients contacted, no email sent, no queue/configuration changes.')
            return
        if '--inspect' in sys.argv:
            meta = frappe.get_meta('Email Account')
            expected = ('email_account_name','email_id','enable_incoming','enable_outgoing',
                'default_outgoing','auth_method','login_id_is_different','login_id',
                'smtp_server','smtp_port','use_tls','use_ssl_for_outgoing',
                'no_smtp_authentication','always_use_account_email_id_as_sender',
                'always_use_account_name_as_sender_name','awaiting_password','password')
            missing = [key for key in expected if not meta.has_field(key)]
            print('Missing expected Email Account fields:', ', '.join(missing) or 'none')
            print('Reply-To switch available:', bool(meta.has_field('add_reply_to_header')))
            field = meta.get_field('reply_to_addresses')
            print('Reply-To table available:', bool(field))
            if field and field.options:
                child = frappe.get_meta(field.options)
                for item in child.fields:
                    if item.fieldtype in ('Data','Small Text','Text','Link'):
                        print('Reply-To schema field:', item.fieldname, '| type:', item.fieldtype,
                              '| Email option:', item.options == 'Email')
            return
        if not frappe.conf.get('pause_scheduler'):
            raise ValueError('Sandbox scheduler must remain paused')
        if any(a.enable_outgoing and a.name != ACCOUNT for a in accounts):
            print('STOP: another outgoing account exists; review it before selecting a new default.')
            return
        if frappe.db.exists('Email Account', ACCOUNT):
            existing = frappe.get_doc('Email Account', ACCOUNT)
            if existing.email_id != SENDER or existing.smtp_server != HOST or existing.enable_incoming:
                print('STOP: existing account differs; no overwrite performed.')
                return
        directory = Path.home()/'.sisu-secrets/brevo-sandbox'
        for folder in (directory.parent, directory):
            if folder.is_symlink(): raise ValueError('Unsafe private directory')
            folder.mkdir(mode=0o700, exist_ok=True)
            if folder.stat().st_uid != os.getuid(): raise ValueError('Private directory owner mismatch')
            os.chmod(folder,0o700)
        marker = directory/'single-test.json'
        if marker.exists():
            state = json.loads(marker.read_text())
            queue = state.get('queue')
            print('Existing authorized test status:', frappe.db.get_value('Email Queue',queue,'status') if queue else 'attempt reserved')
            print('No second email sent. Check the existing test in Brevo and the recipient inbox.')
            return
        stage = 'hidden input'
        secret = getpass.getpass('Existing Brevo SMTP key (hidden; NOT an API key): ').strip()
        to = recipient(getpass.getpass('One authorized test recipient email (hidden): '))
        reply_verified = getpass.getpass('Have you personally confirmed info@sisuacademylk.com receives mail? Type yes or no (hidden): ').strip().lower() == 'yes'
        if not secret: raise ValueError('SMTP key required')
        stage = 'SMTP connectivity, certificate-verified STARTTLS and authentication'
        probe(secret)
        print('PASS: SMTP connection, STARTTLS certificate verification and authentication.')
        stage = 'private backup'
        backup = directory/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup.mkdir(mode=0o700)
        subprocess.run(['bench','--site',SITE,'backup','--backup-path',str(backup)],cwd=bench,check=True)
        stage = 'configure Frappe outgoing account'
        values = dict(email_account_name=ACCOUNT,email_id=SENDER,enable_incoming=0,enable_outgoing=1,
            default_outgoing=1,auth_method='Basic',login_id_is_different=1,login_id=USERNAME,
            smtp_server=HOST,smtp_port='587',use_tls=1,use_ssl_for_outgoing=0,
            no_smtp_authentication=0,always_use_account_email_id_as_sender=1,
            always_use_account_name_as_sender_name=1,awaiting_password=0)
        meta = frappe.get_meta('Email Account')
        missing = [key for key in values if not meta.has_field(key)]
        if missing:
            print('Missing required Email Account fields:', ', '.join(missing))
            raise ValueError('Installed Email Account schema differs')
        doc = frappe.get_doc('Email Account',ACCOUNT) if frappe.db.exists('Email Account',ACCOUNT) else frappe.new_doc('Email Account')
        doc.update(values); doc.password = secret
        if reply_verified:
            stage = 'configure confirmed Reply-To mailbox'
            field = meta.get_field('reply_to_addresses')
            if not field or not meta.has_field('add_reply_to_header'):
                raise ValueError('Reply-To schema requires review')
            child_meta = frappe.get_meta(field.options)
            email_field = reply_to_field(child_meta)
            doc.add_reply_to_header = 1
            doc.set('reply_to_addresses', [{email_field:'info@sisuacademylk.com'}])
        # The existing Password field encrypts the SMTP key using the site key.
        stage = 'save outgoing Email Account'
        doc.save(ignore_permissions=True)
        frappe.db.set_default('suspend_email_queue',1)
        frappe.db.commit()
        print('PASS: Brevo outgoing account saved; general Email Queue remains suspended.')
        stage = 'create one test Email Queue record'
        message = EmailMessage()
        message['From'] = formataddr(('SISU Academy',SENDER)); message['To'] = to
        message['Subject'] = 'SISU sandbox SMTP verification'
        message['Message-ID'] = make_msgid(domain='sisuacademylk.com')
        if reply_verified: message['Reply-To'] = 'info@sisuacademylk.com'
        message.set_content('This is the single authorized SISU LMS sandbox email test. No customer campaign or production service was enabled.')
        queue = frappe.get_doc(dict(doctype='Email Queue',sender=formataddr(('SISU Academy',SENDER)),
            email_account=doc.name,message=message.as_string(),message_id=message['Message-ID'],
            status='Not Sent',recipients=[dict(recipient=to,status='Not Sent')])).insert(ignore_permissions=True)
        frappe.db.commit()
        # Reserve before sending. An interrupted/uncertain send must not resend on rerun.
        with os.fdopen(os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as output:
            json.dump({'queue':queue.name,'recipient_hash':hashlib.sha256(to.encode()).hexdigest()},output)
        stage = 'send the single authorized queued email'
        queue.send(force_send=True)
        frappe.db.commit(); queue.reload()
        print('Email Queue test record:',queue.name)
        print('Email Queue status:',queue.status)
        print('Reply-To included in test:',reply_verified)
        print('SMTP acceptance is not inbox delivery. Check Brevo Transactional > Logs and your inbox/spam.')
        print('No general queue flush, signup-policy change, production change or automatic retry performed.')
    finally:
        frappe.destroy()
        os.chdir(bench)


if __name__ == '__main__':
    try:
        main()
    except (Exception,KeyboardInterrupt) as error:
        allowed={'SMTPAuthenticationError','SMTPConnectError','SMTPRecipientsRefused','SMTPSenderRefused','SMTPDataError','SSLCertVerificationError','TimeoutError','ConnectionRefusedError','PermissionError','FileNotFoundError','ValueError','ValidationError','CalledProcessError'}
        kind=type(error).__name__
        print('CHECK FAILED:',stage,'['+(kind if kind in allowed else 'other error')+']')
        print('No credentials or exception contents printed. Do not blindly resend; inspect the test queue first.')
        raise SystemExit(1) from None
