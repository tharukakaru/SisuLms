import frappe

no_cache = 1


def get_context(context):
    context.no_cache = 1
    if frappe.session.user != 'Guest':
        from institute_lms.registration import require_owner
        require_owner()
        frappe.local.flags.redirect_location = '/campus'
        raise frappe.Redirect
    context.title = 'SISU Super Admin'
