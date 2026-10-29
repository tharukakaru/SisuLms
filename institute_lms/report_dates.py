"""Calendar date windows shared by payment reports (end date is inclusive)."""
from datetime import date, datetime, timedelta

def report_window(start_date=None, end_date=None, today=None):
    today = today or date.today()
    if isinstance(today, datetime):
        today = today.date()
    if not start_date and not end_date:
        start = today.replace(day=1)
        stop = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, stop
    if not start_date or not end_date:
        raise ValueError('Choose both a start and end date.')
    try:
        start = date.fromisoformat(str(start_date))
        end = date.fromisoformat(str(end_date))
        if start > end:
            raise ValueError()
        return start, end + timedelta(days=1)
    except (ValueError, OverflowError):
        raise ValueError('Choose valid dates, with the end on or after the start.')
