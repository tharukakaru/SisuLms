"""Public portal identity and navigation; authentication remains with Frappe."""
from urllib.parse import urlsplit
import frappe


def student_campus_url(config):
    if not config.get('il_control_plane'):
        return ''
    value = config.get('il_student_campus_url') or ''
    try:
        target = urlsplit(value)
        owner = urlsplit(config.get('host_name') or '')
        if not target.hostname or target.username or target.password or target.fragment:
            return ''
        if any(c.isspace() for c in value) or '\\' in value:
            return ''
        # Accessing port also rejects malformed URLs.
        target.port
        if target.scheme == 'https':
            return value
        if (target.scheme == owner.scheme == 'http'
                and target.hostname == owner.hostname
                and target.hostname in ('127.0.0.1', 'localhost', '::1')):
            return value
    except (ValueError, TypeError):
        pass
    return ''


@frappe.whitelist(allow_guest=True, methods=['GET'])
def public():
    return {'control_plane': bool(frappe.conf.get('il_control_plane')),
            'student_campus_url': student_campus_url(frappe.conf)}


def redirect_owner_guest():
    if frappe.conf.get('il_control_plane') and frappe.session.user == 'Guest':
        frappe.local.flags.redirect_location = '/login?redirect-to=/campus'
        raise frappe.Redirect(302)
