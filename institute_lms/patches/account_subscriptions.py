"""Idempotent cutover; no sample members, fabricated payments or renewed trials."""
import frappe

def execute():
    if frappe.conf.get('il_control_plane'):return
    from institute_lms.account_billing import account
    for doctype,fields in [('IL Account Subscription',['institute','role']),('IL Account Invoice',['subscription','status'])]:
        frappe.db.add_index(doctype,fields)
    after=''
    while True:
        rows=frappe.get_all('IL Member',filters={'active':1,'name':['>',after]},fields=['name','institute','user','role','full_name'],order_by='name',limit_page_length=500)
        if not rows:break
        for member in rows:
            if member.role in ('Teacher','Student','Admin'):
                inst=frappe.get_doc('IL Institute',member.institute)
                account(inst,member,create=True)
        after=rows[-1].name
    # Cancel legacy card mandates. Historical financial documents remain untouched.
    frappe.db.sql('UPDATE `tabIL Provider Account` SET auto_pay=0')
