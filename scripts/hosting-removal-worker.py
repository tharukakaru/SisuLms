#!/usr/bin/env python3
"""Run from a root-owned installation, with an explicitly reviewed host inventory."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

from institute_lms.hosting_removal_adapter import BenchRemovalAdapter, private_file
from institute_lms.hosting_retirement import RemovalIdentity, execute


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Root-owned hosting service required')
    os.umask(0o077)
    config = json.loads(private_file(args.config).read_text())
    if config.get('version') != 1 or config.get('enabled') is not True:
        parser.error('Reviewed hosting inventory is not enabled')
    root = Path(config['backup_root'])
    if not root.is_absolute() or root.is_symlink():
        parser.error('Absolute private backup directory required')
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.stat().st_uid != 0 or root.stat().st_mode & 0o077:
        parser.error('Unsafe backup directory owner/mode')
    with (root / 'worker.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another removal worker is running');return
        result = subprocess.run(['sudo', '-H', '-u', 'sisu', '--', '/usr/local/bin/bench',
            '--site', config['control_site'], 'execute', 'institute_lms.removal_control.pending'],
            cwd=config['bench'], check=True, capture_output=True, text=True)
        failed = False
        for row in json.loads(result.stdout):
            if row['name'] not in config['tenants']:
                print('Request awaits approved hosting inventory:', row['name']);continue
            identity = RemovalIdentity(row['name'], row['site_hostname'], row['institute_code'], row['removal_request_id'])
            adapter = None
            try:
                identity.validate({k: v['hostname'] for k, v in config['tenants'].items()})
                adapter = BenchRemovalAdapter(config, identity)
                adapter.authorize_request(identity)
                adapter.bridge('progress', tenant=identity.tenant, request_id=identity.request_id, stage='starting')
                execute(identity, adapter, adapter.root / 'journal.json', root,
                        {k: v['hostname'] for k, v in config['tenants'].items()})
                print('Removal verified:', identity.tenant)
            except Exception as exc:
                failed = True
                # Do not emit subprocess stderr, credentials or customer records.
                print('Removal stopped:', identity.tenant, type(exc).__name__)
                if adapter:
                    try:
                        adapter.bridge('progress', tenant=identity.tenant, request_id=identity.request_id,
                                       stage='failed', failed=True)
                    except Exception:
                        print('Control-plane status update failed; private journal remains authoritative')
        if failed:
            sys.exit(1)


if __name__ == '__main__':
    main()
