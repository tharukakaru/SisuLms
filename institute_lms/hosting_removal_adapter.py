"""Restricted Linux hosting adapter. Imported by the root-owned timer, never HTTP.

Inventory is installed separately by the host administrator. A dashboard request
cannot supply database credentials, filesystem paths, executables or shell code.
Only dedicated databases/users and dedicated nginx tenant files are supported.
"""
import gzip
import hashlib
import http.client
import time
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

from .hosting_retirement import PROTECTED


def private_file(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected private regular file')
    if os.name == 'posix' and (path.stat().st_uid != 0 or path.stat().st_mode & 0o077):
        raise ValueError('Worker configuration must be root-owned, mode 0600')
    return path


def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


class BenchRemovalAdapter:
    def __init__(self, config, identity):
        self.config, self.identity = config, identity
        self.row = config['tenants'][identity.tenant]
        self.bench = Path(config['bench']).resolve(strict=True)
        self.site = self.bench / 'sites' / identity.hostname
        self.root = Path(config['backup_root']).resolve(strict=True) / identity.request_id
        self.root.mkdir(mode=0o700, exist_ok=True)
        self.route = Path(self.row['nginx_file'])
        self.archived = self.root / 'retired-site'
        self.defaults = private_file(self.row['mysql_defaults_file'])
        for field in ('database', 'database_user'):
            if not re.fullmatch(r'[a-zA-Z0-9_]{1,64}', self.row[field]):
                raise ValueError('Invalid database identifier')
        if self.row['database'] in {'mysql', 'sys', 'performance_schema', 'information_schema'}:
            raise ValueError('Protected database')
        if not re.fullmatch(r'[a-zA-Z0-9.%:_-]{1,255}', self.row['database_user_host']):
            raise ValueError('Invalid database account host')
        if self.row['hostname'] != identity.hostname or self.row['code'] != identity.code:
            raise ValueError('Inventory identity mismatch')
        if identity.hostname in PROTECTED or identity.hostname == config['control_site']:
            raise ValueError('Protected site')
        if self.route.is_symlink() or self.route.parent.resolve() != Path(config['nginx_directory']).resolve():
            raise ValueError('Routing path outside approved directory')
        self.db = self.row['database']
        self.user = self.row['database_user']
        self.account = "'%s'@'%s'" % (self.user, self.row['database_user_host'])

    def run(self, args, **kwargs):
        # Never shell=True. stderr stays private; callers expose only error codes.
        return subprocess.run([str(x) for x in args], check=True, capture_output=True, **kwargs)

    def sql(self, query):
        return self.run(['/usr/bin/mariadb', '--defaults-extra-file=' + str(self.defaults),
                         '--batch', '--skip-column-names'], input=query.encode()).stdout.decode().strip()

    def bridge(self, method, **kwargs):
        if method not in {'snapshot', 'progress', 'complete'}:
            raise ValueError('Unsupported worker operation')
        result = self.run(['sudo', '-H', '-u', 'sisu', '--', '/usr/local/bin/bench',
                           '--site', self.config['control_site'], 'execute',
                           'institute_lms.removal_control.' + method, '--kwargs', json.dumps(kwargs)], cwd=self.bench)
        return json.loads(result.stdout.decode())

    def authorize_request(self, identity):
        result = self.bridge('snapshot', tenant=identity.tenant, request_id=identity.request_id)
        if not result.get('completed'):
            for key in ('tenant', 'hostname', 'code', 'request_id'):
                if result[key] != getattr(identity, key):
                    raise ValueError('Control-plane request mismatch')

    def route_text(self):
        return self.route.read_text(encoding='utf-8')

    def verify_identity(self, identity, stage):
        directory = self.site if self.site.exists() else self.archived
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError('Site directory missing or symlinked')
        cfg = json.loads((directory / 'site_config.json').read_text())
        expected = {'db_name': self.db, 'db_host': self.row['database_host'], 'db_port': self.row['database_port']}
        for field, value in expected.items():
            if str(cfg.get(field, '127.0.0.1' if field == 'db_host' else 3306)) != str(value):
                raise ValueError('Database identity mismatch')
        if cfg.get('il_tenant_id') != identity.tenant:
            raise ValueError('Site is not bound to this organization')
        if cfg.get('db_user', cfg['db_name']) != self.user:
            raise ValueError('Database principal mismatch')
        for other in (self.bench / 'sites').iterdir():
            if other == self.site or not (other / 'site_config.json').is_file():
                continue
            other_cfg = json.loads((other / 'site_config.json').read_text())
            same_server = (str(other_cfg.get('db_host', '127.0.0.1')), str(other_cfg.get('db_port', 3306))) == (str(self.row['database_host']), str(self.row['database_port']))
            if same_server and (other_cfg.get('db_name') == self.db or other_cfg.get('db_user', other_cfg.get('db_name')) == self.user):
                raise ValueError('Database or user shared with another configured site')
        # Verify credentials target the inventoried server, not a default socket/database.
        defaults = self.defaults.read_text()
        for key, value in [('host', self.row['database_host']), ('port', self.row['database_port'])]:
            matches = re.findall(r'^\s*' + key + r'\s*=\s*(.*?)\s*$', defaults, re.M)
            if matches != [str(value)]:
                raise ValueError('Database credential endpoint mismatch')
        route = self.route_text()
        names = re.findall(r'^\s*server_name\s+([^;]+);', route, re.M)
        if not names or any(name.split() != [identity.hostname] for name in names):
            raise ValueError('Only a dedicated single-tenant nginx file is supported')
        saved = self.root / 'routing.conf'
        expected_hash = hashlib.sha256(saved.read_bytes()).hexdigest() if saved.exists() else self.row['nginx_sha256']
        if not (self.root / 'quiesced.json').exists() and hashlib.sha256(self.route.read_bytes()).hexdigest() != expected_hash:
            raise ValueError('Routing changed since inventory approval')

    def check_dependencies(self, identity):
        if (self.root / 'drop-intent.json').exists():
            return
        # Fail closed if the table inventory is different from the reviewed schema.
        tables = set(self.sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='%s'" % self.db).splitlines())
        required = {'tabIL Account Invoice', 'tabIL Payout Request', 'tabIL Payment Attempt', 'tabIL Wallet'}
        if not required <= tables:
            raise ValueError('Financial schema requires operator review')
        queries = ["SELECT COUNT(*) FROM `%s`.`tabIL Account Invoice` WHERE status IN ('Draft','Unpaid')",
                   "SELECT COUNT(*) FROM `%s`.`tabIL Payout Request` WHERE status IN ('Pending','Processing')",
                   "SELECT COUNT(*) FROM `%s`.`tabIL Payment Attempt` WHERE status IN ('created','pending')"]
        if any(int(self.sql(q % self.db)) for q in queries):
            raise ValueError('Unresolved tenant financial obligations')
        optional = {
            'tabIL Invoice': ('Unpaid', 'Overdue'),
            'tabIL Provider Invoice': ('Unpaid', 'Under review'),
            'tabIL Usage Invoice': ('Estimate', 'Unpaid'),
            'tabIL Lecture Refund': ('Pending', 'Review'),
        }
        for table, statuses in optional.items():
            if table in tables:
                values = ','.join("'%s'" % value for value in statuses)
                if int(self.sql('SELECT COUNT(*) FROM `%s`.`%s` WHERE status IN (%s)' % (self.db, table, values))):
                    raise ValueError('Unresolved invoice or refund obligations')
        # Non-zero wallet balances require reconciliation, never deletion by inference.
        columns = set(self.sql("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='tabIL Wallet'" % self.db).splitlines())
        balance_columns = sorted(columns & {'balance', 'balance_minor', 'available_balance', 'pending_balance', 'available_minor', 'held_minor'})
        if not balance_columns:
            raise ValueError('Wallet balance schema requires review')
        if any(int(self.sql('SELECT COUNT(*) FROM `%s`.`tabIL Wallet` WHERE COALESCE(`%s`,0) != 0' % (self.db, col))) for col in balance_columns):
            raise ValueError('Wallet balances must be reconciled')

    def quiesce(self, identity):
        marker = self.root / 'quiesced.json'
        if marker.exists():
            return
        if not (self.root / 'routing.conf').exists():
            shutil.copyfile(self.route, self.root / 'routing.conf')
        cfg_path = self.site / 'site_config.json'
        if not (self.root / 'configuration-original.json').exists():
            shutil.copyfile(cfg_path, self.root / 'configuration-original.json')
        grants = self.sql('SHOW GRANTS FOR ' + self.account).splitlines()
        # Dedicated DB users only: global privileges and grants to other schemas are forbidden.
        for grant in grants:
            if 'GRANT USAGE ON *.*' not in grant and (' ON `' + self.db + '`.* TO ') not in grant:
                raise ValueError('Database user has privileges outside this tenant')
        if not (self.root / 'grants.json').exists():
            atomic_json(self.root / 'grants.json', grants)
        cfg_stat = cfg_path.stat()
        cfg = json.loads(cfg_path.read_text());cfg['maintenance_mode'] = 1;cfg['pause_scheduler'] = 1
        atomic_json(cfg_path, cfg)
        os.chown(cfg_path, cfg_stat.st_uid, cfg_stat.st_gid)
        os.chmod(cfg_path, cfg_stat.st_mode & 0o777)
        # Preserve TLS/listen directives, but replace every location response with maintenance
        # by adding a server-level return. Dedicated routing must have simple server blocks.
        original = (self.root / 'routing.conf').read_text()
        retired = re.sub(r'\bserver\s*\{', 'server {\n    return 410;', original)
        self.route.write_text(retired)
        try:
            self.run(['/usr/sbin/nginx', '-t'])
            self.run(['/usr/sbin/nginx', '-s', 'reload'])
        except Exception:
            self.route.write_text(original)
            self.run(['/usr/sbin/nginx', '-t'])
            self.run(['/usr/sbin/nginx', '-s', 'reload'])
            raise
        if any((' ON `' + self.db + '`.* TO ') in g for g in grants):
            self.sql('REVOKE ALL PRIVILEGES ON `%s`.* FROM %s' % (self.db, self.account))
        for identifier in self.sql("SELECT ID FROM information_schema.PROCESSLIST WHERE USER='%s'" % self.user).splitlines():
            if not identifier.isdigit():
                raise ValueError('Invalid database session identifier')
            self.sql('KILL ' + identifier)
        atomic_json(marker, {'routing_sha256': hashlib.sha256(self.route.read_bytes()).hexdigest()})
        self.check_dependencies(identity)

    def backup(self, identity):
        sql_path = self.root / 'database.sql.gz'
        with (self.root / 'dump-error.log').open('wb') as errors, gzip.open(sql_path, 'wb') as output:
            process = subprocess.Popen(['/usr/bin/mariadb-dump', '--defaults-extra-file=' + str(self.defaults),
                '--single-transaction', '--quick', '--skip-lock-tables', '--skip-add-locks', self.db], stdout=subprocess.PIPE, stderr=errors)
            shutil.copyfileobj(process.stdout, output)
            if process.wait():
                raise RuntimeError('Database backup failed')
        for label, folder in [('public_files', 'public/files'), ('private_files', 'private/files')]:
            directory = self.site / folder
            with tarfile.open(self.root / (label + '.tar.gz'), 'w:gz') as tar:
                if directory.exists():
                    for path in directory.rglob('*'):
                        if path.is_symlink():
                            raise ValueError('Upload symlink requires manual review')
                    tar.add(directory, arcname='files')
        paths = {'database': sql_path, 'public_files': self.root / 'public_files.tar.gz',
                 'private_files': self.root / 'private_files.tar.gz', 'configuration': self.root / 'configuration-original.json'}
        return {name: {'path': str(path), 'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()} for name, path in paths.items()}

    def verify_restore_artifacts(self, identity, backups):
        with gzip.open(backups['database']['path'], 'rb') as stream:
            seen = False
            for line in stream:
                if line.startswith((b'CREATE DATABASE', b'DROP DATABASE', b'USE ')):
                    raise ValueError('Backup contains cross-database directives')
                seen |= b'CREATE TABLE' in line
            if not seen:
                raise ValueError('Database backup contains no schema')
        for name in ('public_files', 'private_files'):
            with tarfile.open(backups[name]['path']) as tar:
                for member in tar:
                    if member.issym() or member.islnk() or Path(member.name).is_absolute() or '..' in Path(member.name).parts:
                        raise ValueError('Invalid upload backup member')
                    if member.isfile():
                        with tar.extractfile(member) as stream:
                            while stream.read(1024 * 1024):
                                pass
        json.loads(Path(backups['configuration']['path']).read_text())

    def routing_retired(self):
        for attempt in range(20):
            connection = http.client.HTTPConnection('127.0.0.1', int(self.config.get('probe_port', 80)), timeout=3)
            try:
                connection.request('GET', '/', headers={'Host': self.identity.hostname})
                response = connection.getresponse()
                if response.status == 410:
                    return True
            finally:
                connection.close()
            time.sleep(.1)
        return False

    def decommission(self, identity):
        self.verify_identity(identity, 'backed_up')
        marker = self.root / 'quiesced.json'
        if not marker.exists() or hashlib.sha256(self.route.read_bytes()).hexdigest() != json.loads(marker.read_text())['routing_sha256']:
            raise ValueError('Tenant routing is not quiesced')
        if not self.routing_retired():
            raise ValueError('Running nginx has not confirmed tenant retirement')
        # The verified dump and uploads remain in the private archive for audit/recovery.
        atomic_json(self.root / 'drop-intent.json', {'tenant': identity.tenant, 'database': self.db})
        self.sql('DROP DATABASE IF EXISTS `%s`' % self.db)
        self.sql('DROP USER IF EXISTS ' + self.account)
        if self.site.exists():
            if self.archived.exists():
                raise ValueError('Conflicting retired site directory')
            shutil.move(str(self.site), str(self.archived))
        atomic_json(self.root / 'dropped.json', {'tenant': identity.tenant})

    def verify_absent(self, identity):
        database = self.sql("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='%s'" % self.db)
        user = self.sql("SELECT COUNT(*) FROM mysql.user WHERE User='%s' AND Host='%s'" % (self.user, self.row['database_user_host']))
        marker = json.loads((self.root / 'quiesced.json').read_text())
        return self.routing_retired() and database == '0' and user == '0' and not self.site.exists() and self.archived.is_dir() and hashlib.sha256(self.route.read_bytes()).hexdigest() == marker['routing_sha256']

    def record_progress(self, identity, stage):
        if stage != 'completed':
            self.bridge('progress', tenant=identity.tenant, request_id=identity.request_id, stage=stage)

    def complete_registry(self, identity, state):
        self.bridge('complete', tenant=identity.tenant, request_id=identity.request_id, hostname=identity.hostname, code=identity.code)
        # The root-owned inventory retains the audit identity; mark its reservation released.
        # Reuse requires provisioning to replace the old 410 route deliberately.
        atomic_json(self.root / 'completion.json', {'tenant': identity.tenant, 'request_id': identity.request_id, 'completed': True})
