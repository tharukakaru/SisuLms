"""Portable, read-only source/schema validation used by CI."""
import ast,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
files=[p for p in root.rglob('*') if p.is_file() and not {'node_modules','.git','__pycache__','.venv','.venv-review','venv'}.intersection(p.relative_to(root).parts)]
python=[p for p in files if p.suffix=='.py'];schemas=[p for p in files if p.suffix=='.json']
for p in python:ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
for p in schemas:
    d=json.loads(p.read_text(encoding='utf-8-sig'))
    if isinstance(d,dict) and d.get('doctype')=='DocType':
        names=[f['fieldname'] for f in d.get('fields',[])]
        assert len(names)==len(set(names)),f'Duplicate field: {p}'
        assert set(d.get('field_order',[]))<=set(names),f'Unknown field order: {p}'
print(f'PASS: {len(python)} Python sources; {len(schemas)} JSON documents')
