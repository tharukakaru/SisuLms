"""Add financial lookup indexes. Existing fees and payments are never rewritten."""
import frappe

def execute():
    for doctype,fields in [
        ('IL Provider Account',['institute','owner_type','owner_user']),
        ('IL Bank Slip',['classroom','status']),
        ('IL Paid Access',['provider_account','starts_at','ends_at']),
        ('IL Paid Access',['student','classroom','status']),
        ('IL Provider Invoice',['provider_account','status','due_at']),
    ]:frappe.db.add_index(doctype,fields)
