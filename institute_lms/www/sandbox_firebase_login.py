import frappe


def get_context(context):
    if frappe.local.site != 'hnb-checkout.localhost':
        raise frappe.DoesNotExistError
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
