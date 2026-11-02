"""Copy only named application source files to the Windows review workspace.

Does not read site configuration, credentials, database records or private files.
Does not install code, enable shared mode or restart services.
"""
import ast
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

FILES = ('api.py', 'saas.py', 'account_billing.py', 'native_access.py',
         'portal_session.py', 'teaching.py', 'institute_coverage.py', 'hooks.py',
         'profiles.py', 'onboarding.py', 'portal_policy.py', 'validation.py')


def main():
    bench = (Path.home() / 'sisu-hnb-sandbox-bench').resolve()
    if os.name != 'posix' or Path.cwd().resolve() != bench:
        raise ValueError('Run in the local Ubuntu sandbox bench')
    if not (bench / 'sites/hnb-checkout.localhost/site_config.json').is_file():
        raise ValueError('Local sandbox site missing')
    source = (bench / 'apps/institute_lms/institute_lms').resolve(strict=True)
    project = Path(__file__).resolve().parents[1]
    destination = project.parent / 'sandbox-source-review' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    # Validate all inputs before writing the review copy.
    rows = {}
    for name in FILES:
        path = source / name
        if not path.is_file():
            print(f'MISSING: {name}')
            continue
        if path.resolve().parent != source:
            raise ValueError('Source file leaves the application directory')
        content = path.read_bytes()
        if len(content) > 2_000_000:
            raise ValueError('Unexpected source size')
        ast.parse(content.decode('utf-8-sig'))
        rows[name] = content
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {}
    for name, content in rows.items():
        (destination / name).write_bytes(content)
        local = project / 'institute_lms' / name
        digest = hashlib.sha256(content).hexdigest()
        manifest[name] = digest
        match = local.is_file() and hashlib.sha256(local.read_bytes()).hexdigest() == digest
        print(f'{"MATCH" if match else "REVIEW"}: {name}')
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'REVIEW COPY: {destination}')
    print('Sandbox unchanged. Only named Python source files copied; no settings, database or messages accessed.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'BLOCKED: source review [{type(error).__name__}]. No configuration or credentials printed.')
        raise SystemExit(1)
