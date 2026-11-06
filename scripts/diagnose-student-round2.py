"""Read deployment logs and report fixed categories, never raw log contents."""
import json
import re
from pathlib import Path

root = Path('/home/sisu/.sisu-secrets')
runs = sorted(p for p in root.glob('student-round2-*') if p.is_dir() and not p.is_symlink())
if not runs:
    raise SystemExit('No student-round2 recovery directory found.')
run = runs[-1]
print('Recovery directory:', run)
patterns = {
    'build_completed': r'built in|build completed',
    'node_stack_overflow': r'Maximum call stack|RangeError|stack overflow',
    'out_of_memory': r'heap out of memory|allocation failed|Killed',
    'missing_module': r'Cannot find module|ModuleNotFoundError|ImportError|Could not resolve|Failed to resolve',
    'syntax_error': r'SyntaxError|Unexpected token|Error parsing',
    'permission_denied': r'Permission denied|PermissionError|EACCES',
    'missing_file': r'ENOENT|FileNotFoundError|No such file',
    'disk_full': r'ENOSPC|No space left',
    'seed_saved': r'^SAVED:',
    'seed_stopped': r'^STOPPED:',
    'demo_conflict': r'Demo .*conflict|Demo .*changed',
    'directory_check_failed': r'did not appear in directory',
    'validation_error': r'ValidationError|MandatoryError|LinkValidationError',
    'database_error': r'OperationalError|ProgrammingError|IntegrityError',
    'attribute_error': r'AttributeError',
    'type_error': r'TypeError',
    'runtime_error': r'RuntimeError',
}
for name in ('database-backup.log', 'build.log', 'demo-seed.log'):
    path = run / name
    body = path.read_text(errors='replace') if path.is_file() and not path.is_symlink() else ''
    known_conflicts = (
        'Demo profile conflict', 'Demo membership changed; review required',
        'Demo provider package changed; review required',
        'Demo class fee changed; review required', 'Demo classroom changed',
        'Independent demo profile changed', 'Independent demo membership changed',
        'Demo code belongs to another institute',
    )
    for message in known_conflicts:
        if message in body:
            print('Exact fixed diagnostic: ' + message)
    print(json.dumps({'log': name, 'present': path.is_file(), 'bytes': len(body.encode()),
                      'categories': [label for label, pattern in patterns.items() if re.search(pattern, body, re.I | re.M)],
                      'exception_types': sorted(set(re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b', body)))}))
print('Read only. No raw logs, credentials, configuration changes, retries or messages.')
