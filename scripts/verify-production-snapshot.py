"""Check the exact exported source, accepting recorded LF-normalized hashes."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
m = json.loads((root / 'deployment/production-manifest.json').read_text(encoding='utf8'))
failed = []
for name, info in m['files'].items():
    prefix, relative = name.split('/', 1)
    p = root / (relative if prefix == 'lms' else 'marketing/' + relative)
    if not p.is_file():
        failed.append(name + ': missing')
        continue
    data = p.read_bytes()
    if hashlib.sha256(data).hexdigest() == info['sha256']:
        continue
    if info.get('lf_sha256') and hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest() == info['lf_sha256']:
        continue
    failed.append(name + ': changed')
if failed:
    print('\n'.join(failed))
    raise SystemExit(1)
print('PASS:', len(m['files']), 'production files match.')
