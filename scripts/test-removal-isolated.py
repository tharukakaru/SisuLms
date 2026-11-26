#!/usr/bin/env python3
"""Destructive test ONLY inside a freshly created disposable Docker database.

Uses a separate nginx PID/config/port and temporary fake Bench directory. Never
opens production site configs. Control-plane bridge is a fixture, not a Frappe
integration test. Keeps private backups/evidence; removes only its own container.
"""
import gzip
import hashlib
import http.client
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time

from institute_lms.hosting_removal_adapter import BenchRemovalAdapter
from institute_lms.hosting_retirement import RemovalIdentity, execute


def command(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def main():
    if os.geteuid() != 0:
        raise RuntimeError('Run as root for the isolated local nginx process')
    os.umask(0o077)
    command(['docker', 'image', 'inspect', 'mariadb:11.8'])  # No image pull or production upgrade.
    root = Path(tempfile.mkdtemp(prefix='sisu-removal-disposable-'))
    name = 'sisu-removal-test-' + secrets.token_hex(6)
    password = secrets.token_hex(24)
    env = root / 'database.env';env.write_text('MARIADB_ROOT_PASSWORD=' + password + '\n')
    defaults = root / 'mysql.cnf'
    nginx = root / 'nginx.conf'
    started_nginx = False
    try:
        command(['docker', 'run', '-d', '--name', name, '--label', 'sisu.disposable-removal-test=true',
                 '--env-file', str(env), '-p', '127.0.0.1::3306', 'mariadb:11.8'])
        port = command(['docker', 'port', name, '3306/tcp']).stdout.decode().strip().rsplit(':', 1)[1]
        defaults.write_text('[client]\nhost=127.0.0.1\nport=' + port + '\nuser=root\npassword=' + password + '\n')
        def sql(query, database=None):
            args = ['/usr/bin/mariadb', '--defaults-extra-file=' + str(defaults), '--batch', '--skip-column-names']
            if database:args.append(database)
            return command(args, input=query.encode()).stdout.decode().strip()
        for attempt in range(60):
            try:sql('SELECT 1');break
            except subprocess.CalledProcessError:
                if attempt == 59:raise
                time.sleep(1)
        sql("CREATE DATABASE disposable_tenant; CREATE DATABASE unrelated_tenant; "
            "CREATE TABLE unrelated_tenant.sentinel (value INT); INSERT INTO unrelated_tenant.sentinel VALUES (725); "
            "CREATE USER 'disposable_tenant'@'%' IDENTIFIED BY 'test-only-local'; "
            "GRANT ALL ON disposable_tenant.* TO 'disposable_tenant'@'%';")
        sql("CREATE TABLE `tabIL Account Invoice` (status VARCHAR(30)); "
            "CREATE TABLE `tabIL Payout Request` (status VARCHAR(30)); "
            "CREATE TABLE `tabIL Payment Attempt` (status VARCHAR(30)); "
            "CREATE TABLE `tabIL Wallet` (available_minor INT, held_minor INT); "
            "CREATE TABLE `tabIL Institute` (name VARCHAR(80)); "
            "INSERT INTO `tabIL Institute` VALUES ('Disposable institute'); "
            "INSERT INTO `tabIL Account Invoice` VALUES ('Paid'); "
            "INSERT INTO `tabIL Wallet` VALUES (0,0);", 'disposable_tenant')
        identity = RemovalIdentity('org-' + 'd' * 32, 'disposable-removal.example.invalid', 'DUMMY', secrets.token_hex(16))
        bench = root / 'bench';site = bench / 'sites' / identity.hostname
        (site / 'public/files').mkdir(parents=True);(site / 'private/files').mkdir(parents=True)
        (site / 'public/files/example.txt').write_text('dummy public upload')
        (site / 'private/files/example.txt').write_text('dummy private upload')
        (site / 'site_config.json').write_text(json.dumps({'db_name': 'disposable_tenant', 'db_host': '127.0.0.1',
            'db_port': int(port), 'il_tenant_id': identity.tenant}))
        sentinel = bench / 'sites/sisuacademylk.com';sentinel.mkdir()
        (sentinel / 'site_config.json').write_text(json.dumps({'db_name': 'unrelated_tenant', 'db_host': '127.0.0.1', 'db_port': int(port)}))
        sentinel_hash = hashlib.sha256((sentinel / 'site_config.json').read_bytes()).hexdigest()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0));http_port = sock.getsockname()[1]
        routes = root / 'routes';routes.mkdir();route = routes / 'dummy.conf'
        route.write_text('server {\nlisten 127.0.0.1:%d;\nserver_name %s;\nlocation / { return 200 "dummy"; }\n}\n' % (http_port, identity.hostname))
        nginx.write_text('pid %s;\nerror_log %s;\nevents {}\nhttp { access_log off; include %s; }\n' % (root / 'nginx.pid', root / 'nginx-error.log', route))
        command(['/usr/sbin/nginx', '-p', str(root), '-c', str(nginx)]);started_nginx = True
        backups = root / 'backups';backups.mkdir()
        config = {'probe_port': http_port, 'bench': str(bench), 'backup_root': str(backups), 'control_site': 'platform.sisuacademylk.com',
                  'nginx_directory': str(routes), 'tenants': {identity.tenant: {
                      'hostname': identity.hostname, 'code': identity.code, 'database': 'disposable_tenant',
                      'database_user': 'disposable_tenant', 'database_user_host': '%', 'database_host': '127.0.0.1',
                      'database_port': int(port), 'mysql_defaults_file': str(defaults), 'nginx_file': str(route),
                      'nginx_sha256': hashlib.sha256(route.read_bytes()).hexdigest()}}}
        calls = []
        class IsolatedAdapter(BenchRemovalAdapter):
            def bridge(self, method, **kwargs):
                calls.append(method)
                if method == 'snapshot':return dict(identity.__dict__, status='Requested')
                if method == 'complete':
                    assert self.verify_absent(identity), 'Completion before verified absence'
                return {}

            def run(self, args, **kwargs):
                if str(args[0]) == '/usr/sbin/nginx':
                    args = [str(args[0]), '-p', str(root), '-c', str(nginx), *args[1:]]
                return super().run(args, **kwargs)

        adapter = IsolatedAdapter(config, identity)
        allow = {identity.tenant: identity.hostname}
        # Unpaid invoices must block without removing any data.
        sql("INSERT INTO `tabIL Account Invoice` VALUES ('Unpaid')", 'disposable_tenant')
        try:adapter.check_dependencies(identity)
        except ValueError:pass
        else:raise AssertionError('Unpaid invoice was not blocked')
        sql("DELETE FROM `tabIL Account Invoice` WHERE status='Unpaid'", 'disposable_tenant')
        state = execute(identity, adapter, adapter.root / 'journal.json', backups, allow)
        assert state['stage'] == 'completed' and adapter.verify_absent(identity)
        for attempt in range(20):
            connection = http.client.HTTPConnection('127.0.0.1', http_port, timeout=3)
            connection.request('GET', '/', headers={'Host': identity.hostname});response = connection.getresponse()
            status = response.status;response.read();connection.close()
            if status == 410:break
            time.sleep(.1)
        assert status == 410, 'Dummy website is not retired'
        assert sql('SELECT value FROM unrelated_tenant.sentinel') == '725'
        assert hashlib.sha256((sentinel / 'site_config.json').read_bytes()).hexdigest() == sentinel_hash
        # Restore the archived real SQL into a new DB in the same disposable container.
        sql('CREATE DATABASE restored_dummy')
        with gzip.open(state['backups']['database']['path'], 'rt') as stream:
            sql(stream.read(), 'restored_dummy')
        assert sql('SELECT name FROM `tabIL Institute`', 'restored_dummy') == 'Disposable institute'
        assert sql('SELECT status FROM `tabIL Account Invoice`', 'restored_dummy') == 'Paid'
        execute(identity, adapter, adapter.root / 'journal.json', backups, allow)
        report = {'result': 'PASS', 'database_dropped': True, 'dummy_http_status': status,
                  'unrelated_database_preserved': True, 'backup_restored': True, 'retry_safe': True,
                  'scope': 'Real disposable MariaDB/nginx; fixture control-plane bridge, not full Frappe dashboard integration'}
        (root / 'result.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2));print('Private test evidence:', root)
    finally:
        if started_nginx:
            subprocess.run(['/usr/sbin/nginx', '-p', str(root), '-c', str(nginx), '-s', 'quit'], capture_output=True)
        # This random container was created by this invocation; no production volumes are mounted.
        subprocess.run(['docker', 'rm', '-f', '-v', name], capture_output=True)


if __name__ == '__main__':main()
