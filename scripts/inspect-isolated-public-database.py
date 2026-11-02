"""Read-only preparation diagnostics; never emit container environment or logs."""
import errno
import json
import os
import socket
import subprocess
from pathlib import Path


def emit(**values):
    print(json.dumps(values))


def main():
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run as root on deployment server')
    for port in (3308, 3309, 3310):
        try:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', port))
            emit(port=port, available=True)
        except OSError as exc:
            emit(port=port, available=False, error=errno.errorcode.get(exc.errno, 'UNKNOWN'))
    result = subprocess.run(['docker', 'ps', '-a', '--format', '{{json .}}'], capture_output=True, text=True)
    emit(docker_listing_ok=result.returncode == 0)
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            item = json.loads(line)
            if item.get('Names') == 'sisu-public-db' or any(str(p) in item.get('Ports', '') for p in (3308, 3309, 3310)):
                emit(container=item.get('Names'), status=item.get('Status'), ports=item.get('Ports'))
    result = subprocess.run(['docker', 'volume', 'ls', '--format', '{{.Name}}'], capture_output=True, text=True)
    emit(public_volume_present='sisu-public-db-data' in result.stdout.splitlines())
    root = Path('/root/sisu-public-database')
    site = Path('/home/sisu/frappe-bench/sites/sisuacademylk.com')
    emit(preparation_directory=root.exists(), credential_file=(root/'database.env').is_file(),
         preserved_partial_site=(root/'preserved-partial-site').exists(),
         public_site_directory=site.exists(), isolated_creation_started=Path('/root/sisu-public-provision-isolated').exists())
    print('READ ONLY: no files, containers, databases or settings changed. No credentials or raw logs displayed.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        emit(stopped=type(exc).__name__, errno=getattr(exc, 'errno', None))
        raise SystemExit(1)
