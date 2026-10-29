"""Site-local material expiry rules."""
from datetime import datetime, timedelta

def deadline(days, now):
    if days in (None, ''): return None
    if isinstance(days, bool) or not str(days).isdigit() or not 1 <= int(days) <= 36500:
        raise ValueError('Choose Permanent or a whole number of days between 1 and 36500')
    return now + timedelta(days=int(days))

def expired(value, now):
    if not value: return False
    end = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return now >= end

def require_available(value, role, now):
    if role == 'Student' and expired(value, now):
        raise PermissionError('This material has expired. Ask your teacher to extend access.')
