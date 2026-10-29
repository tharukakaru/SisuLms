"""Private learning goals, addressed exclusively by the authenticated user."""
import json
import frappe
from .learning_rules import preferences

def user():
    if frappe.session.user == 'Guest':
        frappe.throw('Sign in required', frappe.PermissionError)
    return frappe.session.user

@frappe.whitelist()
def get_preferences():
    name=user()
    record=frappe.db.get_value('IL Learning Preference', {'user':name}, ['motto','event_title','event_date','hide_countdown'], as_dict=True)
    return record or {'motto':'','event_title':'','event_date':'','hide_countdown':0}

@frappe.whitelist(methods=['POST'])
def save_preferences(data):
    name=user()
    try:
        values=preferences(json.loads(data) if isinstance(data,str) else data)
    except (ValueError,TypeError):
        frappe.throw('Add a valid title and date together, and a motto up to 180 characters.')
    frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE', (name,))
    existing=frappe.db.get_value('IL Learning Preference', {'user':name}, 'name')
    doc=frappe.get_doc('IL Learning Preference',existing) if existing else frappe.get_doc({'doctype':'IL Learning Preference','user':name})
    doc.update(values);doc.save(ignore_permissions=True)
    return values

