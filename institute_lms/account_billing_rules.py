"""Fixed USD account subscriptions. No enrolment or attendance inputs."""
from calendar import monthrange
from datetime import datetime, timedelta

VERSION = 'monthly-country-2026-10'
TEACHER_CENTS = {
    'LK': {'Individual': 600, 'Silver': 1500, 'Gold': 4500, 'Platinum': 7500},
    'OVERSEAS': {'Individual': 900, 'Silver': 2200, 'Gold': 6500, 'Platinum': 11000},
}
PLANS = tuple(TEACHER_CENTS['LK'])

def amount(role, plan, country):
    if not isinstance(country, str) or len(country) != 2 or not country.isascii() or not country.isalpha() or country != country.upper():
        raise ValueError('A verified two-letter billing country is required')
    market = 'LK' if country == 'LK' else 'OVERSEAS'
    if role == 'Student':
        if plan != 'Student': raise ValueError('Students use the Student subscription')
        return 50 if market == 'LK' else 150
    if role not in ('Teacher', 'Institute') or plan not in PLANS:
        raise ValueError('Choose a valid subscription')
    return TEACHER_CENTS[market][plan] * (2 if role == 'Institute' else 1)

def next_anniversary(start, anchor_day):
    if not 1 <= anchor_day <= 31: raise ValueError('Invalid billing anchor')
    year, month = (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
    return start.replace(year=year, month=month, day=min(anchor_day, monthrange(year, month)[1]))

def trial_end(created):
    return created + timedelta(days=14)

def access_state(now, trial_until, paid_until=None, disabled=False):
    if disabled: return 'Suspended', False
    if paid_until and now < paid_until: return 'Active', True
    if now < trial_until: return 'Trial', True
    return 'Payment required', False

def payment_matches(expected, received, currency):
    return type(received) is int and received == expected and currency == 'USD'
