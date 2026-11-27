"""Pure rules for continuous paid classroom periods."""
from datetime import timedelta


def paid_through(periods, start):
    """Extend only through overlapping/adjacent periods, never across unpaid gaps."""
    end = start
    for begins, finishes in sorted(periods):
        if begins > end:
            break
        if finishes > end:
            end = finishes
    return end


def reminder_due(end, now):
    return now < end <= now + timedelta(days=3)
