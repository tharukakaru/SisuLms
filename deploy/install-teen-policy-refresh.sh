#!/bin/bash
set -euo pipefail
if [ "$(id -u)" != 0 ]; then echo 'Run this installer as root.'; exit 1; fi
test -x /home/sisu/frappe-bench/env/bin/python
test -f /home/sisu/frappe-bench/sites/platform.sisuacademylk.com/site_config.json
test -f /home/sisu/frappe-bench/sites/teen.sisuacademylk.com/site_config.json

tmp=$(mktemp -d)
trap 'rm -f "$tmp/refresh.py" "$tmp/service" "$tmp/timer"; rmdir "$tmp"' EXIT
cat > "$tmp/refresh.py" <<'PY'
"""Operator delivery: refresh signed policy, never extend trial or mark payment."""
import json
import sys
import frappe
import requests

TENANT = 'org-b88f135d14e04c99a493c851841ff22a'
HOST = 'teen.sisuacademylk.com'

def main():
    signed = None
    try:
        frappe.init(site='platform.sisuacademylk.com', sites_path='.')
        frappe.connect()
        if not frappe.conf.get('il_control_plane'):
            raise RuntimeError('Wrong site role')
        frappe.set_user('Administrator')
        org = frappe.get_doc('IL Organization', TENANT)
        if org.site_hostname != HOST or org.admin_contact != 'hello@teenacademy.lk':
            raise RuntimeError('Unexpected tenant binding')
        from institute_lms.platform import signed_policy
        signed = signed_policy(TENANT)
        frappe.db.commit()
    finally:
        frappe.destroy()

    expected = json.loads(signed['payload'])['revision']
    with requests.Session() as session:
        session.trust_env = False
        response = session.post(
            'https://' + HOST + '/api/method/institute_lms.saas.apply_manifest',
            json=signed, timeout=(10, 60), allow_redirects=False,
        )
        if response.status_code != 200:
            print('Policy delivery failed: HTTP', response.status_code)
            return 1
        result = response.json().get('message', {})
        if result.get('applied') is not True or result.get('revision') != expected:
            print('Policy delivery failed: unexpected acknowledgement')
            return 1
    print('Teen policy refreshed; revision', expected, '; trial dates unchanged.')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        # Do not log request bodies, signatures, credentials or provider responses.
        print('Policy refresh failed:', type(error).__name__)
        sys.exit(1)
PY

cat > "$tmp/service" <<'UNIT'
[Unit]
Description=Refresh signed SISU policy for Teen Academy
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=sisu
Group=sisu
WorkingDirectory=/home/sisu/frappe-bench/sites
ExecStart=/home/sisu/frappe-bench/env/bin/python /opt/sisu-tools/teen-policy-refresh.py
TimeoutStartSec=180
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
UNIT

cat > "$tmp/timer" <<'UNIT'
[Unit]
Description=Refresh Teen Academy policy hourly before its 24-hour lease expires

[Timer]
OnBootSec=5min
OnCalendar=hourly
RandomizedDelaySec=120
Persistent=true
Unit=sisu-teen-policy-refresh.service

[Install]
WantedBy=timers.target
UNIT

check_target() {
    if [ -e "$2" ] && ! cmp -s "$1" "$2"; then
        echo "STOP: Existing file differs: $2"
        exit 1
    fi
}
check_target "$tmp/refresh.py" /opt/sisu-tools/teen-policy-refresh.py
check_target "$tmp/service" /etc/systemd/system/sisu-teen-policy-refresh.service
check_target "$tmp/timer" /etc/systemd/system/sisu-teen-policy-refresh.timer
/home/sisu/frappe-bench/env/bin/python -c 'import ast,sys; ast.parse(open(sys.argv[1]).read())' "$tmp/refresh.py"
install -d /opt/sisu-tools
install -o root -g root -m 644 "$tmp/refresh.py" /opt/sisu-tools/teen-policy-refresh.py
install -o root -g root -m 644 "$tmp/service" /etc/systemd/system/sisu-teen-policy-refresh.service
install -o root -g root -m 644 "$tmp/timer" /etc/systemd/system/sisu-teen-policy-refresh.timer
systemd-analyze verify /etc/systemd/system/sisu-teen-policy-refresh.service /etc/systemd/system/sisu-teen-policy-refresh.timer
systemctl daemon-reload
if ! systemctl start sisu-teen-policy-refresh.service; then
    journalctl -u sisu-teen-policy-refresh.service -n 15 --no-pager
    echo 'STOP: First delivery failed. Timer has not been enabled by this run.'
    exit 1
fi
systemctl enable --now sisu-teen-policy-refresh.timer
journalctl -u sisu-teen-policy-refresh.service -n 8 --no-pager
systemctl list-timers sisu-teen-policy-refresh.timer --no-pager
