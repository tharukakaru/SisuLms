import frappe

no_cache=1

def get_context(context):
    if frappe.local.site != 'hnb-checkout.localhost':
        raise frappe.DoesNotExistError
    return context
