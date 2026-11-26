"""Read-only host inventory. Prints routing paths and versions, never config values."""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path('/home/sisu/frappe-bench')


def main():
    for app in ('frappe', 'lms', 'payments'):
        result = subprocess.run(['git', '-c', 'safe.directory=' + str(ROOT / 'apps' / app),
                                 '-C', str(ROOT / 'apps' / app), 'rev-parse', 'HEAD'],
                                capture_output=True, text=True)
        revision = result.stdout.strip()
        print('APP', app, revision if re.fullmatch('[a-f0-9]{40,64}', revision) else 'revision unavailable')
    result = subprocess.run(['nginx', '-T'], capture_output=True, text=True)
    if result.returncode:
        print('NGINX inventory unavailable')
    else:
        # Deliberately omit proxy headers, certificates, auth and arbitrary directives.
        for line in result.stdout.splitlines():
            if re.match(r'^# configuration file ', line):
                print(line)
            elif re.match(r'^\s*(server_name|root|alias|listen)\s', line):
                print(line.strip())
    registry = ROOT / 'sites/sisu-provisioning.json'
    print('PROVISIONING REGISTRY EXISTS:', registry.is_file())
    # Only field names are needed to establish the registry schema, not private values.
    if registry.is_file():
        try:
            data = json.loads(registry.read_text())
            print('PROVISIONING REGISTRY TYPE:', type(data).__name__)
        except (ValueError, OSError):
            print('PROVISIONING REGISTRY: could not parse')
    print('Read-only inventory complete. No files, databases, email or services changed.')


if __name__ == '__main__':
    main()
