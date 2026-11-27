"""Host-independent removal state machine. Never exposed as a Frappe HTTP method.

A reviewed host adapter must verify real database/routing ownership and execute
fixed operations. No adapter is enabled by default; production is fail-closed.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

PROTECTED=frozenset({'sisuacademylk.com','www.sisuacademylk.com','platform.sisuacademylk.com','staging.sisuacademylk.com'})
STAGES=('validated','quiesced','backed_up','decommissioned','verified','completed')

@dataclass(frozen=True)
class RemovalIdentity:
    tenant: str
    hostname: str
    code: str
    request_id: str

    def validate(self, allowlist):
        if not re.fullmatch(r'org-[a-f0-9]{32}', self.tenant):raise ValueError('Invalid tenant')
        if (self.hostname in PROTECTED or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',self.hostname)
                or '..' in self.hostname or '.' not in self.hostname):raise ValueError('Protected or invalid hostname')
        if not self.code or not re.fullmatch(r'[a-zA-Z0-9_-]{8,100}',self.request_id):raise ValueError('Invalid request identity')
        if allowlist.get(self.tenant)!=self.hostname:raise ValueError('Tenant not approved by hosting inventory')


def verify_backups(receipt, backup_root):
    root=Path(backup_root).resolve(strict=True)
    if set(receipt)!={'database','public_files','private_files','configuration'}:raise ValueError('Incomplete backup receipt')
    for item in receipt.values():
        path=Path(item['path'])
        if path.is_symlink():raise ValueError('Backup symlink forbidden')
        path=path.resolve(strict=True)
        if root not in path.parents or not path.is_file() or path.stat().st_size==0:raise ValueError('Invalid backup path')
        digest=hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
        if digest.hexdigest()!=item['sha256']:raise ValueError('Backup checksum mismatch')


def execute(identity, adapter, journal_path, backup_root, allowlist):
    """Retry only the same bound request; never release a reservation before proof.

    Adapter methods must be idempotent and report proof, not just command exit
    codes. quiesce must not stop unrelated tenants. Financial/history export is
    part of check_dependencies, not implied by a generic database backup.
    """
    identity.validate(allowlist)
    journal_path=Path(journal_path)
    bound=identity.__dict__
    state=json.loads(journal_path.read_text()) if journal_path.exists() else {'identity':bound,'stage':None}
    if state['identity']!=bound:raise ValueError('Journal belongs to another request')
    if state['stage'] not in (None,*STAGES):raise ValueError('Unknown journal stage')
    def persist(stage):
        state['stage']=stage;state.pop('error',None)
        temporary=journal_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state,sort_keys=True),encoding='utf-8');temporary.replace(journal_path)
        progress = getattr(adapter, 'record_progress', None)
        if progress:progress(identity, stage)
    def done(stage):return state['stage'] is not None and STAGES.index(state['stage'])>=STAGES.index(stage)
    try:
        adapter.authorize_request(identity) # Recheck manager and request identity on every retry.
        if done('completed'):return state
        # Adapter must recognize partially decommissioned resources only through this journal.
        adapter.verify_identity(identity,state['stage'])
        adapter.check_dependencies(identity) # Includes unsettled obligations and preservation proof.
        if not done('validated'):persist('validated')
        if not done('quiesced'):
            adapter.quiesce(identity);persist('quiesced')
        if not done('backed_up'):
            state['backups']=adapter.backup(identity)
            verify_backups(state['backups'],backup_root)
            adapter.verify_restore_artifacts(identity,state['backups'])
            persist('backed_up')
        verify_backups(state['backups'],backup_root)
        if not done('decommissioned'):
            adapter.decommission(identity);persist('decommissioned')
        if not adapter.verify_absent(identity):raise RuntimeError('Hosting absence not verified')
        if not done('verified'):persist('verified')
        adapter.complete_registry(identity,state) # Fixed, privileged, non-HTTP completion contract.
        persist('completed')
        return state
    except Exception as exc:
        state['error']=type(exc).__name__ # No credentials or subprocess output in dashboard errors.
        temporary=journal_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state,sort_keys=True),encoding='utf-8');temporary.replace(journal_path)
        raise
