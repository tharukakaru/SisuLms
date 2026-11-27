"""Administrator-only campus directory and relationship reports, plus provider profile review."""
from contextlib import contextmanager
import frappe
from .owner_operations import sources, connect

PAGE_SIZE = 25
BASE = """ FROM `tabUser` u LEFT JOIN `tabIL Public Profile` p ON p.user=u.name
 WHERE u.name NOT IN ('Guest','Administrator') AND (p.name IS NOT NULL OR EXISTS
 (SELECT 1 FROM `tabIL Member` m WHERE m.user=u.name))"""
KIND = "COALESCE(p.kind, CASE WHEN EXISTS (SELECT 1 FROM `tabIL Member` m WHERE m.user=u.name AND m.role='Teacher') THEN 'Teacher' WHEN EXISTS (SELECT 1 FROM `tabIL Member` m WHERE m.user=u.name AND m.role='Admin') THEN 'Institute' ELSE 'Student' END)"
IDENTITY = "u.name AS user,COALESCE(NULLIF(p.display_name,''),u.full_name,u.name) AS display_name,p.username,p.lms_id,p.workspace,p.name AS profile," + KIND + " AS kind,p.status AS profile_status,u.enabled,u.creation AS joined_at,u.last_login"


def authorize():
    from .platform import owner
    from .owner_access import require_manager
    owner()
    require_manager()


def pagination(page):
    try:
        value = int(page)
        if str(value) != str(page) or not 0 <= value <= 10000:
            raise ValueError
        return value
    except (ValueError, TypeError):
        frappe.throw('Choose a valid page.')


@contextmanager
def campus(site):
    if site not in sources():
        frappe.throw('This campus is not enabled for administrator reporting.', frappe.PermissionError)
    connection = None
    try:
        connection = connect(site)
        with connection.cursor() as cursor:
            cursor.execute('START TRANSACTION READ ONLY')
            yield cursor
    finally:
        if connection is not None:
            connection.close()


def fetch(cursor, sql, args=()):
    cursor.execute(sql, args)
    return list(cursor.fetchall())


def window(cursor, sql, args, page):
    rows = fetch(cursor, sql + ' LIMIT %s OFFSET %s', (*args, PAGE_SIZE + 1, page * PAGE_SIZE))
    return dict(rows=rows[:PAGE_SIZE], has_next=len(rows) > PAGE_SIZE, page=page)


@frappe.whitelist(methods=['GET'])
def overview():
    authorize()
    result=[]
    for site in sources():
        try:
            with campus(site) as c:
                counts=fetch(c, 'SELECT ' + KIND + ' AS kind,COUNT(DISTINCT u.name) AS total,COUNT(DISTINCT CASE WHEN u.enabled=1 THEN u.name END) AS enabled' + BASE + ' GROUP BY kind')
                result.append(dict(site=site, available=True, counts=counts))
        except Exception:
            result.append(dict(site=site, available=False, message='Reporting unavailable. Check the campus connection and try again.'))
    return dict(campuses=result)


@frappe.whitelist(methods=['GET'])
def directory(site, kind='All', query='', state='All', page=0):
    authorize()
    page=pagination(page)
    if kind not in ('All','Student','Teacher','Institute') or state not in ('All','Enabled','Disabled'):
        frappe.throw('Choose a valid account filter.')
    query=str(query or '').strip()
    if len(query)>120: frappe.throw('Keep your search under 120 characters.')
    where=BASE
    args=[]
    if kind!='All':
        where+=' AND '+KIND+'=%s';args.append(kind)
    if state!='All':
        where+=' AND u.enabled=%s';args.append(int(state=='Enabled'))
    if query:
        # Treat search wildcards as text; never interpolate query text into SQL.
        term='%'+query.replace('!','!!').replace('%','!%').replace('_','!_')+'%'
        where+=" AND (u.name LIKE %s ESCAPE '!' OR u.full_name LIKE %s ESCAPE '!' OR p.display_name LIKE %s ESCAPE '!' OR p.username LIKE %s ESCAPE '!' OR p.lms_id LIKE %s ESCAPE '!')"
        args.extend([term]*5)
    with campus(site) as c:
        total=fetch(c,'SELECT COUNT(DISTINCT u.name) AS total'+where,args)[0]['total']
        result=window(c,'SELECT '+IDENTITY+where+' ORDER BY display_name,u.name',args,page)
    return dict(result,total=total,site=site)


@frappe.whitelist(methods=['GET'])
def detail(site, user, section='connections', page=0):
    authorize()
    page=pagination(page)
    if section not in ('connections','classes','people','activity','invitations','subscription'):
        frappe.throw('Choose a valid record section.')
    with campus(site) as c:
        identities=fetch(c,'SELECT '+IDENTITY+BASE+' AND u.name=%s',(user,))
        if not identities: frappe.throw('Account not found in this campus.')
        person=identities[0]
        inst=person['workspace'] if person['kind']=='Institute' else None
        if section=='connections':
            sql="""SELECT r.name,CASE WHEN r.user=%s THEN p.display_name ELSE COALESCE(other.display_name,r.user) END AS title,
              CASE WHEN r.user=%s THEN p.user ELSE r.user END AS related_user,r.kind AS relationship,r.status,r.creation AS started_at,r.modified AS updated_at
              FROM `tabIL Profile Relationship` r JOIN `tabIL Public Profile` p ON p.name=r.profile
              LEFT JOIN `tabIL Public Profile` other ON other.user=r.user
              WHERE r.user=%s OR r.profile=%s ORDER BY r.modified DESC,r.name"""
            result=window(c,sql,(user,user,user,person['profile']),page)
            memberships=fetch(c,"""SELECT m.name,i.title,m.role,m.active,m.creation AS joined_at FROM `tabIL Member` m
              JOIN `tabIL Institute` i ON i.name=m.institute WHERE m.user=%s ORDER BY m.creation DESC LIMIT 101""",(user,))
            result['memberships']=memberships[:100];result['memberships_truncated']=len(memberships)>100
        elif section=='classes':
            sql="""SELECT cl.name,cl.title,cl.subject,cl.active,cl.owner_type,i.title AS institute,
              t.full_name AS teacher,t.user AS teacher_user,cl.teacher_assignment_active,
              (SELECT COUNT(DISTINCT em.user) FROM `tabIL Enrollment` e JOIN `tabIL Member` em ON em.name=e.student WHERE e.classroom=cl.name AND e.active=1) AS students,
              (SELECT COUNT(*) FROM `tabIL Session` s WHERE s.classroom=cl.name) AS sessions
              FROM `tabIL Classroom` cl JOIN `tabIL Institute` i ON i.name=cl.institute
              LEFT JOIN `tabIL Member` t ON t.name=cl.teacher
              WHERE cl.owner_user=%s OR t.user=%s OR cl.institute=%s OR EXISTS
              (SELECT 1 FROM `tabIL Enrollment` e JOIN `tabIL Member` m ON m.name=e.student WHERE e.classroom=cl.name AND m.user=%s)
              ORDER BY cl.creation DESC,cl.name"""
            result=window(c,sql,(user,user,inst,user),page)
        elif section=='people':
            # Institute membership, personal learners, or classmates; one row per account.
            sql="""SELECT m.user,MAX(m.full_name) AS display_name,GROUP_CONCAT(DISTINCT m.role ORDER BY m.role SEPARATOR ', ') AS role,
              MAX(m.active) AS active,MIN(m.creation) AS joined_at,COUNT(DISTINCT e.classroom) AS classes
              FROM `tabIL Member` m LEFT JOIN `tabIL Enrollment` e ON e.student=m.name
              WHERE m.user<>%s AND (m.institute=%s OR e.classroom IN
              (SELECT cl.name FROM `tabIL Classroom` cl LEFT JOIN `tabIL Member` t ON t.name=cl.teacher
               WHERE cl.owner_user=%s OR t.user=%s OR EXISTS
               (SELECT 1 FROM `tabIL Enrollment` own JOIN `tabIL Member` me ON me.name=own.student WHERE own.classroom=cl.name AND me.user=%s)))
              GROUP BY m.user ORDER BY display_name,m.user"""
            result=window(c,sql,(user,inst,user,user,user),page)
        elif section=='activity':
            sql="""SELECT a.name,s.title AS session_title,cl.title AS classroom,m.full_name AS student,m.user AS related_user,
              a.status,a.channel,a.recorded_at,s.starts_at
              FROM `tabIL Attendance` a JOIN `tabIL Session` s ON s.name=a.session
              JOIN `tabIL Classroom` cl ON cl.name=a.classroom JOIN `tabIL Member` m ON m.name=a.student
              LEFT JOIN `tabIL Member` t ON t.name=cl.teacher
              WHERE m.user=%s OR cl.owner_user=%s OR t.user=%s OR cl.institute=%s
              ORDER BY a.recorded_at DESC,a.name"""
            result=window(c,sql,(user,user,user,inst),page)
        elif section=='invitations':
            sql="""SELECT v.name,i.title AS institute,v.invite_email,v.status,v.creation AS sent_at,v.responded_at,v.expires_at
              FROM `tabIL Teacher Invitation` v JOIN `tabIL Institute` i ON i.name=v.institute
              WHERE v.invite_email=%s OR v.institute=%s ORDER BY v.creation DESC,v.name"""
            result=window(c,sql,(user,inst),page)
        else:
            sql="""SELECT name,display_name,role,plan,next_plan,enabled,trial_started,trial_until,paid_until,cancel_at_end
              FROM `tabIL Account Subscription` WHERE user=%s OR (institute=%s AND role='Institute') ORDER BY creation DESC,name"""
            result=window(c,sql,(user,inst),page)
    return dict(result,person=person,section=section,site=site)


@frappe.whitelist(methods=['POST'])
def review(site, user, decision, reason):
    """Approve or reject a pending teacher/institute profile on a reporting campus."""
    import time
    from frappe.utils.background_jobs import get_queue
    authorize()
    if decision not in ('Verified', 'Rejected'):
        frappe.throw('Choose approve or reject.')
    reason = str(reason or '').strip()
    if not reason or len(reason) > 500:
        frappe.throw('Give a short reason of up to 500 characters.')
    with campus(site) as c:
        rows = fetch(c, "SELECT name,kind,status FROM `tabIL Public Profile` WHERE user=%s AND kind IN ('Teacher','Institute') ORDER BY creation DESC LIMIT 1", (user,))
    if not rows or rows[0]['status'] != 'Pending':
        frappe.throw('This account has no profile waiting for review. Refresh to see its status.')
    job = get_queue('short').enqueue_call('frappe.utils.background_jobs.execute_job', timeout=120,
        kwargs={'site': site, 'user': 'Administrator', 'method': 'institute_lms.provider_review.apply',
                'event': None, 'job_name': 'provider_review', 'is_async': True,
                'kwargs': {'profile': rows[0]['name'], 'decision': decision, 'reason': reason,
                           'reviewer': frappe.session.user}})
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        status = job.get_status(refresh=True)
        if status == 'finished':
            result = job.return_value() or {}
            if not result.get('ok'):
                frappe.throw(result.get('message') or 'The campus refused this review.')
            return result
        if status in ('failed', 'stopped', 'canceled'):
            frappe.throw('The campus could not save this review. Check its error log and try again.')
        time.sleep(0.4)
    frappe.throw('The campus is taking longer than expected. Refresh in a minute to see whether the review was saved.')
