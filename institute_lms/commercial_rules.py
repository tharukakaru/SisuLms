"""SISU's four-plan contract. Money is integer LKR minor units; intervals are [start, end)."""
from datetime import datetime, timedelta
from calendar import monthrange
from decimal import Decimal

PLANS = {
    'Individual': dict(base_minor=200000, unit_minor=10000, students=30, teachers=1, operators=0),
    'Silver': dict(base_minor=500000, unit_minor=5000, students=None, teachers=None, operators=0),
    'Gold': dict(base_minor=1500000, unit_minor=5000, students=None, teachers=None, operators=2),
    'Platinum': dict(base_minor=2200000, unit_minor=5000, students=None, teachers=None, operators=5),
}
ONLINE = {'Gold', 'Platinum'}

def plan_features(name):
    if name not in PLANS: raise ValueError('Choose Individual, Silver, Gold or Platinum')
    online = name in ONLINE
    return dict(lms=True, news=online, study=True, branding=True, attendance=True,
                payments=True, reports=True, exams=True, whatsapp=online, integrations=online,
                expenses=online, custom_domain=online, view_limits=online, reviews=online,
                watermark=name=='Platinum', tute_delivery=name=='Platinum', white_label=name=='Platinum', ai=False)

def timestamp(value):
    return value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace('Z','+00:00'))

def next_month(value):
    value=timestamp(value); y,m=(value.year+1,1) if value.month==12 else (value.year,value.month+1)
    return value.replace(year=y,month=m,day=min(value.day,monthrange(y,m)[1]))

def access_window(kind, starts_at, ends_at=None):
    start=timestamp(starts_at)
    if kind in ('Day','Week'): end=start+timedelta(days=1 if kind=='Day' else 7)
    elif kind=='Month': end=next_month(start)
    elif kind=='Year': end=start.replace(year=start.year+1,day=min(start.day,monthrange(start.year+1,start.month)[1]))
    elif kind in ('Session','Course','Custom'):
        if not ends_at: raise ValueError('Set the end of this session, course or custom access')
        end=timestamp(ends_at)
    else: raise ValueError('Unknown access duration')
    if end<=start: raise ValueError('Access must end after it starts')
    return start,end

def billing_units(grants,start,end):
    """One unit at the start of each covered 30-day access window.

    Read complete grant history to preserve anchors across invoice boundaries.
    Duplicate module grants, overlapping grants and renewals inside an already
    charged window cannot create another charge. Intervals are end-exclusive.
    """
    start,end=timestamp(start),timestamp(end)
    if end<=start: raise ValueError('Invalid billing cycle')
    groups={}
    for g in grants:
        if g.get('status')!='Active':continue
        a,b=timestamp(g['starts_at']),timestamp(g['ends_at'])
        if b<=a:continue
        groups.setdefault((g['student'],g['product_key']),[]).append((a,b,g))
    units=[]
    for (student,product),rows in sorted(groups.items()):
        covered=None
        for a,b,g in sorted(rows,key=lambda r:(r[0],r[1])):
            anchor=max(a,covered) if covered else a
            while anchor<b:
                until=anchor+timedelta(days=30)
                if start<=anchor<end:
                    units.append(dict(student=student,product_key=product,teacher=g.get('teacher'),
                        title=g.get('title',product),charge_at=anchor.isoformat(),
                        covered_until=until.isoformat(),billing_policy='access-30-v1'))
                covered=until;anchor=until
    return units


def duration_days(value):
    try: days=int(value)
    except (ValueError,TypeError):raise ValueError('Choose a duration of 1–1800 whole days')
    if str(value)!=str(days) or not 1<=days<=1800:raise ValueError('Choose a duration of 1–1800 whole days')
    return days


def invoice_totals(plan,units):
    p=PLANS[plan]
    if type(units) is not int or units<0: raise ValueError('Invalid enrolment count')
    return dict(base_minor=p['base_minor'],unit_minor=p['unit_minor'],units=units,
                total_minor=p['base_minor']+units*p['unit_minor'],currency='LKR')

def overdue(status,due_at,now):
    return status not in ('Paid','Void') and bool(due_at) and timestamp(now)>=timestamp(due_at)

def money_minor(value):
    n=Decimal(str(value))
    if not n.is_finite() or n<=0 or n>Decimal('1000000000') or n.quantize(Decimal('.01'))!=n:
        raise ValueError('Enter a positive amount with at most two decimal places')
    return int(n*100)

def beneficiary(room):
    if room.get('owner_type')=='Teacher':
        if not room.get('owner_user'): raise ValueError('Independent teacher owner is missing')
        return 'Teacher:'+room.get('owner_user')
    if not room.get('institute'): raise ValueError('Institute owner is missing')
    return 'Institute:'+room.get('institute')
