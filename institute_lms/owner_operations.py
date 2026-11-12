"""Owner-only read-only reports from explicitly configured campus sites on this Bench."""
import json
import re
from pathlib import Path
from datetime import date, timedelta
import frappe


def bounds(start=None, end=None, page=0):
    today=date.today()
    try:
        first=date.fromisoformat(str(start)) if start else today.replace(day=1)
        last=date.fromisoformat(str(end)) if end else today
        page=int(page)
    except (ValueError,TypeError):
        frappe.throw('Enter valid dates and a page number.')
    if first>last or (last-first).days>366 or not 0<=page<=10000:
        frappe.throw('Choose a date range of up to one year and a valid page.')
    return first, last+timedelta(days=1),page


def sources():
    configured=frappe.conf.get('il_owner_reporting_sites') or []
    if not isinstance(configured,list): raise ValueError('Reporting sites must be configured as a list')
    return [s for s in configured if isinstance(s,str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.-]+',s) and '..' not in s]


def connect(site):
    import pymysql
    root=Path(frappe.get_site_path()).resolve().parent
    target=(root/site).resolve()
    if target.parent!=root: raise ValueError('Invalid reporting site')
    config=json.loads((root/'common_site_config.json').read_text())
    config.update(json.loads((target/'site_config.json').read_text()))
    if config.get('db_type','mariadb')!='mariadb':raise ValueError('Reporting requires MariaDB')
    return pymysql.connect(host=config.get('db_host') or '127.0.0.1',port=int(config.get('db_port') or 3306),
        user=config.get('db_user') or config['db_name'],password=config['db_password'],database=config['db_name'],
        unix_socket=config.get('db_socket'),charset='utf8mb4',connect_timeout=5,read_timeout=10,write_timeout=5,
        cursorclass=pymysql.cursors.DictCursor)


@frappe.whitelist(methods=['GET'])
def billing(site=None,start=None,end=None,page=0):
    from .platform import owner
    owner()
    allowed=sources()
    if not allowed:return dict(sites=[],configured=False,rows=[],totals=[],subscriptions=[])
    site=site or allowed[0]
    if site not in allowed:frappe.throw('This campus is not enabled for owner reporting.',frappe.PermissionError)
    first,after,page=bounds(start,end,page)
    connection=None
    try:
        connection=connect(site)
        with connection.cursor() as c:
            c.execute('START TRANSACTION READ ONLY')
            c.execute("SELECT plan, COUNT(*) AS accounts, SUM(enabled=1) AS enabled_accounts FROM `tabIL Account Subscription` WHERE role IN ('Teacher','Institute') GROUP BY plan ORDER BY plan")
            subscriptions=c.fetchall()
            filters=" FROM `tabIL Account Invoice` i INNER JOIN `tabIL Account Subscription` s ON s.name=i.subscription WHERE s.role IN ('Teacher','Institute') AND i.creation >= %s AND i.creation < %s"
            c.execute('SELECT i.currency, i.status, COUNT(*) AS invoices, SUM(i.amount_minor) AS amount_minor'+filters+' GROUP BY i.currency,i.status',(first,after))
            totals=c.fetchall()
            c.execute('SELECT i.name,i.creation,i.billed_to,i.plan,i.currency,i.amount_minor,i.status,i.paid_at,i.period_start,i.period_end,i.receipt_number'+filters+' ORDER BY i.creation DESC,i.name DESC LIMIT 51 OFFSET %s',(first,after,page*50))
            rows=c.fetchall()
        return dict(sites=allowed,site=site,configured=True,subscriptions=subscriptions,totals=totals,rows=rows[:50],has_next=len(rows)>50,page=page,start=str(first),end=str(after-timedelta(days=1)))
    except Exception:
        frappe.throw('Campus billing could not be loaded. Ask the hosting operator to check the reporting connection and installed schema.')
    finally:
        if connection is not None:connection.close()


@frappe.whitelist(methods=['GET'])
def readiness():
    from .platform import owner
    owner()
    from .health import readiness as local_readiness
    value=local_readiness()
    # Old payments.lk flags do not describe the current provider checkout.
    services=value.get('provider_configured',{})
    services.pop('student_payments',None);services.pop('subscription_payments',None)
    value['mail']={s:frappe.db.count('Email Queue',{'status':s}) for s in ('Not Sent','Sending','Sent','Error','Partially Sent')}
    value['reporting_sites']=sources()
    value['payment_note']='Students pay their teacher or institute by bank transfer and upload a slip. Provider subscriptions use the separately configured gateway; bank acceptance remains a separate launch check.'
    return value

@frappe.whitelist(methods=['GET'])
def audit(page=0):
    from .platform import owner
    owner()
    from .pricing_rules import integer
    page=integer(page,'Page',10000)
    return frappe.db.sql("""SELECT * FROM (
        SELECT CONCAT('site:',name) AS name,creation,actor,action,reference,details FROM `tabIL SaaS Audit`
        UNION ALL
        SELECT CONCAT('account:',name) AS name,creation,actor,action,reference,details FROM `tabIL Payout Audit`
    ) entries ORDER BY creation DESC,name DESC LIMIT 50 OFFSET %s""",(page*50,),as_dict=True)

@frappe.whitelist(methods=['GET'])
def overview():
    from .platform import owner
    owner()
    campuses=[]
    for site in sources():
        connection=None
        try:
            connection=connect(site)
            with connection.cursor() as c:
                c.execute('START TRANSACTION READ ONLY')
                c.execute("""SELECT
                  (SELECT COUNT(*) FROM `tabIL Member` WHERE role='Student' AND active=1) AS student_memberships,
                  (SELECT COUNT(*) FROM `tabIL Public Profile` WHERE kind='Teacher' AND status='Verified') AS teachers,
                  (SELECT COUNT(*) FROM `tabIL Public Profile` WHERE kind='Institute' AND status='Verified') AS institutes,
                  (SELECT COUNT(*) FROM `tabIL Public Profile` WHERE status='Pending') AS pending_profiles,
                  (SELECT COUNT(*) FROM `tabIL Payout Request` WHERE status='Pending') AS pending_payouts""")
                counts=c.fetchone()
            campuses.append(dict(site=site,available=True,counts=counts,url='https://'+site+'/campus'))
        except Exception:
            campuses.append(dict(site=site,available=False,message='Campus overview unavailable. Check its reporting connection and schema.'))
        finally:
            if connection is not None:connection.close()
    return dict(campuses=campuses,hosted_institutes=frappe.db.count('IL Organization'),
                setup_pending=frappe.db.count('IL Provisioning Job',{'status':['in',['pending','running','failed']]}))
