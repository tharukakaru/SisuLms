"""Calendar-month attendance pricing. A person counts once per provider."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re


def month_bounds(month):
    if not re.fullmatch(r'\d{4}-\d{2}', str(month)):
        raise ValueError('Choose a month in YYYY-MM format.')
    start = datetime.strptime(month, '%Y-%m')
    end = datetime(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1)
    return start, end


def rate_minor(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount > 100000 or amount * 100 != (amount * 100).to_integral_value():
            raise ValueError()
        return int(amount * 100)
    except (ValueError, InvalidOperation):
        raise ValueError('Enter a rate from LKR 0 to 100,000 with at most two decimal places.')


def qualified_students(rows):
    sessions = defaultdict(set)
    for row in rows:
        if row.get('student') and row.get('session') and row.get('status') == 'Present':
            sessions[row['student']].add(row['session'])
    return {student: sorted(values) for student, values in sessions.items() if len(values) >= 2}


def price_for(policy, month):
    matches = [r for r in policy.get('rates', []) if r['month'] <= month]
    return max(matches, key=lambda r:r['month']) if matches else None
