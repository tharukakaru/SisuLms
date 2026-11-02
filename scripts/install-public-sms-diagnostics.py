"""Install bounded SMS diagnostics; no SMS requests or limiter changes."""
import ast,hashlib,os,pwd,subprocess
from pathlib import Path
TARGET=Path('/home/sisu/frappe-bench/apps/institute_lms/institute_lms/notify_adapter.py')
OLD='fa98e875992b2461aa24378f2587744b2ea680de07e640f0c92f3114e9de4275'
NEW='"""Notify.lk acceptance adapter; acceptance is not a delivery receipt.\n\nNotify\'s API returns no message ID and has no documented idempotency support.\nThe notification outbox commits Review before calling us and never retries an\nambiguous send automatically.\n"""\nimport re\nimport requests\nimport frappe\n\n\ndef send(phone, message, idempotency_key=None):\n    config = frappe.conf.get(\'il_notify\') or {}\n    return send_config(config,phone,message)\n\n\ndef send_config(config,phone,message):\n    if not all(config.get(k) for k in (\'user_id\', \'api_key\', \'sender_id\')):\n        frappe.throw(\'SMS provider is not configured\')\n    if config[\'sender_id\'].lower() == \'notifydemo\':\n        frappe.throw(\'Configure an approved sender before enabling SMS verification\')\n    number = str(phone).lstrip(\'+\')\n    if not re.fullmatch(r\'94\\d{9}\', number):\n        frappe.throw(\'Notify SMS requires a Sri Lankan phone number\')\n    text = \'SISU: \' + str(message)\n    if len(text) > 621:\n        frappe.throw(\'SMS is too long\')\n    payload = {k:config[k] for k in (\'user_id\',\'api_key\',\'sender_id\')}\n    payload.update(to=number,message=text)\n    if not text.isascii():\n        payload[\'type\'] = \'unicode\'\n    try:\n        response = requests.post(\'https://app.notify.lk/api/v1/send\', data=payload,\n                                 timeout=(5, 15), allow_redirects=False)\n        value = response.json()\n        confirmed = response.ok and isinstance(value,dict) and value.get(\'status\') == \'success\' and value.get(\'data\') == \'Sent\'\n    except (requests.RequestException, ValueError) as exc:\n        try:\n            if getattr(frappe.local,\'site\',None)==\'sisuacademylk.com\':\n                response_value=locals().get(\'response\')\n                frappe.cache.set_value(\'il_public_sms_last_failure\',{\'error_type\':type(exc).__name__,\n                    \'http_status\':getattr(response_value,\'status_code\',None)},expires_in_sec=3600)\n        except Exception:\n            pass\n        frappe.throw(\'SMS acceptance is uncertain; reconcile before retrying\')\n    if not confirmed:\n        frappe.throw(\'SMS provider did not confirm acceptance\')\n    return {\'accepted\':True, \'provider\':\'notify.lk\', \'provider_id\':None}\n'

def main():
 if os.name!='posix' or os.geteuid()!=0:raise RuntimeError('Run as root')
 data=TARGET.read_bytes()
 if hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()!=OLD:raise RuntimeError('Adapter differs from reviewed source')
 ast.parse(NEW)
 backup=Path('/root/sisu-public-provision-isolated/notify-adapter-before-diagnostics.py')
 os.umask(0o077)
 with backup.open('xb') as out:out.write(data)
 TARGET.write_text(NEW);TARGET.chmod(0o644)
 user=pwd.getpwnam('sisu');os.chown(TARGET,user.pw_uid,user.pw_gid)
 subprocess.run(['supervisorctl','restart','frappe-bench-web:frappe-bench-frappe-web'],check=True)
 print('INSTALLED: public-site SMS exception category capture. Web process restarted; no SMS sent or limits cleared.')
if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__));raise SystemExit(1)
