import frappe
from urllib.parse import urlencode


def get_context(context):
    from institute_lms.portal_entry import redirect_owner_guest
    redirect_owner_guest()
    invoice = frappe.form_dict.get('checkout_invoice')
    if invoice and frappe.session.user == 'Guest':
        target = '/campus?' + urlencode({'checkout_invoice': invoice}) + '#subscription'
        frappe.local.flags.redirect_location = '/login?' + urlencode({'redirect-to': target})
        raise frappe.Redirect(302)
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
