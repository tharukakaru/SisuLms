"""Renewal timing without shortening existing access or creating charges."""
from datetime import datetime, timedelta

WINDOW = timedelta(days=4)

def moment(value):
    return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))

def expiry(account):
    if account.get('paid_until'):
        return moment(account.get('paid_until'))
    if account.get('onboarding_payment_required'):
        return None
    return moment(account.get('trial_until')) if account.get('trial_until') else None

def window(account, now):
    end = expiry(account)
    eligible = account.get('role') in ('Teacher', 'Institute') and bool(account.get('enabled')) and not account.get('cancel_at_end')
    return {'renewal_opens_at': end - WINDOW if end else None,
            'renewal_available': bool(eligible and end and now >= end - WINDOW),
            'access_ends_at': end,
            'remaining_seconds': max(0, int((end-now).total_seconds())) if end else 0}

def period_start(account, now):
    end = expiry(account)
    # Payment adds a month after the existing paid period or remaining free trial.
    if end and end > now:
        return end
    if account.get('paid_until') and end and now-end < timedelta(days=1):
        return end
    return now
