"""Calendar policy shared by provider requests and finance settlement."""
from calendar import monthrange
from datetime import datetime
LIMIT=2
def month_bounds(now):
    start=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    end=start.replace(year=start.year+1,month=1) if start.month==12 else start.replace(month=start.month+1)
    return start,end
def last_week(now):
    return now.day>=monthrange(now.year,now.month)[1]-6
def completed_in_month(rows,now):
    start,end=month_bounds(now)
    return sum(1 for row in rows if row.get('status')=='Completed' and row.get('completed_at') and start<=datetime.fromisoformat(str(row['completed_at']))<end)
def slots_used(rows,now):
    # Outstanding requests from any month also reserve a slot in the current month.
    return completed_in_month(rows,now)+sum(row.get('status') in ('Pending','Processing') for row in rows)

