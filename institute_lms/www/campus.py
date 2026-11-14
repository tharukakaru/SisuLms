import frappe


def get_context(context):
    from institute_lms.portal_entry import redirect_owner_guest
    redirect_owner_guest()
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
