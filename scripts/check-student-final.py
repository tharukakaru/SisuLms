"""Read-only verification of student UI release sources and Python syntax."""
import ast
import hashlib
import json
import tarfile
from pathlib import Path
app=Path('/home/sisu/frappe-bench/apps/institute_lms')
with tarfile.open('/tmp/sisu-student-final.tgz') as archive:
    manifest=json.load(archive.extractfile('manifest.json'))
for name,entry in manifest.items():
    data=(app/name).read_bytes()
    assert hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()==entry['after'], 'Source mismatch: '+name
    if name.endswith('.py'):
        ast.parse(data.decode('utf-8'),filename=name)
assert (app/'institute_lms/www/campus.html').is_file()
print('PASS: 21 deployed source hashes and Python syntax. Campus entry exists.')
print('READ ONLY: no records, invoices, access, messages or gateway settings changed. Browser enrollment/slip approval and notification delivery still require testing.')
