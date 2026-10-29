"""Idempotent non-destructive schema/data initialization. No paid access is invented."""
import json
import frappe
from institute_lms.saas import managed
from institute_lms.saas_rules import CORE, AI, LIMITS

def execute():
    for name in ('STARTER','PREMIUM AI','CUSTOM'):
        if frappe.db.exists('IL SaaS Plan',name):continue
        features={k:True for k in CORE}
        features.update({k:name=='PREMIUM AI' for k in AI})
        features['custom_domain']=name=='CUSTOM'
        # Deliberately unpriced/unallocated. Operator must set commercial limits.
        managed(frappe.get_doc({'doctype':'IL SaaS Plan','plan_name':name,'features':json.dumps(features),
            'limits':json.dumps({k:0 for k in LIMITS}),'price_minor':0,'period_days':30,'version':1}))
    for dt in ('IL Classroom','IL Enrollment'):
        after=''
        while True:
            names=frappe.db.sql('SELECT name FROM `tab'+dt+"` WHERE name>%s AND (lifecycle IS NULL OR lifecycle='') ORDER BY name LIMIT 500",(after,))
            if not names:break
            values=tuple(row[0] for row in names)
            frappe.db.sql('UPDATE `tab'+dt+"` SET lifecycle='ACTIVE' WHERE name IN %s AND (lifecycle IS NULL OR lifecycle='')",(values,))
            after=values[-1]
    indexes={'IL Subscription':['tenant_id','state'],'IL Payment Attempt':['tenant_id','status'],
             'IL Notification Event':['user','creation'],'IL Notification':['event','channel','status'],
             'IL Usage Entry':['resource','period'],'IL Device Token':['user','revoked'],
             'IL Mobile Session':['user','revoked'],'IL Stored Object':['institute','status']}
    for dt,columns in indexes.items():frappe.db.add_index(dt,columns)

def before_migrate():
    """Reject duplicate legacy data rather than delete/merge financial identities."""
    if frappe.db.table_exists('IL Classroom') and frappe.db.table_exists('Course Lesson'):
        from institute_lms.native_access import validate_link
        after=''
        while True:
            names=frappe.get_all('IL Classroom',filters={'lms_course':['is','set'],'name':['>',after]},pluck='name',order_by='name asc',limit_page_length=100)
            if not names:break
            for name in names:validate_link(frappe.get_doc('IL Classroom',name))
            after=names[-1]
    groups={'IL Enrollment':['classroom','student'],'IL Member':['institute','user'],
            'IL Programme Enrollment':['programme','student'],'IL Institute Bill':['institute','period'],
            'IL YouTube Connection':['member']}
    for dt,columns in groups.items():
        if not frappe.db.table_exists(dt):continue
        cols=','.join('`'+c+'`' for c in columns)
        if frappe.db.sql('SELECT '+cols+',COUNT(*) FROM `tab'+dt+'` GROUP BY '+cols+' HAVING COUNT(*)>1 LIMIT 1'):
            frappe.throw('Migration stopped: resolve duplicate '+dt+' identities before adding constraints. No records were removed.')
