"""Tenant-scoped invoice history with complete totals and server pagination."""
from datetime import timedelta
import frappe
from frappe.utils import now_datetime
from .report_dates import report_window

@frappe.whitelist()
def history(start_date=None, end_date=None, status='All', page=0):
    from .api import identity, room_filters
    inst, member = identity()
    if member.role not in ('Student', 'Teacher', 'Admin'):
        frappe.throw('Class fee access required', frappe.PermissionError)
    try:
        start, stop = report_window(start_date, end_date, now_datetime())
        page = max(0, int(page))
    except (ValueError, TypeError) as exc:
        frappe.throw(str(exc))
    if status not in ('All', 'Paid', 'Unpaid', 'Overdue', 'Failed', 'Cancelled'):
        frappe.throw('Choose a valid invoice status')
    filters = {'institute': inst.name, 'due_date': ['between', [str(start), str(stop-timedelta(days=1))]]}
    if member.role == 'Student':
        filters['student'] = member.name
    else:
        filters['classroom'] = ['in', frappe.get_all('IL Classroom', filters=room_filters(inst, member), pluck='name') or ['__none__']]
    totals = frappe.get_all('IL Invoice', filters=filters, fields=['currency', 'status', {'SUM': 'amount', 'as': 'amount'}, {'COUNT': 'name', 'as': 'count'}], group_by='currency,status', limit_page_length=0)
    if status != 'All':
        filters['status'] = status
    count = frappe.db.count('IL Invoice', filters)
    rows = frappe.get_all('IL Invoice', filters=filters, fields=['*'], order_by='due_date desc, name asc', limit_start=page*25, limit_page_length=25)
    return {'rows': rows, 'totals': totals, 'count': count, 'page': page, 'start_date': str(start), 'end_date': str(stop-timedelta(days=1)), 'date_basis': 'Invoice due date'}
