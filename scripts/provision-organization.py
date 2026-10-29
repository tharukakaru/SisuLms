#!/usr/bin/env python3
"""Operator-only Linux Bench command; never invoked from web requests.

Export platform.provisioning_spec to JSON. Review it, run --dry-run, then --apply.
--create-site explicitly permits interactive Bench site creation. Passwords are
entered in Bench's secure prompts, never command arguments/spec files/log output.
"""
import argparse
import fcntl
import json
import re
import subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('spec',type=Path)
    action=p.add_mutually_exclusive_group();action.add_argument('--apply',action='store_true');action.add_argument('--dry-run',action='store_true')
    p.add_argument('--create-site',action='store_true')
    p.add_argument('--registry',type=Path,default=Path('sites/sisu-provisioning.json'))
    a=p.parse_args();s=json.loads(a.spec.read_text())
    required={'tenant_id','site_hostname','code','title','admin_email','job','schema_version','apps'}
    if set(s)!=required or s['schema_version']!=1:p.error('Unsupported provisioning spec')
    if not re.fullmatch(r'org-[a-f0-9]{32}',s['tenant_id']):p.error('Invalid tenant ID')
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{1,251}[a-z0-9])',s['site_hostname']) or '..' in s['site_hostname']:p.error('Invalid hostname')
    if not re.fullmatch(r'[A-Z][A-Z0-9]{1,11}',s['code']):p.error('Invalid institute code')
    if s['apps']!=['lms','institute_lms']:p.error('Unexpected applications')
    site=s['site_hostname'];config=Path('sites')/site/'site_config.json'
    commands=[]
    if not config.exists():
        if not a.create_site:p.error('Create the site separately or explicitly use --create-site')
        commands.append(['bench','new-site',site])
    commands += [['bench','--site',site,'install-app',app] for app in s['apps']]
    commands += [['bench','--site',site,'migrate'],['bench','--site',site,'execute','institute_lms.provisioning.initialize','--kwargs',json.dumps(s)]]
    if not a.apply:
        print(json.dumps({'dry_run':True,'commands':commands,'after':'configure per-site signing key, apply fresh manifest, configure mail and invite admin'},indent=2));return
    a.registry.parent.mkdir(parents=True,exist_ok=True)
    with a.registry.open('a+',encoding='utf-8') as f:
        fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);raw=f.read();registry=json.loads(raw) if raw else {}
        for tenant,row in registry.items():
            if tenant!=s['tenant_id'] and (row['site']==site or row['code']==s['code']):p.error('Site or code already reserved')
        old=registry.get(s['tenant_id'])
        if old and (old['site']!=site or old['code']!=s['code']):p.error('Tenant identity mismatch')
        if config.exists():
            bound=json.loads(config.read_text()).get('il_tenant_id')
            if bound and bound!=s['tenant_id']:p.error('Existing site is bound to another tenant')
        row=registry[s['tenant_id']]={'site':site,'code':s['code'],'job':s['job'],'state':'running'}
        def persist():f.seek(0);f.truncate();json.dump(registry,f,indent=2);f.flush()
        persist()
        try:
            for command in commands:
                if command[3:4]==['install-app']:
                    installed=subprocess.run(['bench','--site',site,'list-apps','--format','json'],check=True,capture_output=True,text=True)
                    if command[-1] in json.loads(installed.stdout):continue
                subprocess.run(command,check=True)
            row['state']='initialized_pending_manifest_and_invitation'
        except subprocess.CalledProcessError:
            row['state']='failed';raise
        finally:persist()
        print(json.dumps(row))
if __name__=='__main__':main()
